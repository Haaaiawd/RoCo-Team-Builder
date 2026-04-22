"""
agent-backend-system 服务入口

FastAPI 应用工厂，暴露 OpenAI 兼容 API。
启动: uvicorn agent_backend.main:app --host 0.0.0.0 --port 8000

对齐: agent-backend-system.md §4.2 OpenAI Compatibility Router
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routes_openai import init_router, router
from .app.model_catalog import ModelCatalog
from .app.quota_guard import BuiltinQuotaPolicy, QuotaStore
from .app.session_service import SessionRegistry
from .integrations.data_layer_client import DataLayerClient
from .runtime.chat_runtime import IChatRuntime


def _build_runtime_factory() -> "callable | None":
    """按环境变量决定是否真正启用 openai-agents Runner。

    - 未安装 `openai-agents` 或未配置 `ROCO_PROVIDER_API_KEY` 时返回 None，
      此时路由层会返回 RUNTIME_AGENT_FAILED，提示后端未配置。生产环境必须
      配置；本地调试时可以先 GET /v1/models 验证 HTTP 层可用。
    """
    try:
        from agents import set_default_openai_client  # noqa: F401
        from .runtime.agent_factory import AgentFactory
        from .runtime.chat_runtime import AgentChatRuntime
    except ImportError:
        return None

    api_key = os.environ.get("ROCO_PROVIDER_API_KEY")
    base_url = os.environ.get("ROCO_PROVIDER_BASE_URL")
    if not api_key:
        return None

    try:
        from openai import AsyncOpenAI

        client_kwargs: dict[str, object] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        set_default_openai_client(AsyncOpenAI(**client_kwargs), use_for_tracing=False)
    except Exception:
        return None

    from data_layer.app.facade import DataLayerFacade

    data_client = DataLayerClient(DataLayerFacade())
    agent_factory = AgentFactory(data_client)
    runtime = AgentChatRuntime(agent_factory)

    def _factory() -> IChatRuntime:
        return runtime

    return _factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期 — 初始化模型目录 / 会话 / 额度 / runtime。"""
    catalog = ModelCatalog()
    sessions = SessionRegistry()
    quota_store = QuotaStore()
    quota_policy = BuiltinQuotaPolicy()
    runtime_factory = _build_runtime_factory()

    init_router(
        catalog,
        sessions=sessions,
        quota_store=quota_store,
        quota_policy=quota_policy,
        runtime_factory=runtime_factory,
    )
    app.state.catalog = catalog
    app.state.sessions = sessions
    app.state.quota_store = quota_store
    app.state.quota_policy = quota_policy
    app.state.runtime_factory = runtime_factory
    yield


app = FastAPI(
    title="RoCo Team Builder Agent Backend",
    version="0.1.0",
    description="OpenAI 兼容后端 — 配队推理、精灵资料查询与卡片渲染",
    lifespan=lifespan,
)

app.include_router(router)
