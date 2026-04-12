"""
额度守卫 — Builtin 轨道额度管理。

职责：
- 定义额度策略（BuiltinQuotaPolicy）
- 管理额度状态（BuiltinQuotaState）
- 执行额度检查（enforce_builtin_quota）
- 明确区分 QUOTA_ 与 RATE_LIMIT_ 错误码

对齐: agent-backend-system.md §3.5 错误矩阵、§3.6 Builtin Quota
验收标准: T3.3.1 额度耗尽返回 QUOTA_ 错误
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class QuotaDecision(Enum):
    """额度决策结果。"""

    ALLOWED = "allowed"
    QUOTA_EXCEEDED = "quota_exceeded"


@dataclass
class BuiltinQuotaPolicy:
    """Builtin 轨道额度策略。"""

    requests_per_window: int = 100  # 时间窗口内最大请求数
    window_minutes: int = 60  # 时间窗口长度（分钟）


@dataclass
class BuiltinQuotaState:
    """Builtin 轨道额度状态。"""

    user_id: str
    request_count: int = 0
    window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_window_expired(self, policy: BuiltinQuotaPolicy) -> bool:
        """判断时间窗口是否已过期。"""
        now = datetime.now(timezone.utc)
        return (now - self.window_start) > timedelta(minutes=policy.window_minutes)

    def reset_window(self) -> None:
        """重置时间窗口和计数器。"""
        self.window_start = datetime.now(timezone.utc)
        self.request_count = 0

    def increment(self) -> None:
        """增加请求计数。"""
        self.request_count += 1

    def is_quota_exceeded(self, policy: BuiltinQuotaPolicy) -> bool:
        """判断额度是否已超限。"""
        return self.request_count >= policy.requests_per_window


class QuotaStore:
    """额度状态存储（内存实现）。"""

    def __init__(self) -> None:
        self._states: dict[str, BuiltinQuotaState] = {}

    def get_state(self, user_id: str) -> BuiltinQuotaState:
        """获取用户额度状态，不存在则创建。"""
        if user_id not in self._states:
            self._states[user_id] = BuiltinQuotaState(user_id=user_id)
        return self._states[user_id]

    def reset_state(self, user_id: str) -> None:
        """重置用户额度状态。"""
        if user_id in self._states:
            del self._states[user_id]


def enforce_builtin_quota(
    context: dict[str, Any],
    policy: BuiltinQuotaPolicy,
    store: QuotaStore,
) -> QuotaDecision:
    """执行 Builtin 轨道额度检查。

    对齐: agent-backend-system.md §5.1 enforce_builtin_quota

    Args:
        context: ChatRequestContext（简化为 dict）
        policy: 额度策略
        store: 额度状态存储

    Returns:
        QuotaDecision.ALLOWED 或 QuotaDecision.QUOTA_EXCEEDED
    """
    user_id = context.get("user_id")
    if not user_id:
        return QuotaDecision.ALLOWED  # 无 user_id 时跳过额度检查

    state = store.get_state(user_id)

    # 检查时间窗口是否过期
    if state.is_window_expired(policy):
        state.reset_window()

    # 检查额度是否超限
    if state.is_quota_exceeded(policy):
        return QuotaDecision.QUOTA_EXCEEDED

    # 额度允许，增加计数
    state.increment()
    return QuotaDecision.ALLOWED
