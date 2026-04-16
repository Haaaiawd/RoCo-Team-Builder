"""
agent-backend-system 服务入口

FastAPI 应用工厂，暴露 OpenAI 兼容 API。
启动: uvicorn agent_backend.main:app --host 0.0.0.0 --port 8000

对齐: agent-backend-system.md §4.2 OpenAI Compatibility Router
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routes_openai import init_router, router
from .app.model_catalog import ModelCatalog
from .app.quota_guard import BuiltinQuotaPolicy, QuotaStore
from .app.session_service import SESSION_POLICY, SessionRegistry
from .integrations.data_layer_client import DataLayerClient
from .runtime.agent_factory import AgentFactory
from data_layer.app.facade import DataLayerFacade


async def _session_janitor(registry: SessionRegistry, interval_seconds: int = 300) -> None:
    """后台任务 — 定期清理闲置会话。

    对齐: agent-backend-system.detail.md §3.6 evict_idle_sessions
    """
    while True:
        await asyncio.sleep(interval_seconds)
        evicted = registry.evict_idle_sessions()
        if evicted:
            import logging
            logging.getLogger(__name__).info(
                "Session janitor evicted %d idle sessions",
                len(evicted),
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期 — 初始化所有运行时依赖，退出时清理资源。"""
    # 1. 模型目录
    catalog = ModelCatalog()
    app.state.catalog = catalog

    # 2. 数据层
    facade = DataLayerFacade()
    app.state.data_facade = facade

    # 3. 会话管理
    session_registry = SessionRegistry()
    app.state.session_registry = session_registry

    # 4. 额度管理
    quota_policy = BuiltinQuotaPolicy()
    quota_store = QuotaStore()
    app.state.quota_policy = quota_policy
    app.state.quota_store = quota_store

    # 5. Agent 工厂
    data_client = DataLayerClient(facade)
    agent_factory = AgentFactory(data_client)
    app.state.agent_factory = agent_factory

    # 6. 注入路由依赖
    init_router(
        catalog=catalog,
        session_registry=session_registry,
        quota_policy=quota_policy,
        quota_store=quota_store,
        agent_factory=agent_factory,
    )

    # 7. 启动 session janitor 后台任务
    janitor_interval = SESSION_POLICY["idle_ttl_minutes"] * 60 // 6  # TTL/6 间隔检查
    janitor_task = asyncio.create_task(
        _session_janitor(session_registry, interval_seconds=janitor_interval)
    )

    yield

    # 清理: 停止 janitor
    janitor_task.cancel()
    try:
        await janitor_task
    except asyncio.CancelledError:
        pass

    # 清理: 关闭 WikiGateway 的 httpx 连接池
    await facade._repository._gateway.close()


app = FastAPI(
    title="RoCo Team Builder Agent Backend",
    version="0.1.0",
    description="OpenAI 兼容后端 — 配队推理、精灵资料查询与卡片渲染",
    lifespan=lifespan,
)

app.include_router(router)
