"""
OpenAI 兼容路由 — /v1/models, /v1/chat/completions, /healthz, /readyz

对齐:
- agent-backend-system.md §5.3 HTTP API 端点摘要
- agent-backend-system.detail.md §3.4 list_models
- agent-backend-system.md §5.1 chat_completions（quota/capability/session/runtime 串联）
- agent-backend-system.md §8.2 SSE 格式

T3.2.3 / T3.2.4 / T3.3.1 / T3.3.2 的实际接线入口。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ..app.capability_guard import (
    CapabilityDecision,
    check_vision_capability,
)
from ..app.model_catalog import ModelCatalog
from ..app.quota_guard import (
    BuiltinQuotaPolicy,
    QuotaDecision,
    QuotaStore,
    enforce_builtin_quota,
)
from ..app.request_context import ChatRequestContext
from ..app.request_normalizer import normalize_chat_request
from ..app.session_service import SessionRegistry
from ..runtime.chat_runtime import IChatRuntime
from .error_mapping import (
    ProductError,
    capability_vision_unsupported,
    quota_exhausted,
    runtime_failure,
    validation_error,
)

router = APIRouter()


@dataclass
class _RouterDeps:
    """路由所需依赖 —— 由 init_router 在 lifespan 中注入。"""

    catalog: ModelCatalog | None = None
    sessions: SessionRegistry | None = None
    quota_store: QuotaStore | None = None
    quota_policy: BuiltinQuotaPolicy | None = None
    runtime_factory: Callable[[], IChatRuntime] | None = None


_deps = _RouterDeps()


def init_router(
    catalog: ModelCatalog,
    *,
    sessions: SessionRegistry | None = None,
    quota_store: QuotaStore | None = None,
    quota_policy: BuiltinQuotaPolicy | None = None,
    runtime_factory: Callable[[], IChatRuntime] | None = None,
) -> None:
    """在应用启动时注入依赖。

    `runtime_factory` 是一个零参工厂，返回 `IChatRuntime` 实例。采用工厂
    而非实例的目的是让测试可以按请求注入假实现，生产可以按请求或按 app
    共享同一实例。
    """
    _deps.catalog = catalog
    _deps.sessions = sessions or SessionRegistry()
    _deps.quota_store = quota_store or QuotaStore()
    _deps.quota_policy = quota_policy or BuiltinQuotaPolicy()
    _deps.runtime_factory = runtime_factory


def _require_catalog() -> ModelCatalog:
    if _deps.catalog is None:
        raise RuntimeError("ModelCatalog not initialized — call init_router() first")
    return _deps.catalog


# ---------------------------------------------------------------------------
# GET /v1/models
# ---------------------------------------------------------------------------


@router.get("/v1/models")
async def list_models() -> dict[str, Any]:
    """返回受控虚拟模型目录。OpenAI 兼容格式。"""
    catalog = _require_catalog()
    return {"object": "list", "data": catalog.list_models()}


# ---------------------------------------------------------------------------
# POST /v1/chat/completions
# ---------------------------------------------------------------------------


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Chat Completions 端点 —— 串联 quota/capability/session/runtime。"""
    try:
        payload = await request.json()
    except Exception:
        return validation_error("请求体必须是合法 JSON", param="body").to_response()

    try:
        context = normalize_chat_request(payload, dict(request.headers), _require_catalog())
    except ProductError as exc:
        return exc.to_response()

    capability_result = check_vision_capability(
        {"messages": context.messages},
        context.model_entry.supports_vision,
    )
    if capability_result == CapabilityDecision.CAPABILITY_MISMATCH:
        return capability_vision_unsupported().to_response()

    assert _deps.quota_store is not None
    assert _deps.quota_policy is not None
    quota_result = enforce_builtin_quota(
        {"user_id": context.user_id},
        _deps.quota_policy,
        _deps.quota_store,
    )
    if quota_result == QuotaDecision.QUOTA_EXCEEDED:
        return quota_exhausted().to_response()

    assert _deps.sessions is not None
    session_record = _deps.sessions.get_or_create(context.session_key)
    session_record.add_item({
        "role": "user",
        "content": context.messages[-1].get("content") if context.messages else "",
    })

    if _deps.runtime_factory is None:
        return runtime_failure(
            "后端 runtime 未配置，无法处理聊天请求",
            detail="init_router 未注入 runtime_factory",
        ).to_response()
    runtime = _deps.runtime_factory()

    if context.stream:
        return StreamingResponse(
            _run_stream(runtime, context, session_record),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async with session_record.lock:
        try:
            body = await runtime.run_nonstream(context, session_record)
        except Exception as exc:  # noqa: BLE001
            return runtime_failure(detail=str(exc)).to_response()
    return body


async def _run_stream(
    runtime: IChatRuntime,
    context: ChatRequestContext,
    session_record: Any,
) -> AsyncIterator[str]:
    """按 session lock 串行化流式响应，保证同一 session 内请求不交错。

    mid-stream error 不能冒泡到 HTTP 层（那会让 Starlette 吐 500 而不是完成 SSE），
    因此在迭代 runtime stream 时统一兜底：打出 error chunk + [DONE]。
    """
    import json

    async with session_record.lock:
        try:
            stream = runtime.stream(context, session_record)
            if hasattr(stream, "__await__"):
                stream = await stream  # type: ignore[assignment]
            async for chunk in stream:
                yield chunk
        except Exception as exc:  # noqa: BLE001 — never bubble stream errors to HTTP layer
            payload = {"error": {"message": str(exc), "type": "runtime_error"}}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Health & Readiness
# ---------------------------------------------------------------------------


@router.get("/healthz")
async def health_check() -> dict[str, str]:
    """容器健康检查 — 进程存活即 OK。"""
    return {"status": "ok"}


@router.get("/readyz")
async def readiness_check():
    """就绪检查 — 验证模型目录已初始化且至少有一个可用模型。"""
    try:
        catalog = _require_catalog()
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
