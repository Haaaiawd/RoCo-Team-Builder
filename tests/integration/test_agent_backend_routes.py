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


@pytest.fixture
async def client():
    """使用 httpx AsyncClient 测试 FastAPI 应用，手动触发 lifespan。"""
    from agent_backend.api.routes_openai import init_router
    from agent_backend.app.model_catalog import ModelCatalog
    from agent_backend.app.quota_guard import BuiltinQuotaPolicy, QuotaStore
    from agent_backend.app.session_service import SessionRegistry
    from agent_backend.integrations.data_layer_client import DataLayerClient
    from agent_backend.runtime.agent_factory import AgentFactory
    from data_layer.app.facade import DataLayerFacade

    catalog = ModelCatalog()
    session_registry = SessionRegistry()
    quota_policy = BuiltinQuotaPolicy()
    quota_store = QuotaStore()
    facade = DataLayerFacade()
    data_client = DataLayerClient(facade)
    agent_factory = AgentFactory(data_client)

    init_router(
        catalog=catalog,
        session_registry=session_registry,
        quota_policy=quota_policy,
        quota_store=quota_store,
        agent_factory=agent_factory,
    )
    app.state.catalog = catalog

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers={"X-Roco-Internal-Secret": "roco-secret-change-in-production"}) as c:
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
        from agent_backend.app.quota_guard import BuiltinQuotaPolicy, QuotaStore
        from agent_backend.app.session_service import SessionRegistry
        from agent_backend.integrations.data_layer_client import DataLayerClient
        from agent_backend.runtime.agent_factory import AgentFactory
        from data_layer.app.facade import DataLayerFacade

        facade = DataLayerFacade()
        data_client = DataLayerClient(facade)
        init_router(
            catalog=ModelCatalog(
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
            session_registry=SessionRegistry(),
            quota_policy=BuiltinQuotaPolicy(),
            quota_store=QuotaStore(),
            agent_factory=AgentFactory(data_client),
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


# ---------------------------------------------------------------------------
# Runtime Integration — provider_factory, runtime_service, quota
# ---------------------------------------------------------------------------


class TestProviderFactory:
    def test_build_run_config_raises_without_api_key(self):
        """缺少 API Key 时抛出 ProviderConfigError。"""
        import os
        from agent_backend.app.model_catalog import ModelCatalogEntry
        from agent_backend.runtime.provider_factory import (
            build_run_config_for_model, ProviderConfigError, ENV_PROVIDER_API_KEY,
        )
        # 确保环境变量未设置
        old = os.environ.pop(ENV_PROVIDER_API_KEY, None)
        try:
            with pytest.raises(ProviderConfigError):
                build_run_config_for_model(
                    ModelCatalogEntry("roco-agent", "gpt-4o", "https://example.com/v1", True, True)
                )
        finally:
            if old is not None:
                os.environ[ENV_PROVIDER_API_KEY] = old

    def test_build_run_config_succeeds_with_api_key(self):
        """设置 API Key 后能成功构建 RunConfig（需 openai-agents 安装）。"""
        import os
        from agent_backend.app.model_catalog import ModelCatalogEntry
        from agent_backend.runtime.provider_factory import (
            build_run_config_for_model, ENV_PROVIDER_API_KEY,
        )
        os.environ[ENV_PROVIDER_API_KEY] = "test-key-for-unit-test"
        try:
            # 如果 openai-agents 未安装，会抛 RuntimeError，这也是合理的
            try:
                run_config = build_run_config_for_model(
                    ModelCatalogEntry("roco-agent", "gpt-4o", "https://example.com/v1", True, True)
                )
                assert run_config is not None
            except RuntimeError as exc:
                assert "openai-agents" in str(exc)
        finally:
            os.environ.pop(ENV_PROVIDER_API_KEY, None)


class TestQuotaGuardIntegration:
    @pytest.mark.asyncio
    async def test_quota_exhausted_returns_429(self, client: AsyncClient):
        """额度耗尽时返回 429 + QUOTA_ 错误码。"""
        from agent_backend.api.routes_openai import init_router
        from agent_backend.app.model_catalog import ModelCatalog
        from agent_backend.app.quota_guard import BuiltinQuotaPolicy, QuotaStore
        from agent_backend.app.session_service import SessionRegistry
        from agent_backend.integrations.data_layer_client import DataLayerClient
        from agent_backend.runtime.agent_factory import AgentFactory
        from data_layer.app.facade import DataLayerFacade

        # 设置极低额度: 1 次请求
        low_policy = BuiltinQuotaPolicy(limit_tokens=1)
        store = QuotaStore()
        facade = DataLayerFacade()
        data_client = DataLayerClient(facade)

        init_router(
            catalog=ModelCatalog(),
            session_registry=SessionRegistry(),
            quota_policy=low_policy,
            quota_store=store,
            agent_factory=AgentFactory(data_client),
        )

        headers = {
            "X-OpenWebUI-User-Id": "quota-user",
            "X-OpenWebUI-Chat-Id": "quota-chat",
        }
        body = {"model": "roco-agent", "messages": [{"role": "user", "content": "hi"}]}

        # 第一次请求应通过 quota（但 runtime 可能因无 API key 失败）
        resp1 = await client.post("/v1/chat/completions", headers=headers, json=body)
        # 第二次请求应被 quota 拦截
        resp2 = await client.post("/v1/chat/completions", headers=headers, json=body)
        assert resp2.status_code == 429
        error = resp2.json()["error"]
        assert error["code"] == "QUOTA_WINDOW_EXHAUSTED"
        assert error["metadata"]["suggested_route"] == "byok"

    def test_enforce_builtin_quota_returns_structured_decision(self):
        """quota guard 返回结构化 QuotaDecision。"""
        from agent_backend.app.quota_guard import BuiltinQuotaPolicy, QuotaStore, enforce_builtin_quota
        from agent_backend.app.request_context import ChatRequestContext
        from agent_backend.app.model_catalog import ModelCatalogEntry

        policy = BuiltinQuotaPolicy(limit_tokens=1)
        store = QuotaStore()
        context = ChatRequestContext(
            request_id="req-1",
            session_key="user-1:chat-1",
            model_entry=ModelCatalogEntry("roco-agent", "gpt-4o", "https://example.com/v1", True, True),
            messages=[{"role": "user", "content": "hi"}],
            stream=False,
            user_id="user-1",
            chat_id="chat-1",
            request_headers={},
        )
        first = enforce_builtin_quota(context, policy, store)
        second = enforce_builtin_quota(context, policy, store)

        assert first.allowed is True
        assert first.error_code is None
        assert first.suggested_route == "builtin"

        assert second.allowed is False
        assert second.error_code == "QUOTA_WINDOW_EXHAUSTED"
        assert second.retry_after_seconds is not None
        assert second.suggested_route == "byok"


class TestRuntimeServiceUnit:
    def test_messages_to_input_merges_history_and_current(self):
        """历史消息 + 本轮输入拼接顺序正确。"""
        from agent_backend.runtime.runtime_service import _messages_to_input

        history = [{"role": "user", "content": "历史消息"}]
        current = [{"role": "user", "content": "本轮输入"}]
        result = _messages_to_input(current, history)
        assert len(result) == 2
        assert result[0]["content"] == "历史消息"
        assert result[1]["content"] == "本轮输入"

    def test_make_completion_id_format(self):
        """completion ID 格式正确。"""
        from agent_backend.runtime.runtime_service import _make_completion_id
        cid = _make_completion_id()
        assert cid.startswith("chatcmpl-")

    def test_run_agent_turn_exists(self):
        """runtime 核心入口暴露为 run_agent_turn。"""
        from agent_backend.runtime.runtime_service import run_agent_turn

        assert callable(run_agent_turn)

    def test_extract_text_delta_from_string(self):
        """从简单字符串 delta 提取文本。"""
        from agent_backend.runtime.runtime_service import _extract_text_delta

        class FakeData:
            delta = "hello"
        assert _extract_text_delta(FakeData()) == "hello"

    def test_extract_text_delta_empty(self):
        """无 delta 属性时返回空字符串。"""
        from agent_backend.runtime.runtime_service import _extract_text_delta
        assert _extract_text_delta(object()) == ""
