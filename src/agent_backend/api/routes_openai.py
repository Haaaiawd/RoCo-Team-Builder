"""
OpenAI 兼容路由 — /v1/models, /v1/chat/completions, /healthz, /readyz

对齐: agent-backend-system.md §5.3 HTTP API 端点摘要
     agent-backend-system.detail.md §3.4 list_models
     agent-backend-system.detail.md §4.1 请求处理路径选择

向 web-ui-system 暴露受控虚拟模型目录、Chat Completions 和健康检查端点。
"""

from __future__ import annotations

import json
import os
import time
from typing import AsyncIterator
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from .error_mapping import ProductError, quota_exhausted_error, validation_error
from ..app.model_catalog import ModelCatalog
from ..app.quota_guard import BuiltinQuotaPolicy, QuotaStore, enforce_builtin_quota
from ..app.request_context import ChatRequestContext
from ..app.request_normalizer import normalize_chat_request
from ..app.session_service import SessionRegistry
from ..runtime.agent_factory import AgentFactory
from ..runtime.runtime_service import run_agent_streamed

router = APIRouter()

_catalog: ModelCatalog | None = None
_session_registry: SessionRegistry | None = None
_quota_policy: BuiltinQuotaPolicy | None = None
_quota_store: QuotaStore | None = None
_agent_factory: AgentFactory | None = None

# 内部密钥验证
_INTERNAL_SECRET = os.environ.get("ROCO_INTERNAL_SECRET", "roco-secret-change-in-production")


def _verify_internal_secret(headers: dict[str, str]) -> None:
    """验证内部服务间调用的共享密钥。
    
    防止伪造 X-OpenWebUI-User-Id/X-OpenWebUI-Chat-Id 头部访问他人会话。
    """
    provided_secret = headers.get("x-roco-internal-secret") or headers.get("X-Roco-Internal-Secret")
    if provided_secret != _INTERNAL_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized: Invalid or missing internal secret",
        )


def init_router(
    catalog: ModelCatalog,
    session_registry: SessionRegistry,
    quota_policy: BuiltinQuotaPolicy,
    quota_store: QuotaStore,
    agent_factory: AgentFactory,
) -> None:
    """在应用启动时注入所有运行时依赖。"""
    global _catalog, _session_registry, _quota_policy, _quota_store, _agent_factory
    _catalog = catalog
    _session_registry = session_registry
    _quota_policy = quota_policy
    _quota_store = quota_store
    _agent_factory = agent_factory


def _get_catalog() -> ModelCatalog:
    if _catalog is None:
        raise RuntimeError("ModelCatalog not initialized — call init_router() first")
    return _catalog


# ---------------------------------------------------------------------------
# GET /v1/models
# ---------------------------------------------------------------------------


@router.get("/v1/models")
async def list_models(request: Request):
    """返回受控虚拟模型目录。

    OpenAI 兼容格式: { "object": "list", "data": [...] }
    """
    _verify_internal_secret(dict(request.headers))
    catalog = _get_catalog()
    models = catalog.list_models()
    return {"object": "list", "data": models}


# ---------------------------------------------------------------------------
# POST /v1/chat/completions
# ---------------------------------------------------------------------------


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Chat Completions 端点 — 完整归一化 + quota + session + agent runtime。

    对齐: agent-backend-system.detail.md §4.1 请求处理路径选择
    """
    _verify_internal_secret(dict(request.headers))
    
    # 1. 解析 JSON body
    try:
        payload = await request.json()
    except Exception:
        return validation_error("请求体必须是合法 JSON", param="body").to_response()

    # 2. 归一化请求（含 session key 解析、model 校验、capability 兜底）
    try:
        context = normalize_chat_request(payload, dict(request.headers), _get_catalog())
    except ProductError as exc:
        return exc.to_response()

    # 3. Builtin quota 检查
    if _quota_policy is not None and _quota_store is not None:
        quota_decision = enforce_builtin_quota(context, _quota_policy, _quota_store)
        if not quota_decision.allowed:
            return quota_exhausted_error(
                retry_after_seconds=quota_decision.retry_after_seconds,
                suggested_route=quota_decision.suggested_route or "byok",
            ).to_response()

    # 4. 获取或创建 session
    if _session_registry is None:
        return JSONResponse(
            status_code=503,
            content={"error": {"message": "Session registry not initialized", "type": "internal_error"}},
        )
    session = _session_registry.get_or_create(context.session_key)

    # 6. 分流: stream / non-stream
    if context.stream:
        return StreamingResponse(
            _run_streamed(context, session),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        return await _run_non_streamed(context, session)


async def _run_streamed(context: ChatRequestContext, session) -> AsyncIterator[str]:
    """流式路径 — 调用 Agent Runtime 并以 SSE 输出。"""
    if _agent_factory is None:
        yield encode_mid_stream_error_init("Agent factory not initialized")
        yield "data: [DONE]\n\n"
        return

    async with session.lock:
        session.touch()
        for msg in context.messages:
            if msg.get("role") == "user":
                session.add_item(msg)

        async for chunk in run_agent_streamed(context, session, _agent_factory):
            yield chunk


async def _run_non_streamed(context, session):
    """非流式路径 — 收集完整输出后返回 JSON。"""
    if _agent_factory is None:
        return JSONResponse(
            status_code=503,
            content={"error": {"message": "Agent factory not initialized", "type": "internal_error"}},
        )

    # 收集所有 SSE chunk 中的 content
    collected_content: list[str] = []
    async with session.lock:
        session.touch()
        for msg in context.messages:
            if msg.get("role") == "user":
                session.add_item(msg)

        async for chunk in run_agent_streamed(context, session, _agent_factory):
            # 解析 SSE chunk 提取 content
            if chunk.startswith("data: ") and chunk != "data: [DONE]\n\n":
                try:
                    data = json.loads(chunk[6:].strip())
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            collected_content.append(content)
                except (json.JSONDecodeError, IndexError):
                    pass

    full_content = "".join(collected_content)
    return {
        "id": f"chatcmpl-{context.request_id}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": context.model_entry.public_model_id,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": full_content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


def encode_mid_stream_error_init(message: str) -> str:
    """SSE mid-stream error 编码（路由层辅助）。"""
    error_data = {
        "error": {
            "message": message,
            "type": "internal_error",
        }
    }
    return f"data: {json.dumps(error_data)}\n\n"


# ---------------------------------------------------------------------------
# Health & Readiness
# ---------------------------------------------------------------------------


@router.get("/healthz")
async def health_check():
    """容器健康检查 — 进程存活即 OK。"""
    return {"status": "ok"}


@router.get("/readyz")
async def readiness_check():
    """就绪检查 — 验证模型目录已初始化且至少有一个可用模型。"""
    try:
        catalog = _get_catalog()
        models = catalog.list_models()
        if not models:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "no enabled models"},
            )
        return {"status": "ready", "models_count": len(models)}
    except RuntimeError:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "catalog not initialized"},
        )
