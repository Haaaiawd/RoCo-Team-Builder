"""
内存会话仓库 — 基于 user_id:chat_id 组合键的 Session 管理。

对齐: agent-backend-system.md §4.2 Session Resolver
     agent-backend-system.detail.md §1 SESSION_POLICY, §2 SessionRecord
     agent-backend-system.detail.md §3.1 resolve_session_key
     agent-backend-system.detail.md §3.6 evict_idle_sessions
     ADR-003: 内存 Session + 单进程 + user_id:chat_id

不允许回退到仅 user_id 或随机 key。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


SESSION_POLICY = {
    "idle_ttl_minutes": 30,
    "max_messages_per_session": 40,
    "key_format": "user_id:chat_id",
    "missing_identity_action": "reject_400",
}


class SessionIdentityError(Exception):
    """会话身份缺失 — 任一头部缺失时拒绝请求。"""

    error_code: str = "SESSION_MISSING_IDENTITY"

    def __init__(self, message: str = "缺少必要的会话身份头部"):
        super().__init__(message)
        self.message = message


@dataclass
class SessionRecord:
    """单个会话记录 — 包含消息历史、访问时间和并发锁。"""

    session_key: str
    items: list[dict[str, Any]] = field(default_factory=list)
    last_access_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def touch(self) -> None:
        """更新最后访问时间。"""
        self.last_access_at = datetime.now(timezone.utc)

    def is_idle(self, ttl_minutes: int = SESSION_POLICY["idle_ttl_minutes"]) -> bool:
        """判断是否已闲置超时。"""
        now = datetime.now(timezone.utc)
        return (now - self.last_access_at) > timedelta(minutes=ttl_minutes)

    def add_item(self, item: dict[str, Any]) -> None:
        """添加消息到历史，超出上限时丢弃最早的。"""
        self.items.append(item)
        max_items = SESSION_POLICY["max_messages_per_session"]
        if len(self.items) > max_items:
            self.items = self.items[-max_items:]
        self.touch()


def resolve_session_key(headers: dict[str, str]) -> str:
    """从请求头部解析 session key。

    对齐: agent-backend-system.detail.md §3.1

    Args:
        headers: HTTP 请求头部

    Returns:
        稳定的 'user_id:chat_id' 组合键

    Raises:
        SessionIdentityError: 任一头部缺失
    """
    user_id = headers.get("x-openwebui-user-id") or headers.get("X-OpenWebUI-User-Id")
    chat_id = headers.get("x-openwebui-chat-id") or headers.get("X-OpenWebUI-Chat-Id")

    if not user_id or not chat_id:
        missing = []
        if not user_id:
            missing.append("X-OpenWebUI-User-Id")
        if not chat_id:
            missing.append("X-OpenWebUI-Chat-Id")
        raise SessionIdentityError(
            f"缺少必要的会话身份头部: {', '.join(missing)}"
        )

    return f"{user_id}:{chat_id}"


class SessionRegistry:
    """内存会话注册表 — 管理所有活跃会话。

    线程安全（单进程 asyncio 环境下使用 dict + per-session Lock）。
    """

    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}

    def get_or_create(self, session_key: str) -> SessionRecord:
        """获取或创建会话记录。"""
        if session_key not in self._sessions:
            from .session_extensions import SessionRecordExtended

            self._sessions[session_key] = SessionRecordExtended(session_key=session_key)
        record = self._sessions[session_key]
        record.touch()
        return record

    def get(self, session_key: str) -> SessionRecord | None:
        """获取已存在的会话记录，不创建。"""
        return self._sessions.get(session_key)

    def remove(self, session_key: str) -> bool:
        """移除指定会话。"""
        return self._sessions.pop(session_key, None) is not None

    def evict_idle_sessions(self, ttl_minutes: int | None = None) -> list[str]:
        """清理闲置会话。

        对齐: agent-backend-system.detail.md §3.6

        Returns:
            被清理的 session_key 列表
        """
        ttl = ttl_minutes if ttl_minutes is not None else SESSION_POLICY["idle_ttl_minutes"]
        evicted: list[str] = []
        for key in list(self._sessions.keys()):
            record = self._sessions[key]
            if record.is_idle(ttl):
                del self._sessions[key]
                evicted.append(key)
        return evicted

    @property
    def active_count(self) -> int:
        return len(self._sessions)

    @property
    def all_keys(self) -> list[str]:
        return list(self._sessions.keys())
