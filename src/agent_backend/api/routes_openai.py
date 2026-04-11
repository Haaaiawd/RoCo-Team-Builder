"""
OpenAI 兼容路由 — /v1/models, /healthz, /readyz

对齐: agent-backend-system.md §5.3 HTTP API 端点摘要
     agent-backend-system.detail.md §3.4 list_models

向 web-ui-system 暴露受控虚拟模型目录和健康检查端点。
/v1/chat/completions 将在 T3.2.1 中接入。
"""

from __future__ import annotations

import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .error_mapping import ProductError, validation_error
from ..app.request_normalizer import normalize_chat_request
from ..app.model_catalog import ModelCatalog

router = APIRouter()

_catalog: ModelCatalog | None = None


def init_router(catalog: ModelCatalog) -> None:
    """在应用启动时注入模型目录依赖。"""
    global _catalog
    _catalog = catalog


def _get_catalog() -> ModelCatalog:
    if _catalog is None:
        raise RuntimeError("ModelCatalog not initialized — call init_router() first")
    return _catalog


# ---------------------------------------------------------------------------
# GET /v1/models
# ---------------------------------------------------------------------------


@router.get("/v1/models")
async def list_models():
    """返回受控虚拟模型目录。

    OpenAI 兼容格式: { "object": "list", "data": [...] }
    """
    catalog = _get_catalog()
    models = catalog.list_models()
    return {"object": "list", "data": models}


# ---------------------------------------------------------------------------
# POST /v1/chat/completions — T3.2.1 will implement
# ---------------------------------------------------------------------------


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Chat Completions 端点 — 骨架占位，T3.2.1 接入完整归一化与 runtime。"""
    try:
        payload = await request.json()
    except Exception:
        return validation_error("请求体必须是合法 JSON", param="body").to_response()

    try:
        context = normalize_chat_request(payload, dict(request.headers), _get_catalog())
    except ProductError as exc:
        return exc.to_response()

    return {
        "id": f"chatcmpl_{context.request_id}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": context.model_entry.public_model_id,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Request normalized successfully. Runtime not yet connected.",
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
