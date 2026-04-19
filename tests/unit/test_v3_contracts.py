"""
Unit tests for v3 team analysis contracts and errors.

验证 T1.1.1: 固化 v3 工作台共享契约在数据层的输入/输出边界
"""

from dataclasses import asdict

import pytest

from src.data_layer.app.contracts import (
    TeamAnalysisSection,
    TeamAnalysisSnapshot,
    TeamDraft,
)
from src.data_layer.app.errors import (
    TeamAnalysisDataGapError,
    TeamAnalysisInputError,
)


class TestTeamDraft:
    """Test TeamDraft shared contract."""

    def test_team_draft_requires_schema_version(self):
        """TeamDraft must have schema_version field."""
        draft = TeamDraft(
            schema_version="v1",
            slots=[],
        )
        assert draft.schema_version == "v1"
        assert draft.slots == []

    def test_team_draft_with_slots(self):
        """TeamDraft can hold slot data."""
        draft = TeamDraft(
            schema_version="v1",
            slots=[
                {"slot_index": 0, "spirit_name": "火神", "skills": []},
                {"slot_index": 1, "spirit_name": "水神", "skills": []},
            ],
            metadata={"created_by": "user"},
        )
        assert len(draft.slots) == 2
        assert draft.slots[0]["spirit_name"] == "火神"
        assert draft.metadata["created_by"] == "user"


class TestTeamAnalysisSection:
    """Test TeamAnalysisSection contract."""

    def test_section_requires_key_and_title(self):
        """Section must have key and title."""
        section = TeamAnalysisSection(
            key="attack_distribution",
            title="攻向分布",
            items=[],
            status="ready",
        )
        assert section.key == "attack_distribution"
        assert section.title == "攻向分布"

    def test_section_status_enum(self):
        """Section status must be one of allowed values."""
        valid_statuses = ["ready", "insufficient_data", "partial_unavailable"]
        for status in valid_statuses:
            section = TeamAnalysisSection(
                key="test",
                title="Test",
                items=[],
                status=status,
            )
            assert section.status == status

    def test_section_can_have_notes(self):
        """Section can carry notes for partial data scenarios."""
        section = TeamAnalysisSection(
            key="defense_focus",
            title="防守侧重点",
            items=[],
            status="partial_unavailable",
            notes=["部分精灵资料缺失"],
        )
        assert len(section.notes) == 1
        assert section.notes[0] == "部分精灵资料缺失"


class TestTeamAnalysisSnapshot:
    """Test TeamAnalysisSnapshot contract."""

    def test_snapshot_requires_schema_version(self):
        """Snapshot must have schema_version."""
        snapshot = TeamAnalysisSnapshot(
            schema_version="v1",
            request_id="req-123",
            team_fingerprint="fp-abc",
            attack_distribution=TeamAnalysisSection(
                key="attack_distribution",
                title="攻向分布",
                items=[],
                status="ready",
            ),
            attack_coverage=TeamAnalysisSection(
                key="attack_coverage",
                title="攻击覆盖",
                items=[],
                status="ready",
            ),
            defense_focus=TeamAnalysisSection(
                key="defense_focus",
                title="防守侧重点",
                items=[],
                status="ready",
            ),
            resistance_highlights=TeamAnalysisSection(
                key="resistance_highlights",
                title="抗性较多",
                items=[],
                status="ready",
            ),
            pressure_points=TeamAnalysisSection(
                key="pressure_points",
                title="易被压制",
                items=[],
                status="ready",
            ),
        )
        assert snapshot.schema_version == "v1"
        assert snapshot.request_id == "req-123"
        assert snapshot.team_fingerprint == "fp-abc"

    def test_snapshot_can_have_missing_data_notes(self):
        """Snapshot can track which data is missing."""
        snapshot = TeamAnalysisSnapshot(
            schema_version="v1",
            request_id="req-123",
            team_fingerprint="fp-abc",
            attack_distribution=TeamAnalysisSection(
                key="attack_distribution",
                title="攻向分布",
                items=[],
                status="partial_unavailable",
            ),
            attack_coverage=TeamAnalysisSection(
                key="attack_coverage",
                title="攻击覆盖",
                items=[],
                status="partial_unavailable",
            ),
            defense_focus=TeamAnalysisSection(
                key="defense_focus",
                title="防守侧重点",
                items=[],
                status="partial_unavailable",
            ),
            resistance_highlights=TeamAnalysisSection(
                key="resistance_highlights",
                title="抗性较多",
                items=[],
                status="partial_unavailable",
            ),
            pressure_points=TeamAnalysisSection(
                key="pressure_points",
                title="易被压制",
                items=[],
                status="partial_unavailable",
            ),
            missing_data_notes=["槽位2精灵资料缺失", "槽位5精灵资料缺失"],
        )
        assert len(snapshot.missing_data_notes) == 2
        assert "槽位2精灵资料缺失" in snapshot.missing_data_notes


