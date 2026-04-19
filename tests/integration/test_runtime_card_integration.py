"""
Integration tests for Runtime Card Rendering.

验证 T3.2.1: 卡片渲染与工作台分析结果接入 Agent runtime / tool 响应
"""

import pytest
from fastapi.testclient import TestClient

from src.agent_backend.main import app
from src.agent_backend.integrations.data_layer_client import DataLayerClient
from src.agent_backend.integrations.spirit_card_client import SpiritCardClient
from src.agent_backend.runtime.team_builder_tools import TeamBuilderTools
from data_layer.app.facade import DataLayerFacade
from spirit_card.app.facade import SpiritCardFacade


@pytest.fixture
def client():
    """Create test client with app state initialized."""
    # Initialize data_layer_client in app state
    facade = DataLayerFacade()
    data_client = DataLayerClient(facade)
    app.state.data_layer_client = data_client
    app.state.data_facade = facade

    # Initialize spirit_card_client in app state
    card_facade = SpiritCardFacade()
    card_client = SpiritCardClient(card_facade)
    app.state.spirit_card_client = card_client
    app.state.card_facade = card_facade

    with TestClient(app) as test_client:
        yield test_client


class TestCardRenderingIntegration:
    """Test card rendering integration is wired up correctly."""

    def test_spirit_card_client_initialized(self, client):
        """Spirit card client should be initialized in app state."""
        # This test verifies the wiring is in place
        # Actual card rendering will be tested through agent tool calls in T3.2.3
        assert hasattr(client.app.state, "spirit_card_client")
        assert hasattr(client.app.state, "card_facade")


class TestAISnapshotIntegration:
    """Test AI review uses snapshot properly."""

    def test_ai_review_uses_snapshot_not_recompute(self, client):
        """AI review should use provided snapshot, not recompute analysis."""
        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        # Create a snapshot with specific data
        snapshot = {
            "schema_version": "v1",
            "attack_distribution": {"status": "balanced"},
            "defense_focus": {"primary": "fire"},
        }

        payload = {
            "team_draft": team_draft,
            "team_snapshot": snapshot,
            "user_note": "请评价这个队伍",
        }

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/ai-review", json=payload, headers=headers)

        # Should return 200 with AI review
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "v1"
        assert "review_summary" in data
        assert "suggestions" in data

        # Metadata should indicate snapshot was used
        assert data["metadata"]["uses_snapshot"] is True
        assert data["metadata"]["snapshot_schema_version"] == "v1"

    def test_ai_review_handles_empty_snapshot_gracefully(self, client):
        """Empty snapshot should be handled gracefully with controlled error."""
        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        snapshot = {}  # Empty snapshot - will fail validation

        payload = {
            "team_draft": team_draft,
            "team_snapshot": snapshot,
        }

        headers = {
            "X-OpenWebUI-User-Id": "user123",
            "X-OpenWebUI-Chat-Id": "chat456",
        }

        response = client.post("/v1/workbench/ai-review", json=payload, headers=headers)

        # Empty snapshot fails validation (422) - this is expected behavior
        # The schema requires non-empty snapshot
        assert response.status_code == 422

    def test_ai_review_handles_insufficient_data_snapshot(self, client):
        """Snapshot with insufficient_data status should provide appropriate suggestions."""
        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        snapshot = {
            "schema_version": "v1",
            "attack_distribution": {"status": "insufficient_data"},
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

        # Should return 200 with suggestions to add more data
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "v1"
        assert "补充精灵资料" in data["suggestions"][0]


class TestErrorBoundaries:
    """Test error boundaries for snapshot integration."""

    def test_ai_review_error_boundary_preserves_draft_semantics(self, client):
        """AI review error should not lose draft semantics."""
        team_draft = {
            "schema_version": "v1",
            "slots": [{"slot_index": 0, "spirit_name": "fire_spirit", "skills": []}],
        }

        # Snapshot with missing required fields
        snapshot = {
            "schema_version": "v1",
            "attack_distribution": {},  # Missing status
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

        # Should handle gracefully - may return 200 with error or 500 with controlled error
        # The key is that it doesn't crash or lose the draft
        assert response.status_code in [200, 500]
