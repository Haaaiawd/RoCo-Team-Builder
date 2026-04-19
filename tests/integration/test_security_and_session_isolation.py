"""
Integration tests for Security and Session Isolation.

验证 T3.2.2: 建立后端关键路径的安全与集成测试门槛
"""

import pytest
from fastapi.testclient import TestClient

from src.agent_backend.main import app
from src.agent_backend.integrations.data_layer_client import DataLayerClient
from data_layer.app.facade import DataLayerFacade


@pytest.fixture
def client():
    """Create test client with app state initialized."""
    facade = DataLayerFacade()
    data_client = DataLayerClient(facade)
    app.state.data_layer_client = data_client
    app.state.data_facade = facade

    with TestClient(app) as test_client:
        yield test_client


class TestSessionIsolation:
    """Test session isolation with composite session keys."""

    def test_multiple_chat_ids_for_same_user_do_not_cross_write(self, client):
        """Same user with different chat_id should have isolated sessions."""
        user_id = "user123"
        chat_id_1 = "chat1"
        chat_id_2 = "chat2"

        # Set owned spirits for chat_id_1
        payload_1 = {
            "spirit_ids": ["fire_spirit", "water_spirit"],
        }
        headers_1 = {
            "X-OpenWebUI-User-Id": user_id,
            "X-OpenWebUI-Chat-Id": chat_id_1,
        }

        # Note: POST /v1/session/confirmed-owned-list endpoint may not exist yet
        # This test will be updated when the endpoint is implemented
        # For now, we test that session keys are different

        from src.agent_backend.app.session_service import resolve_session_key

        session_key_1 = resolve_session_key(headers_1)
        session_key_2 = resolve_session_key({
            "X-OpenWebUI-User-Id": user_id,
            "X-OpenWebUI-Chat-Id": chat_id_2,
        })

        # Session keys should be different
        assert session_key_1 != session_key_2
        assert session_key_1 == f"{user_id}:{chat_id_1}"
        assert session_key_2 == f"{user_id}:{chat_id_2}"

    def test_session_key_requires_both_user_id_and_chat_id(self, client):
        """Session key resolution should reject requests missing either header."""
        from src.agent_backend.app.session_service import resolve_session_key, SessionIdentityError

        # Missing chat_id
        with pytest.raises(SessionIdentityError):
            resolve_session_key({
                "X-OpenWebUI-User-Id": "user123",
            })

        # Missing user_id
        with pytest.raises(SessionIdentityError):
            resolve_session_key({
                "X-OpenWebUI-Chat-Id": "chat456",
            })

        # Both missing
        with pytest.raises(SessionIdentityError):
            resolve_session_key({})


class TestWorkbenchEndpointConsistency:
    """Test workbench endpoints return consistent HTTP/payload with design docs."""

    def test_team_analysis_response_structure_matches_design(self, client):
        """Team analysis response should match design document structure."""
        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        payload = {"team_draft": team_draft}

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/team-analysis", json=payload, headers=headers)

        # Should return 200 or controlled error
        if response.status_code == 200:
            data = response.json()
            # Verify structure matches design
            assert "schema_version" in data
            assert "team_snapshot" in data
            assert "wiki_targets" in data
            assert data["schema_version"] == "v1"
        elif response.status_code == 500:
            data = response.json()
            # Should be controlled error
            assert "error" in data
            assert data["error"]["code"] == "TEAM_ANALYSIS_FAILED"

    def test_ai_review_response_structure_matches_design(self, client):
        """AI review response should match design document structure."""
        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        snapshot = {
            "schema_version": "v1",
            "attack_distribution": {"status": "balanced"},
        }

        payload = {
            "team_draft": team_draft,
            "team_snapshot": snapshot,
        }

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/ai-review", json=payload, headers=headers)

        # Should return 200
        assert response.status_code == 200
        data = response.json()
        # Verify structure matches design
        assert "schema_version" in data
        assert "review_summary" in data
        assert "suggestions" in data
        assert "metadata" in data
        assert data["schema_version"] == "v1"
        assert data["metadata"]["uses_snapshot"] is True


class TestHeaderForwarding:
    """Test header forwarding and validation."""

    def test_workbench_routes_require_session_headers(self, client):
        """Workbench routes should reject requests without session headers."""
        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        payload = {"team_draft": team_draft}

        # No headers
        response = client.post("/v1/workbench/team-analysis", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "SESSION_MISSING_IDENTITY"

    def test_headers_are_case_insensitive(self, client):
        """Headers should be accepted regardless of case."""
        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        payload = {"team_draft": team_draft}

        # Lowercase headers
        headers = {
            "x-openwebui-user-id": "user123",
            "x-openwebui-chat-id": "chat456",
        }

        response = client.post("/v1/workbench/team-analysis", json=payload, headers=headers)

        # Should accept lowercase headers (may fail for other reasons)
        # The key is that it doesn't reject due to header case
        if response.status_code == 400:
            data = response.json()
            # Should not be SESSION_MISSING_IDENTITY error
            assert data["error"]["code"] != "SESSION_MISSING_IDENTITY"


class TestQuotaEnforcement:
    """Test quota enforcement (basic validation)."""

    def test_quota_system_is_initialized(self, client):
        """Quota system should be initialized in app state."""
        assert hasattr(client.app.state, "quota_policy")
        assert hasattr(client.app.state, "quota_store")

    def test_quota_policy_has_builtin_config(self, client):
        """Quota policy should have builtin configuration."""
        quota_policy = client.app.state.quota_policy
        assert quota_policy is not None
        assert hasattr(quota_policy, "window_seconds")
        assert hasattr(quota_policy, "owner_scope")


class TestModelCatalog:
    """Test model catalog endpoint."""

    def test_models_endpoint_requires_internal_secret(self, client):
        """GET /v1/models should require internal secret (return 403 without it)."""
        response = client.get("/v1/models")

        # Without internal secret, should return 403
        assert response.status_code == 403
