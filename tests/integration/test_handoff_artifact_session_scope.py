"""
Integration tests for Handoff Artifact and Session Scope.

验证 T3.1.1: 收口 handoff artifact 与已确认拥有列表的会话作用域闭环
"""

import pytest

from src.agent_backend.app.session_service import (
    SessionIdentityError,
    SessionRegistry,
    resolve_session_key,
)
from src.agent_backend.contracts.workbench import (
    ConfirmedOwnedSpiritList,
    WorkbenchHandOffPayload,
    build_empty_handoff,
)
from src.agent_backend.runtime.handoff_payload_builder import (
    build_confirmed_owned_list,
    build_workbench_payload,
)


class TestSessionKeyResolution:
    """Test session key resolution with strict identity requirements."""

    def test_resolve_session_key_with_valid_headers(self):
        """Valid headers should produce stable session key."""
        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }
        session_key = resolve_session_key(headers)
        assert session_key == "user123:chat456"

    def test_resolve_session_key_with_lowercase_headers(self):
        """Lowercase headers should also work (case-insensitive)."""
        headers = {
            "x-openwebui-user-id": "user123",
            "x-openwebui-chat-id": "chat456",
        }
        session_key = resolve_session_key(headers)
        assert session_key == "user123:chat456"

    def test_resolve_session_key_missing_user_id_rejects(self):
        """Missing user_id should reject request (no fallback)."""
        headers = {
            "X-OpenWebUI-Chat-Id": "chat456",
        }
        with pytest.raises(SessionIdentityError) as exc_info:
            resolve_session_key(headers)
        assert "X-OpenWebUI-User-Id" in str(exc_info.value)

    def test_resolve_session_key_missing_chat_id_rejects(self):
        """Missing chat_id should reject request (no fallback)."""
        headers = {
            "X-OpenWebUI-User-Id": "user123",
        }
        with pytest.raises(SessionIdentityError) as exc_info:
            resolve_session_key(headers)
        assert "X-OpenWebUI-Chat-Id" in str(exc_info.value)

    def test_resolve_session_key_missing_both_rejects(self):
        """Missing both headers should reject request."""
        headers = {}
        with pytest.raises(SessionIdentityError) as exc_info:
            resolve_session_key(headers)
        assert "X-OpenWebUI-User-Id" in str(exc_info.value)
        assert "X-OpenWebUI-Chat-Id" in str(exc_info.value)


class TestConfirmedOwnedListStorage:
    """Test ConfirmedOwnedSpiritList storage in session scope."""

    def test_store_confirmed_owned_list(self):
        """Store confirmed owned list in session."""
        registry = SessionRegistry()
        session_key = "user123:chat456"

        spirit_ids = ["fire_spirit", "water_spirit"]
        registry.store_confirmed_owned_list(session_key, spirit_ids)

        retrieved = registry.get_confirmed_owned_list(session_key)
        assert retrieved == spirit_ids

    def test_get_confirmed_owned_list_from_nonexistent_session(self):
        """Get owned list from nonexistent session returns empty list."""
        registry = SessionRegistry()
        session_key = "user999:chat999"

        retrieved = registry.get_confirmed_owned_list(session_key)
        assert retrieved == []

    def test_store_overwrites_previous_list(self):
        """Storing new list should overwrite previous one."""
        registry = SessionRegistry()
        session_key = "user123:chat456"

        # First store
        registry.store_confirmed_owned_list(session_key, ["fire_spirit"])

        # Second store (overwrite)
        registry.store_confirmed_owned_list(session_key, ["water_spirit", "earth_spirit"])

        retrieved = registry.get_confirmed_owned_list(session_key)
        assert retrieved == ["water_spirit", "earth_spirit"]

    def test_owned_list_isolated_by_session_key(self):
        """Owned lists should be isolated by session_key (user_id:chat_id)."""
        registry = SessionRegistry()

        # Different sessions
        registry.store_confirmed_owned_list("user1:chat1", ["fire_spirit"])
        registry.store_confirmed_owned_list("user1:chat2", ["water_spirit"])
        registry.store_confirmed_owned_list("user2:chat1", ["earth_spirit"])

        assert registry.get_confirmed_owned_list("user1:chat1") == ["fire_spirit"]
        assert registry.get_confirmed_owned_list("user1:chat2") == ["water_spirit"]
        assert registry.get_confirmed_owned_list("user2:chat1") == ["earth_spirit"]


