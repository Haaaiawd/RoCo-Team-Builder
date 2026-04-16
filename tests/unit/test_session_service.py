"""
T3.1.2 测试 — 会话键解析、内存会话仓库与闲置清理。

验收标准:
  - Given 双头部存在 → 生成稳定 user_id:chat_id 组合键并加锁
  - Given 任一头部缺失 → 返回 400 + SESSION_ 语义
  - Given 30 分钟无操作 → 会话被移出 registry
  - 同用户不同 chat_id 隔离
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from agent_backend.app.session_extensions import SessionRecordExtended
from agent_backend.app.session_service import (
    SESSION_POLICY,
    SessionIdentityError,
    SessionRecord,
    SessionRegistry,
    resolve_session_key,
)
from agent_backend.app.request_context import ChatRequestContext
from agent_backend.app.model_catalog import ModelCatalogEntry


# ---------------------------------------------------------------------------
# resolve_session_key
# ---------------------------------------------------------------------------


class TestResolveSessionKey:
    def test_valid_headers(self):
        """双头部齐全时返回稳定组合键。"""
        key = resolve_session_key({
            "x-openwebui-user-id": "user-abc",
            "x-openwebui-chat-id": "chat-123",
        })
        assert key == "user-abc:chat-123"

    def test_mixed_case_headers(self):
        """支持大写形式的头部。"""
        key = resolve_session_key({
            "X-OpenWebUI-User-Id": "user-abc",
            "X-OpenWebUI-Chat-Id": "chat-123",
        })
        assert key == "user-abc:chat-123"

    def test_missing_user_id(self):
        """缺少 user_id 时抛出 SessionIdentityError。"""
        with pytest.raises(SessionIdentityError) as exc_info:
            resolve_session_key({"x-openwebui-chat-id": "chat-123"})
        assert "User-Id" in str(exc_info.value)
        assert exc_info.value.error_code == "SESSION_MISSING_IDENTITY"

    def test_missing_chat_id(self):
        """缺少 chat_id 时抛出 SessionIdentityError。"""
        with pytest.raises(SessionIdentityError) as exc_info:
            resolve_session_key({"x-openwebui-user-id": "user-abc"})
        assert "Chat-Id" in str(exc_info.value)

    def test_both_missing(self):
        """双头部都缺失时抛出 SessionIdentityError。"""
        with pytest.raises(SessionIdentityError) as exc_info:
            resolve_session_key({})
        assert "User-Id" in str(exc_info.value)
        assert "Chat-Id" in str(exc_info.value)

    def test_empty_string_values(self):
        """空字符串等价于缺失。"""
        with pytest.raises(SessionIdentityError):
            resolve_session_key({
                "x-openwebui-user-id": "",
                "x-openwebui-chat-id": "chat-123",
            })


# ---------------------------------------------------------------------------
# SessionRecord
# ---------------------------------------------------------------------------


class TestSessionRecord:
    def test_initial_state(self):
        record = SessionRecord(session_key="u:c")
        assert record.session_key == "u:c"
        assert record.items == []
        assert record.lock is not None

    def test_touch_updates_time(self):
        record = SessionRecord(session_key="u:c")
        old_time = record.last_access_at
        record.touch()
        assert record.last_access_at >= old_time

    def test_is_idle(self):
        record = SessionRecord(session_key="u:c")
        record.last_access_at = datetime.now(timezone.utc) - timedelta(minutes=31)
        assert record.is_idle(ttl_minutes=30) is True

    def test_not_idle(self):
        record = SessionRecord(session_key="u:c")
        assert record.is_idle(ttl_minutes=30) is False

    def test_add_item(self):
        record = SessionRecord(session_key="u:c")
        record.add_item({"role": "user", "content": "hello"})
        assert len(record.items) == 1

    def test_add_item_truncation(self):
        """超出 max_messages_per_session 时丢弃最早的。"""
        record = SessionRecord(session_key="u:c")
        max_items = SESSION_POLICY["max_messages_per_session"]
        for i in range(max_items + 10):
            record.add_item({"index": i})
        assert len(record.items) == max_items
        assert record.items[0]["index"] == 10


# ---------------------------------------------------------------------------
# SessionRegistry
# ---------------------------------------------------------------------------


class TestSessionRegistry:
    def test_get_or_create(self):
        reg = SessionRegistry()
        record = reg.get_or_create("u1:c1")
        assert isinstance(record, SessionRecord)
        assert record.session_key == "u1:c1"
        assert reg.active_count == 1

    def test_get_or_create_returns_extended_record(self):
        """registry 应返回可承载 owned_spirits 的扩展 session。"""
        reg = SessionRegistry()
        record = reg.get_or_create("u1:c1")
        assert isinstance(record, SessionRecordExtended)

    def test_owned_spirits_persist_in_registry_session(self):
        """同一 session_key 再次获取时，owned_spirits 应保留。"""
        reg = SessionRegistry()
        record = reg.get_or_create("u1:c1")
        record.set_owned_spirits(["火神", "冰龙王"])

        same_record = reg.get_or_create("u1:c1")
        assert isinstance(same_record, SessionRecordExtended)
        assert same_record.get_owned_spirits() == ["火神", "冰龙王"]

    def test_get_or_create_idempotent(self):
        """同一 key 返回同一 record。"""
        reg = SessionRegistry()
        r1 = reg.get_or_create("u1:c1")
        r2 = reg.get_or_create("u1:c1")
        assert r1 is r2

    def test_different_chat_id_isolation(self):
        """同用户不同 chat_id 隔离。"""
        reg = SessionRegistry()
        r1 = reg.get_or_create("user-a:chat-1")
        r2 = reg.get_or_create("user-a:chat-2")
        assert r1 is not r2
        r1.add_item({"msg": "only in chat-1"})
        assert len(r2.items) == 0
        assert reg.active_count == 2

    def test_get_existing(self):
        reg = SessionRegistry()
        reg.get_or_create("u1:c1")
        assert reg.get("u1:c1") is not None
        assert reg.get("nonexistent") is None

    def test_remove(self):
        reg = SessionRegistry()
        reg.get_or_create("u1:c1")
        assert reg.remove("u1:c1") is True
        assert reg.active_count == 0
        assert reg.remove("u1:c1") is False

    def test_evict_idle_sessions(self):
        """闲置清理: 超时会话被移出。"""
        reg = SessionRegistry()
        active = reg.get_or_create("active:c1")
        idle = reg.get_or_create("idle:c1")
        idle.last_access_at = datetime.now(timezone.utc) - timedelta(minutes=31)

        evicted = reg.evict_idle_sessions(ttl_minutes=30)
        assert "idle:c1" in evicted
        assert "active:c1" not in evicted
        assert reg.active_count == 1
        assert reg.get("idle:c1") is None

    def test_evict_returns_empty_when_all_active(self):
        reg = SessionRegistry()
        reg.get_or_create("u1:c1")
        reg.get_or_create("u2:c2")
        evicted = reg.evict_idle_sessions()
        assert evicted == []
        assert reg.active_count == 2

    def test_all_keys(self):
        reg = SessionRegistry()
        reg.get_or_create("a:1")
        reg.get_or_create("b:2")
        assert set(reg.all_keys) == {"a:1", "b:2"}


# ---------------------------------------------------------------------------
# ChatRequestContext 基础检查
# ---------------------------------------------------------------------------


class TestChatRequestContext:
    def test_instantiation(self):
        entry = ModelCatalogEntry("m", "p/m", "http://x", True, True)
        ctx = ChatRequestContext(
            request_id="req-1",
            session_key="u:c",
            model_entry=entry,
            messages=[{"role": "user", "content": "hi"}],
            stream=False,
            user_id="u",
            chat_id="c",
        )
        assert ctx.session_key == "u:c"
        assert ctx.normalized_token_budget() is None
