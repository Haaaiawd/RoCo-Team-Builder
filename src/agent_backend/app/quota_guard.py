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
from typing import Literal

from .request_context import ChatRequestContext


@dataclass
class QuotaDecision:
    """额度决策结果。"""

    allowed: bool
    error_code: str | None
    retry_after_seconds: int | None
    suggested_route: Literal["builtin", "byok"] | None


@dataclass
class BuiltinQuotaPolicy:
    """Builtin 轨道额度策略。"""

    owner_scope: Literal["ip", "session"] = "session"
    window_seconds: int = 1800
    limit_tokens: int = 120000
    exhaustion_action: Literal["suggest_byok"] = "suggest_byok"

    def owner_key_for(self, context: ChatRequestContext) -> str:
        if self.owner_scope == "ip":
            return context.request_headers.get("x-forwarded-for", "unknown_ip")
        return context.session_key


@dataclass
class BuiltinQuotaState:
    """Builtin 轨道额度状态。"""

    owner_key: str
    window_started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tokens_used: int = 0
    tokens_remaining: int = 0
    status: Literal["available", "exhausted"] = "available"

    def is_window_expired(self, policy: BuiltinQuotaPolicy) -> bool:
        """判断时间窗口是否已过期。"""
        now = datetime.now(timezone.utc)
        return (now - self.window_started_at) > timedelta(seconds=policy.window_seconds)

    def reset_window(self, policy: BuiltinQuotaPolicy) -> None:
        """重置时间窗口和计数器。"""
        self.window_started_at = datetime.now(timezone.utc)
        self.tokens_used = 0
        self.tokens_remaining = policy.limit_tokens
        self.status = "available"

    def consume(self, token_cost: int, policy: BuiltinQuotaPolicy) -> None:
        """消耗额度并刷新状态。"""
        self.tokens_used += token_cost
        self.tokens_remaining = max(0, policy.limit_tokens - self.tokens_used)
        self.status = "exhausted" if self.tokens_used >= policy.limit_tokens else "available"

    def is_exhausted(self) -> bool:
        """判断额度是否已耗尽。"""
        return self.status == "exhausted"


class QuotaStore:
    """额度状态存储（内存实现）。"""

    def __init__(self) -> None:
        self._states: dict[str, BuiltinQuotaState] = {}

    def get_or_create(self, owner_key: str, policy: BuiltinQuotaPolicy) -> BuiltinQuotaState:
        """获取额度状态，不存在则按策略初始化。"""
        if owner_key not in self._states:
            state = BuiltinQuotaState(owner_key=owner_key)
            state.reset_window(policy)
            self._states[owner_key] = state
        return self._states[owner_key]

    def reset_state(self, owner_key: str) -> None:
        """重置用户额度状态。"""
        if owner_key in self._states:
            del self._states[owner_key]


def _seconds_until_window_reset(
    state: BuiltinQuotaState,
    policy: BuiltinQuotaPolicy,
) -> int:
    """计算距离窗口重置的剩余秒数。"""
    window_end = state.window_started_at + timedelta(seconds=policy.window_seconds)
    now = datetime.now(timezone.utc)
    remaining = (window_end - now).total_seconds()
    return max(0, int(remaining))


def _estimate_token_cost(context: ChatRequestContext) -> int:
    token_budget = context.normalized_token_budget()
    if token_budget is not None and token_budget > 0:
        return token_budget

    total_text_chars = 0
    for message in context.messages:
        content = message.get("content")
        if isinstance(content, str):
            total_text_chars += len(content)
            continue
        if not isinstance(content, list):
            continue
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                total_text_chars += len(part.get("text", ""))

    return max(1, total_text_chars // 4)


def enforce_builtin_quota(
    context: ChatRequestContext,
    policy: BuiltinQuotaPolicy,
    store: QuotaStore,
) -> QuotaDecision:
    """执行 Builtin 轨道额度检查。

    对齐: agent-backend-system.md §5.1 enforce_builtin_quota

    Args:
        context: ChatRequestContext
        policy: 额度策略
        store: 额度状态存储

    Returns:
        结构化 QuotaDecision
    """
    owner_key = policy.owner_key_for(context)
    if not owner_key:
        return QuotaDecision(
            allowed=True,
            error_code=None,
            retry_after_seconds=None,
            suggested_route="builtin",
        )

    state = store.get_or_create(owner_key, policy)

    # 检查时间窗口是否过期
    if state.is_window_expired(policy):
        state.reset_window(policy)

    if state.is_exhausted():
        return QuotaDecision(
            allowed=False,
            error_code="QUOTA_WINDOW_EXHAUSTED",
            retry_after_seconds=_seconds_until_window_reset(state, policy),
            suggested_route="byok",
        )

    token_cost = _estimate_token_cost(context)

    # 检查额度是否超限
    if state.tokens_used + token_cost > policy.limit_tokens:
        state.tokens_remaining = 0
        state.status = "exhausted"
        return QuotaDecision(
            allowed=False,
            error_code="QUOTA_WINDOW_EXHAUSTED",
            retry_after_seconds=_seconds_until_window_reset(state, policy),
            suggested_route="byok",
        )

    # 额度允许，增加计数
    state.consume(token_cost, policy)
    return QuotaDecision(
        allowed=True,
        error_code=None,
        retry_after_seconds=None,
        suggested_route="builtin",
    )
