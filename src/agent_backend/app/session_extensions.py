"""
会话扩展 — 为 SessionRecord 添加 owned_spirits 字段。

职责：
- 扩展 SessionRecord 添加 owned_spirits 字段
- 提供 owned_spirits 的读写接口
- 确保 owned_spirits 持久化到会话上下文

对齐: agent-backend-system.md §6 数据模型
验收标准: T3.2.4 owned_spirits 写入会话上下文
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .session_service import SessionRecord


@dataclass
class SessionRecordExtended(SessionRecord):
    """扩展的会话记录 — 包含 owned_spirits 字段。

    继承自 SessionRecord，添加用户确认拥有的精灵列表。
    """

    owned_spirits: list[str] = field(default_factory=list)

    def set_owned_spirits(self, spirit_names: list[str]) -> None:
        """设置用户拥有的精灵列表。"""
        self.owned_spirits = spirit_names

    def get_owned_spirits(self) -> list[str]:
        """获取用户拥有的精灵列表。"""
        return self.owned_spirits

    def has_owned_spirits(self) -> bool:
        """判断是否已设置 owned_spirits。"""
        return len(self.owned_spirits) > 0
