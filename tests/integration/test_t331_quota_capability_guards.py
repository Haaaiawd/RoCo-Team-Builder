"""
T3.3.1 集成测试 — Builtin 配额守卫与视觉能力后端兜底。

验收标准:
  - Given builtin 轨道额度已耗尽 → When 请求进入后端 → Then 返回 QUOTA_ 错误并建议切换 BYOK 或等待窗口重置
  - Given 图片请求命中不支持视觉的模型 → When 后端执行最终能力校验 → Then 返回 CAPABILITY_ 错误而不是透传 Provider 默认报错
  - Given Provider 真实限流 → When 上游返回限流错误 → Then 仍映射为 RATE_LIMIT_，不与 QUOTA_ 混用
"""

from __future__ import annotations

import pytest

from agent_backend.app.request_context import ChatRequestContext
from agent_backend.app.model_catalog import ModelCatalogEntry
from agent_backend.app.capability_guard import CapabilityDecision, check_vision_capability
from agent_backend.app.quota_guard import (
    BuiltinQuotaPolicy,
    BuiltinQuotaState,
    QuotaDecision,
    QuotaStore,
    enforce_builtin_quota,
)


class TestQuotaGuard:
    def _make_context(self, *, session_key: str = "user123:chat1", headers: dict[str, str] | None = None) -> ChatRequestContext:
        return ChatRequestContext(
            request_id="req-1",
            session_key=session_key,
            model_entry=ModelCatalogEntry("roco-agent", "gpt-4o", "https://example.com/v1", True, True),
            messages=[{"role": "user", "content": "hi"}],
            stream=False,
            user_id="user123",
            chat_id="chat1",
            request_headers=headers or {},
        )

    def test_quota_state_initialization(self):
        """额度状态初始化应包含默认值。"""
        state = BuiltinQuotaState(owner_key="user123:chat1")
        assert state.owner_key == "user123:chat1"
        assert state.tokens_used == 0
        assert state.window_started_at is not None

    def test_owner_key_for_session_scope(self):
        policy = BuiltinQuotaPolicy(owner_scope="session")
        context = self._make_context(session_key="user123:chat1")
        assert policy.owner_key_for(context) == "user123:chat1"

    def test_owner_key_for_ip_scope(self):
        policy = BuiltinQuotaPolicy(owner_scope="ip")
        context = self._make_context(headers={"x-forwarded-for": "1.2.3.4"})
        assert policy.owner_key_for(context) == "1.2.3.4"

    def test_quota_state_reset(self):
        """重置应清零计数器并更新窗口开始时间。"""
        policy = BuiltinQuotaPolicy(limit_tokens=100)
        state = BuiltinQuotaState(owner_key="user123:chat1")
        state.consume(50, policy)
        state.consume(20, policy)
        assert state.tokens_used == 70

        state.reset_window(policy)
        assert state.tokens_used == 0
        assert state.tokens_remaining == 100
        assert state.window_started_at is not None

    def test_is_exhausted(self):
        """判断额度是否超限。"""
        policy = BuiltinQuotaPolicy(limit_tokens=5)
        state = BuiltinQuotaState(owner_key="user123:chat1")
        state.reset_window(policy)
        state.consume(5, policy)
        assert state.is_exhausted() is True

    def test_quota_store_get_or_create(self):
        """额度存储应能获取或创建用户状态。"""
        policy = BuiltinQuotaPolicy(limit_tokens=100)
        store = QuotaStore()
        state1 = store.get_or_create("user123:chat1", policy)
        state2 = store.get_or_create("user123:chat1", policy)
        assert state1 is state2  # 同一用户返回同一实例

        state3 = store.get_or_create("user456:chat1", policy)
        assert state3 is not state1  # 不同用户返回不同实例

    def test_quota_store_reset_state(self):
        """额度存储应能重置用户状态。"""
        policy = BuiltinQuotaPolicy(limit_tokens=100)
        store = QuotaStore()
        store.get_or_create("user123:chat1", policy).consume(10, policy)
        store.reset_state("user123:chat1")

        state = store.get_or_create("user123:chat1", policy)
        assert state.tokens_used == 0

    def test_enforce_builtin_quota_allowed(self):
        """额度允许时返回 ALLOWED。"""
        policy = BuiltinQuotaPolicy(limit_tokens=100)
        store = QuotaStore()
        context = self._make_context()

        decision = enforce_builtin_quota(context, policy, store)
        assert isinstance(decision, QuotaDecision)
        assert decision.allowed is True
        assert decision.suggested_route == "builtin"

    def test_enforce_builtin_quota_exceeded(self):
        """额度超限时返回 QUOTA_EXCEEDED。"""
        policy = BuiltinQuotaPolicy(limit_tokens=0)
        store = QuotaStore()
        context = self._make_context()

        decision = enforce_builtin_quota(context, policy, store)
        assert decision.allowed is False
        assert decision.error_code == "QUOTA_WINDOW_EXHAUSTED"
        assert decision.suggested_route == "byok"

    def test_enforce_builtin_quota_ip_scope(self):
        """ip scope 时使用 x-forwarded-for 作为 owner key。"""
        policy = BuiltinQuotaPolicy(owner_scope="ip", limit_tokens=100)
        store = QuotaStore()
        context = self._make_context(headers={"x-forwarded-for": "1.2.3.4"})

        decision = enforce_builtin_quota(context, policy, store)
        assert decision.allowed is True
        assert store.get_or_create("1.2.3.4", policy).owner_key == "1.2.3.4"


class TestCapabilityGuard:
    def test_check_vision_capability_no_image(self):
        """无图片请求时返回 ALLOWED。"""
        context = {
            "messages": [
                {"role": "user", "content": "你好"}
            ]
        }
        decision = check_vision_capability(context, model_supports_vision=False)
        assert decision == CapabilityDecision.ALLOWED

    def test_check_vision_capability_image_with_support(self):
        """有图片且模型支持视觉时返回 ALLOWED。"""
        context = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "这是什么精灵？"},
                        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                    ]
                }
            ]
        }
        decision = check_vision_capability(context, model_supports_vision=True)
        assert decision == CapabilityDecision.ALLOWED

    def test_check_vision_capability_image_without_support(self):
        """有图片但模型不支持视觉时返回 CAPABILITY_MISMATCH。"""
        context = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "这是什么精灵？"},
                        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                    ]
                }
            ]
        }
        decision = check_vision_capability(context, model_supports_vision=False)
        assert decision == CapabilityDecision.CAPABILITY_MISMATCH

    def test_check_vision_capability_text_content_string(self):
        """文本内容为字符串时也能正确处理。"""
        context = {
            "messages": [
                {"role": "user", "content": "你好"}
            ]
        }
        decision = check_vision_capability(context, model_supports_vision=False)
        assert decision == CapabilityDecision.ALLOWED

    def test_check_vision_capability_multiple_messages(self):
        """多轮对话中检查图片。"""
        context = {
            "messages": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "这是什么？"},
                        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                    ]
                }
            ]
        }
        decision = check_vision_capability(context, model_supports_vision=False)
        assert decision == CapabilityDecision.CAPABILITY_MISMATCH
