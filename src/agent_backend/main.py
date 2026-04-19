"""
agent-backend-system 服务入口

FastAPI 应用工厂，暴露 OpenAI 兼容 API。
启动: uvicorn agent_backend.main:app --host 0.0.0.0 --port 8000

对齐: agent-backend-system.md §4.2 OpenAI Compatibility Router
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routes_openai import init_router, router
from .app.model_catalog import ModelCatalog


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期 — 初始化模型目录等依赖。"""
    catalog = ModelCatalog()
    init_router(catalog)
    app.state.catalog = catalog
    yield


app = FastAPI(
    title="RoCo Team Builder Agent Backend",
    version="0.1.0",
    description="OpenAI 兼容后端 — 配队推理、精灵资料查询与卡片渲染",
    lifespan=lifespan,
)

app.include_router(router)