class TestTeamAnalysisErrors:
    """Test TEAM_ANALYSIS_ error semantics."""

    def test_team_analysis_input_error_code_prefix(self):
        """TeamAnalysisInputError must have TEAM_ANALYSIS_ prefix."""
        error = TeamAnalysisInputError("Invalid team draft format")
        assert error.error_code == "TEAM_ANALYSIS_INVALID_INPUT"
        assert error.error_code.startswith("TEAM_ANALYSIS_")
        assert not error.retryable

    def test_team_analysis_input_error_message(self):
        """TeamAnalysisInputError carries message."""
        error = TeamAnalysisInputError("Missing required field: slots")
        assert error.message == "Missing required field: slots"

    def test_team_analysis_data_gap_error_code_prefix(self):
        """TeamAnalysisDataGapError must have TEAM_ANALYSIS_ prefix."""
        error = TeamAnalysisDataGapError("Partial data gap")
        assert error.error_code == "TEAM_ANALYSIS_PARTIAL_DATA_GAP"
        assert error.error_code.startswith("TEAM_ANALYSIS_")
        assert not error.retryable

    def test_team_analysis_data_gap_error_tracks_missing_sections(self):
        """TeamAnalysisDataGapError can track which sections are missing."""
        error = TeamAnalysisDataGapError(
            "Some spirit profiles missing",
            missing_sections=["attack_coverage", "defense_focus"],
        )
        assert len(error.missing_sections) == 2
        assert "attack_coverage" in error.missing_sections
        assert "defense_focus" in error.missing_sections

    def test_team_analysis_data_gap_error_default_missing_sections(self):
        """TeamAnalysisDataGapError defaults to empty missing_sections."""
        error = TeamAnalysisDataGapError("Partial data gap")
        assert error.missing_sections == []


class TestContractSerialization:
    """Test contracts can be serialized to dict for API responses."""

    def test_team_draft_to_dict(self):
        """TeamDraft can be converted to dict."""
        draft = TeamDraft(
            schema_version="v1",
            slots=[{"slot_index": 0, "spirit_name": "火神"}],
        )
        draft_dict = asdict(draft)
        assert draft_dict["schema_version"] == "v1"
        assert len(draft_dict["slots"]) == 1

    def test_team_analysis_snapshot_to_dict(self):
        """TeamAnalysisSnapshot can be converted to dict."""
        snapshot = TeamAnalysisSnapshot(
            schema_version="v1",
            request_id="req-123",
            team_fingerprint="fp-abc",
            attack_distribution=TeamAnalysisSection(
                key="attack_distribution",
                title="攻向分布",
                items=[{"type": "火", "count": 2}],
                status="ready",
            ),
            attack_coverage=TeamAnalysisSection(
                key="attack_coverage",
                title="攻击覆盖",
                items=[],
                status="ready",
            ),
            defense_focus=TeamAnalysisSection(
                key="defense_focus",
                title="防守侧重点",
                items=[],
                status="ready",
            ),
            resistance_highlights=TeamAnalysisSection(
                key="resistance_highlights",
                title="抗性较多",
                items=[],
                status="ready",
            ),
            pressure_points=TeamAnalysisSection(
                key="pressure_points",
                title="易被压制",
                items=[],
                status="ready",
            ),
        )
        snapshot_dict = asdict(snapshot)
        assert snapshot_dict["schema_version"] == "v1"
        assert snapshot_dict["request_id"] == "req-123"
        assert snapshot_dict["attack_distribution"]["items"][0]["type"] == "火"
