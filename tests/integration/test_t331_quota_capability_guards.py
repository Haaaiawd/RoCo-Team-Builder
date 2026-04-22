"""
T3.3.1 集成测试 — Builtin 配额守卫与视觉能力后端兜底。

验收标准:
  - Given builtin 轨道额度已耗尽 → When 请求进入后端 → Then 返回 QUOTA_ 错误并建议切换 BYOK 或等待窗口重置
  - Given 图片请求命中不支持视觉的模型 → When 后端执行最终能力校验 → Then 返回 CAPABILITY_ 错误而不是透传 Provider 默认报错
  - Given Provider 真实限流 → When 上游返回限流错误 → Then 仍映射为 RATE_LIMIT_，不与 QUOTA_ 混用
"""

from __future__ import annotations


from agent_backend.app.capability_guard import CapabilityDecision, check_vision_capability
from agent_backend.app.quota_guard import (
    BuiltinQuotaPolicy,
    BuiltinQuotaState,
    QuotaDecision,
    QuotaStore,
    enforce_builtin_quota,
)


class TestQuotaGuard:
    def test_quota_state_initialization(self):
        """额度状态初始化应包含默认值。"""
        state = BuiltinQuotaState(user_id="user123")
        assert state.user_id == "user123"
        assert state.request_count == 0
        assert state.window_start is not None

    def test_quota_state_increment(self):
        """增加请求计数应正确更新。"""
        state = BuiltinQuotaState(user_id="user123")
        state.increment()
        assert state.request_count == 1
        state.increment()
        assert state.request_count == 2

    def test_quota_state_reset(self):
        """重置应清零计数器并更新窗口开始时间。"""
        state = BuiltinQuotaState(user_id="user123")
        state.increment()
        state.increment()
        assert state.request_count == 2

        state.reset_window()
        assert state.request_count == 0
        assert state.window_start is not None

    def test_is_quota_exceeded(self):
        """判断额度是否超限。"""
        policy = BuiltinQuotaPolicy(requests_per_window=5, window_minutes=60)
        state = BuiltinQuotaState(user_id="user123")

        for _ in range(5):
            state.increment()

        assert state.is_quota_exceeded(policy) is True

        state.increment()
        assert state.is_quota_exceeded(policy) is True

    def test_quota_store_get_state(self):
        """额度存储应能获取或创建用户状态。"""
        store = QuotaStore()
        state1 = store.get_state("user123")
        state2 = store.get_state("user123")
        assert state1 is state2  # 同一用户返回同一实例

        state3 = store.get_state("user456")
        assert state3 is not state1  # 不同用户返回不同实例

    def test_quota_store_reset_state(self):
        """额度存储应能重置用户状态。"""
        store = QuotaStore()
        store.get_state("user123").increment()
        store.reset_state("user123")

        state = store.get_state("user123")
        assert state.request_count == 0

    def test_enforce_builtin_quota_allowed(self):
        """额度允许时返回 ALLOWED。"""
        policy = BuiltinQuotaPolicy(requests_per_window=10, window_minutes=60)
        store = QuotaStore()
        context = {"user_id": "user123"}

        decision = enforce_builtin_quota(context, policy, store)
        assert decision == QuotaDecision.ALLOWED

    def test_enforce_builtin_quota_exceeded(self):
        """额度超限时返回 QUOTA_EXCEEDED。"""
        policy = BuiltinQuotaPolicy(requests_per_window=2, window_minutes=60)
        store = QuotaStore()
        context = {"user_id": "user123"}

        # 前两次请求允许
        assert enforce_builtin_quota(context, policy, store) == QuotaDecision.ALLOWED
        assert enforce_builtin_quota(context, policy, store) == QuotaDecision.ALLOWED

        # 第三次请求超限
        decision = enforce_builtin_quota(context, policy, store)
        assert decision == QuotaDecision.QUOTA_EXCEEDED

    def test_enforce_builtin_quota_no_user_id(self):
        """无 user_id 时跳过额度检查。"""
        policy = BuiltinQuotaPolicy(requests_per_window=0, window_minutes=60)
        store = QuotaStore()
        context = {}  # 无 user_id

        decision = enforce_builtin_quota(context, policy, store)
        assert decision == QuotaDecision.ALLOWED


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
