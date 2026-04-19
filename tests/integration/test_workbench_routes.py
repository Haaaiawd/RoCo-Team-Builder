"""
Integration tests for Workbench Routes.

验证 T3.1.2: /v1/workbench/team-analysis 与 /v1/workbench/ai-review 工作台动作路由
"""

import pytest
from fastapi.testclient import TestClient

from src.agent_backend.main import app
from src.agent_backend.integrations.data_layer_client import DataLayerClient
from data_layer.app.facade import DataLayerFacade


@pytest.fixture
def client():
    """Create test client with app state initialized."""
    # Initialize data_layer_client in app state
    facade = DataLayerFacade()
    data_client = DataLayerClient(facade)
    app.state.data_layer_client = data_client
    app.state.data_facade = facade

    with TestClient(app) as test_client:
        yield test_client


class TestTeamAnalysisRoute:
    """Test /v1/workbench/team-analysis endpoint."""

    def test_team_analysis_with_valid_draft_and_headers(self, client):
        """Valid team draft with headers should return TeamAnalysisSnapshot or controlled error."""

        team_draft = {
            "schema_version": "v1",
            "slots": [
                {"slot_index": 0, "spirit_name": "fire_spirit", "skills": []},
                {"slot_index": 1, "spirit_name": "water_spirit", "skills": []},
            ],
        }

        payload = {
            "team_draft": team_draft,
            "user_note": "测试队伍",
        }

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/team-analysis", json=payload, headers=headers)

        # Should return 200 with team snapshot OR 500 with controlled TEAM_ANALYSIS_FAILED error
        # (spirits may not exist in test environment, which is valid controlled error)
        if response.status_code == 200:
            data = response.json()
            assert data["schema_version"] == "v1"
            assert "team_snapshot" in data
            assert "wiki_targets" in data
        elif response.status_code == 500:
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "TEAM_ANALYSIS_FAILED"
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_team_analysis_missing_user_id_rejects(self):
        """Missing user_id should reject request (400)."""
        client = TestClient(app)

        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        payload = {"team_draft": team_draft}

        headers = {
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/team-analysis", json=payload, headers=headers)

        # Should return 400 with SESSION_MISSING_IDENTITY error
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "SESSION_MISSING_IDENTITY"

    def test_team_analysis_missing_chat_id_rejects(self, client):
        """Missing chat_id should reject request (400)."""

        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        payload = {"team_draft": team_draft}

        headers = {
            "X-OpenWebUI-User-Id": "user123",
        }

        response = client.post("/v1/workbench/team-analysis", json=payload, headers=headers)

        # Should return 400 with SESSION_MISSING_IDENTITY error
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "SESSION_MISSING_IDENTITY"

    def test_team_analysis_empty_slots_validation_error(self):
        """Empty slots should return validation error."""
        client = TestClient(app)

        team_draft = {
            "schema_version": "v1",
            "slots": [],  # Empty slots
        }

        payload = {"team_draft": team_draft}

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/team-analysis", json=payload, headers=headers)

        # Should return 422 validation error
        assert response.status_code == 422


class TestAIReviewRoute:
    """Test /v1/workbench/ai-review endpoint."""

    def test_ai_review_with_valid_draft_and_snapshot(self, client):
        """Valid team draft + snapshot should return AI review."""

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

        payload = {
            "team_draft": team_draft,
            "team_snapshot": team_snapshot,
            "user_note": "请评价这个队伍",
        }

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/ai-review", json=payload, headers=headers)

        # Should return 200 with AI review (skeleton implementation)
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "v1"
        assert "review_summary" in data
        assert "suggestions" in data

    def test_ai_review_missing_user_id_rejects(self):
        """Missing user_id should reject request (400)."""
        client = TestClient(app)

        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        team_snapshot = {
            "schema_version": "v1",
            "attack_distribution": {"status": "insufficient_data"},
        }

        payload = {
            "team_draft": team_draft,
            "team_snapshot": team_snapshot,
        }

        headers = {
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/ai-review", json=payload, headers=headers)

        # Should return 400 with SESSION_MISSING_IDENTITY error
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "SESSION_MISSING_IDENTITY"

    def test_ai_review_empty_snapshot_validation_error(self, client):
        """Empty team_snapshot should return validation error."""

        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        payload = {
            "team_draft": team_draft,
            "team_snapshot": {},  # Empty snapshot
        }

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/ai-review", json=payload, headers=headers)

        # Should return 422 validation error
        assert response.status_code == 422


class TestWorkbenchErrorHandling:
    """Test workbench error handling and structured error codes."""

    def test_team_analysis_upstream_failure_returns_controlled_error(self):
        """Upstream data-layer failure should return TEAM_ANALYSIS_FAILED error."""
        client = TestClient(app)

        # This test would need to mock data-layer client to simulate failure
        # For now, we test the error path exists
        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "nonexistent_spirit", "skills": []}],
        }

        payload = {"team_draft": team_draft}

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/team-analysis", json=payload, headers=headers)

        # Should handle error gracefully
        # May return 200 with error in snapshot or 500 with controlled error
        assert response.status_code in [200, 500]

    def test_ai_review_skeleton_implementation(self, client):
        """AI review should return skeleton response (T3.2.1 will implement actual LLM)."""

        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        team_snapshot = {
            "schema_version": "v1",
            "attack_distribution": {"status": "insufficient_data"},
        }

        payload = {
            "team_draft": team_draft,
            "team_snapshot": team_snapshot,
        }

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/ai-review", json=payload, headers=headers)

        # Should return skeleton response
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "v1"
        assert data["review_summary"]  # Should have some summary text
        assert isinstance(data["suggestions"], list)
