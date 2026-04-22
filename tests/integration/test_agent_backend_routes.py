"""
T3.1.1 集成测试 — OpenAI 兼容路由、模型目录与健康检查。

验收标准:
  - Given 服务启动 → GET /v1/models 返回受控虚拟模型目录 + supports_vision
  - Given 调用 /healthz 与 /readyz → 返回可用于容器探针的成功响应
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from agent_backend.main import app
from agent_backend.app.model_catalog import ModelCatalog, ModelCatalogEntry


class _FakeChatRuntime:
    """测试用假 runtime：非流式返回固定 assistant 回复；流式产出两段 delta + [DONE]。"""

    async def run_nonstream(self, context, session_record):
        import time

        session_record.add_item({"role": "assistant", "content": "ok"})
        return {
            "id": f"chatcmpl_{context.request_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": context.model_entry.public_model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "ok"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    def stream(self, context, session_record):
        async def _iter():
            import json

            session_record.add_item({"role": "assistant", "content": "hi there"})
            yield (
                "data: "
                + json.dumps(
                    {
                        "id": f"chatcmpl_{context.request_id}",
                        "object": "chat.completion.chunk",
                        "model": context.model_entry.public_model_id,
                        "choices": [
                            {"index": 0, "delta": {"content": "hi "}, "finish_reason": None}
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            yield (
                "data: "
                + json.dumps(
                    {
                        "id": f"chatcmpl_{context.request_id}",
                        "object": "chat.completion.chunk",
                        "model": context.model_entry.public_model_id,
                        "choices": [
                            {"index": 0, "delta": {"content": "there"}, "finish_reason": None}
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            yield "data: [DONE]\n\n"

        return _iter()


@pytest.fixture
async def client():
    """使用 httpx AsyncClient 测试 FastAPI 应用，手动触发 lifespan。"""
    from agent_backend.api.routes_openai import init_router
    from agent_backend.app.model_catalog import ModelCatalog

    catalog = ModelCatalog()
    init_router(catalog, runtime_factory=lambda: _FakeChatRuntime())
    app.state.catalog = catalog

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# GET /v1/models
# ---------------------------------------------------------------------------


class TestListModels:
    @pytest.mark.asyncio
    async def test_returns_model_list(self, client: AsyncClient):
        """返回 OpenAI 兼容的模型列表。"""
        resp = await client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    @pytest.mark.asyncio
    async def test_model_entry_shape(self, client: AsyncClient):
        """模型条目包含必要字段。"""
        resp = await client.get("/v1/models")
        entry = resp.json()["data"][0]
        assert "id" in entry
        assert entry["object"] == "model"
        assert entry["owned_by"] == "roco-agent"
        assert "metadata" in entry
        assert "supports_vision" in entry["metadata"]

    @pytest.mark.asyncio
    async def test_default_model_is_roco_agent(self, client: AsyncClient):
        """默认模型 ID 为 roco-agent。"""
        resp = await client.get("/v1/models")
        model_ids = [m["id"] for m in resp.json()["data"]]
        assert "roco-agent" in model_ids

    @pytest.mark.asyncio
    async def test_supports_vision_flag(self, client: AsyncClient):
        """默认模型支持视觉能力。"""
        resp = await client.get("/v1/models")
        entry = resp.json()["data"][0]
        assert entry["metadata"]["supports_vision"] is True


# ---------------------------------------------------------------------------
# GET /healthz
# ---------------------------------------------------------------------------


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_ok(self, client: AsyncClient):
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# GET /readyz
# ---------------------------------------------------------------------------


class TestReadinessCheck:
    @pytest.mark.asyncio
    async def test_ready_with_models(self, client: AsyncClient):
        resp = await client.get("/readyz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ready"
        assert body["models_count"] >= 1


# ---------------------------------------------------------------------------
# POST /v1/chat/completions — T3.2.1 请求归一化
# ---------------------------------------------------------------------------


class TestChatCompletionsNormalization:
    @pytest.mark.asyncio
    async def test_returns_minimal_success_response(self, client: AsyncClient):
        resp = await client.post(
            "/v1/chat/completions",
            headers={
                "X-OpenWebUI-User-Id": "user-1",
                "X-OpenWebUI-Chat-Id": "chat-1",
            },
            json={"model": "roco-agent", "messages": [{"role": "user", "content": "hello"}]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["object"] == "chat.completion"
        assert body["model"] == "roco-agent"
        assert body["choices"][0]["message"]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_missing_headers_returns_session_error(self, client: AsyncClient):
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "roco-agent", "messages": [{"role": "user", "content": "hello"}]},
        )
        assert resp.status_code == 400
        error = resp.json()["error"]
        assert error["code"] == "SESSION_MISSING_IDENTITY"
        assert error["type"] == "invalid_request_error"

    @pytest.mark.asyncio
    async def test_unknown_model_returns_model_error(self, client: AsyncClient):
        resp = await client.post(
            "/v1/chat/completions",
            headers={
                "X-OpenWebUI-User-Id": "user-1",
                "X-OpenWebUI-Chat-Id": "chat-1",
            },
            json={"model": "missing-model", "messages": [{"role": "user", "content": "hello"}]},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "MODEL_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_non_vision_model_with_image_returns_capability_error(self, client: AsyncClient):
        from agent_backend.api.routes_openai import init_router

        init_router(
            ModelCatalog(
                entries=[
                    ModelCatalogEntry(
                        public_model_id="text-only",
                        provider_model_name="provider/text-only",
                        provider_base_url="http://localhost",
                        supports_vision=False,
                        enabled=True,
                    )
                ]
            ),
            runtime_factory=lambda: _FakeChatRuntime(),
        )

        resp = await client.post(
            "/v1/chat/completions",
            headers={
                "X-OpenWebUI-User-Id": "user-1",
                "X-OpenWebUI-Chat-Id": "chat-1",
            },
            json={
                "model": "text-only",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "看看这只精灵"},
                            {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}},
                        ],
                    }
                ],
            },
        )
        assert resp.status_code == 400
        error = resp.json()["error"]
        assert error["code"] == "CAPABILITY_VISION_UNSUPPORTED"
        assert error["metadata"]["retryable"] is True


# ---------------------------------------------------------------------------
# ModelCatalog 单元测试
# ---------------------------------------------------------------------------


class TestModelCatalog:
    def test_default_catalog_has_roco_agent(self):
        catalog = ModelCatalog()
        entry = catalog.get("roco-agent")
        assert entry is not None
        assert entry.public_model_id == "roco-agent"
        assert entry.supports_vision is True
        assert entry.enabled is True

    def test_custom_entries(self):
        custom = ModelCatalogEntry(
            public_model_id="test-model",
            provider_model_name="provider/test",
            provider_base_url="http://localhost",
            supports_vision=False,
            enabled=True,
        )
        catalog = ModelCatalog(entries=[custom])
        assert catalog.get("test-model") is not None
        assert catalog.get("roco-agent") is None

    def test_list_models_excludes_disabled(self):
        entries = [
            ModelCatalogEntry("a", "p/a", "http://x", True, True),
            ModelCatalogEntry("b", "p/b", "http://x", False, False),
        ]
        catalog = ModelCatalog(entries=entries)
        models = catalog.list_models()
        assert len(models) == 1
        assert models[0]["id"] == "a"

    def test_can_accept_image(self):
        entry = ModelCatalogEntry("x", "p/x", "http://x", True, True)
        assert entry.can_accept_image() is True
        entry.enabled = False
        assert entry.can_accept_image() is False