class TestOwnedListConstraint:
    """Test owned list constraint application."""

    def test_constraint_filters_candidates_by_owned_list(self):
        """Constraint should filter candidates to only owned spirits."""
        registry = SessionRegistry()
        session_key = "user123:chat456"

        # Set owned list
        registry.store_confirmed_owned_list(session_key, ["fire_spirit", "water_spirit"])

        # Apply constraint
        candidates = ["fire_spirit", "water_spirit", "earth_spirit"]
        constrained, is_constrained = registry.apply_owned_list_constraint(
            session_key, candidates
        )

        assert constrained == ["fire_spirit", "water_spirit"]
        assert is_constrained is True

    def test_no_constraint_when_owned_list_empty(self):
        """No constraint should be applied when owned list is empty."""
        registry = SessionRegistry()
        session_key = "user123:chat456"

        # Don't set owned list (empty by default)

        candidates = ["fire_spirit", "water_spirit", "earth_spirit"]
        constrained, is_constrained = registry.apply_owned_list_constraint(
            session_key, candidates
        )

        assert constrained == candidates
        assert is_constrained is False

    def test_constraint_override_with_user_intent(self):
        """User can override constraint with explicit intent."""
        registry = SessionRegistry()
        session_key = "user123:chat456"

        # Set owned list
        registry.store_confirmed_owned_list(session_key, ["fire_spirit"])

        # User explicitly asks to ignore owned list
        candidates = ["fire_spirit", "water_spirit"]
        user_intent = "请忽略我的拥有列表，推荐所有精灵"
        constrained, is_constrained = registry.apply_owned_list_constraint(
            session_key, candidates, user_intent
        )

        assert constrained == candidates
        assert is_constrained is False

    def test_constraint_applied_without_override_intent(self):
        """Constraint should be applied when no override intent."""
        registry = SessionRegistry()
        session_key = "user123:chat456"

        # Set owned list
        registry.store_confirmed_owned_list(session_key, ["fire_spirit"])

        # Normal user intent (no override)
        candidates = ["fire_spirit", "water_spirit"]
        user_intent = "推荐一些好用的精灵"
        constrained, is_constrained = registry.apply_owned_list_constraint(
            session_key, candidates, user_intent
        )

        assert constrained == ["fire_spirit"]
        assert is_constrained is True


class TestWorkbenchHandOffPayload:
    """Test WorkbenchHandOffPayload construction and validation."""

    def test_build_workbench_payload_with_minimal_fields(self):
        """Build payload with minimal required fields."""
        team_draft = {
            "schema_version": "v1",
            "slots": [],
        }

        payload = build_workbench_payload(team_draft)

        assert payload.schema_version == "v1"
        assert payload.team_draft == team_draft
        assert payload.team_snapshot is None
        assert payload.wiki_targets == []
        assert payload.handoff_ready is True
        assert payload.source == "agent_chat"

    def test_build_workbench_payload_with_all_fields(self):
        """Build payload with all optional fields."""
        team_draft = {
            "schema_version": "v1",
            "slots": [
                {"slot_index": 0, "spirit_name": "fire_spirit", "skills": []},
            ],
        }
        team_snapshot = {
            "schema_version": "v1",
            "attack_distribution": {"status": "insufficient_data"},
        }
        wiki_targets = [
            {"canonical_name": "fire_spirit", "wiki_url": "https://wiki.biligame.com/..."},
        ]

        payload = build_workbench_payload(
            team_draft, team_snapshot, wiki_targets, source="user_manual"
        )

        assert payload.team_draft == team_draft
        assert payload.team_snapshot == team_snapshot
        assert payload.wiki_targets == wiki_targets
        assert payload.source == "user_manual"

    def test_build_workbench_payload_missing_schema_version_raises(self):
        """Missing schema_version should raise ValueError."""
        team_draft = {
            "slots": [],
        }

        with pytest.raises(ValueError) as exc_info:
            build_workbench_payload(team_draft)
        assert "schema_version" in str(exc_info.value)

    def test_build_workbench_payload_empty_draft_raises(self):
        """Empty team_draft should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            build_workbench_payload({})
        assert "team_draft" in str(exc_info.value)

    def test_build_workbench_payload_none_draft_raises(self):
        """None team_draft should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            build_workbench_payload(None)
        assert "team_draft" in str(exc_info.value)

    def test_build_empty_handoff_does_not_forge_payload(self):
        """Empty handoff should return payload with handoff_ready=False."""
        payload = build_empty_handoff()

        assert payload.handoff_ready is False
        assert payload.team_draft == {}
        assert payload.schema_version == "v1"


