"""
工作台共享契约 — WorkbenchHandOffPayload 与相关数据类。

对齐: data-layer-system.md §3.5 Shared Objects
     agent-backend-system.md §6 数据模型
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class ConfirmedOwnedSpiritList:
    """用户确认拥有的精灵列表 — chat 作用域。

    由用户在工作台中确认的精灵 ID 列表，用于后续推荐约束。
    仅在当前 user_id:chat_id 会话内生效，不持久化，不跨 chat 共享。
    """

    spirit_ids: list[str]
    confirmed_at: str  # ISO 8601 timestamp
    session_key: str  # "{user_id}:{chat_id}"

    def is_empty(self) -> bool:
        """判断是否为空列表。"""
        return len(self.spirit_ids) == 0

    def contains(self, spirit_id: str) -> bool:
        """判断是否包含指定精灵 ID。"""
        return spirit_id in self.spirit_ids


@dataclass(frozen=True)
class WorkbenchHandOffPayload:
    """工作台承接载荷 — 从 Agent 聊天结果传递到工作台的 artifact。

    当 Agent 输出可承接队伍时，响应中附带此载荷，使前端能稳定
    承接到工作台，而不依赖自然语言文案反推队伍字段。
    """

    schema_version: str  # "v1"
    team_draft: dict
    team_snapshot: dict | None = None
    wiki_targets: list[dict] = field(default_factory=list)
    handoff_ready: bool = True
    source: Literal["agent_chat", "user_manual"] = "agent_chat"

    def is_valid(self) -> bool:
        """判断载荷是否有效。"""
        required_fields = ["schema_version", "team_draft"]
        return all(getattr(self, field) is not None for field in required_fields)

    def has_snapshot(self) -> bool:
        """判断是否包含队伍分析快照。"""
        return self.team_snapshot is not None

    def has_wiki_targets(self) -> bool:
        """判断是否包含 wiki 目标。"""
        return len(self.wiki_targets) > 0


def build_empty_handoff() -> WorkbenchHandOffPayload:
    """构建空的承接载荷（用于字段缺失时不返回伪造 payload）。"""
    return WorkbenchHandOffPayload(
        schema_version="v1",
        team_draft={},
        handoff_ready=False,
    )