class TestConfirmedOwnedSpiritList:
    """Test ConfirmedOwnedSpiritList dataclass."""

    def test_build_confirmed_owned_list(self):
        """Build confirmed owned list with timestamp."""
        spirit_ids = ["fire_spirit", "water_spirit"]
        session_key = "user123:chat456"

        owned_list = build_confirmed_owned_list(spirit_ids, session_key)

        assert owned_list.spirit_ids == spirit_ids
        assert owned_list.session_key == session_key
        assert owned_list.confirmed_at is not None
        # ISO format: either ends with Z or +00:00
        assert owned_list.confirmed_at.endswith("Z") or "+00:00" in owned_list.confirmed_at

    def test_confirmed_owned_list_is_empty(self):
        """is_empty should return True for empty list."""
        owned_list = ConfirmedOwnedSpiritList(
            spirit_ids=[],
            confirmed_at="2026-04-19T00:00:00Z",
            session_key="user123:chat456",
        )
        assert owned_list.is_empty() is True

    def test_confirmed_owned_list_contains(self):
        """contains should check if spirit_id is in list."""
        owned_list = ConfirmedOwnedSpiritList(
            spirit_ids=["fire_spirit", "water_spirit"],
            confirmed_at="2026-04-19T00:00:00Z",
            session_key="user123:chat456",
        )
        assert owned_list.contains("fire_spirit") is True
        assert owned_list.contains("earth_spirit") is False


class TestHandoffArtifactValidation:
    """Test handoff artifact validation (acceptance criteria)."""

    def test_agent_output_with_handoff_ready_team_includes_valid_payload(self):
        """Given Agent outputs handoff-ready team, response includes valid payload."""
        team_draft = {
            "schema_version": "v1",
            "slots": [
                {"slot_index": 0, "spirit_name": "fire_spirit", "skills": []},
            ],
        }

        payload = build_workbench_payload(team_draft)

        assert payload.is_valid() is True
        assert payload.handoff_ready is True

    def test_follow_up_recommendation_with_owned_list_constraint_applies(self):
        """Given user confirmed owned list, follow-up recommendation applies constraint."""
        registry = SessionRegistry()
        session_key = "user123:chat456"

        # User confirms owned list
        registry.store_confirmed_owned_list(session_key, ["fire_spirit"])

        # Follow-up recommendation request
        candidates = ["fire_spirit", "water_spirit", "earth_spirit"]
        constrained, is_constrained = registry.apply_owned_list_constraint(
            session_key, candidates
        )

        # Constraint should be applied within current session
        assert constrained == ["fire_spirit"]
        assert is_constrained is True

    def test_missing_fields_in_handoff_does_not_forge_payload(self):
        """Given handoff payload missing fields, artifact generation does not forge."""
        # Simulate missing fields scenario
        team_draft = {}  # Missing schema_version

        with pytest.raises(ValueError):
            build_workbench_payload(team_draft)

        # Use empty handoff instead of forging
        payload = build_empty_handoff()
        assert payload.handoff_ready is False
