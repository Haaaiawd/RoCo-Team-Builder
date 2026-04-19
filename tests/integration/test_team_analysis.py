"""
Integration tests for Team Analysis Service.

验证 T1.1.2: 实现 Team Analysis Service 与部分数据缺失降级逻辑
通过 in-process facade + 静态样本验证五类区块、空草稿和部分缺失三类场景。
"""

import pytest

from src.data_layer.app.errors import TeamAnalysisDataGapError, TeamAnalysisInputError
from src.data_layer.app.facade import DataLayerFacade
from src.data_layer.analysis.draft_normalizer import (
    build_team_fingerprint,
    normalize_team_draft,
)
from src.data_layer.analysis.snapshot_builder import analyze_team_draft
from src.data_layer.analysis.wiki_link_resolver import build_wiki_link, build_wiki_targets


class TestDraftNormalizer:
    """Test TeamDraft normalization logic."""

    def test_normalize_valid_draft(self):
        """Valid TeamDraft should be normalized correctly."""
        draft = {
            "schema_version": "v1",
            "slots": [
                {"slot_index": 0, "spirit_name": "火神", "skills": [{"name": "火球"}]},
                {"slot_index": 1, "spirit_name": "水神", "skills": []},
            ],
        }

        normalized = normalize_team_draft(draft)

        assert normalized["schema_version"] == "v1"
        assert len(normalized["slots"]) == 2
        assert normalized["slots"][0]["spirit_name"] == "火神"
        assert normalized["slots"][1]["spirit_name"] == "水神"

    def test_normalize_strips_ui_transient_fields(self):
        """UI transient fields should be stripped."""
        draft = {
            "schema_version": "v1",
            "slots": [
                {
                    "slot_index": 0,
                    "spirit_name": "火神",
                    "skills": [],
                    "loading": True,
                    "selected": False,
                    "ui_state": {"expanded": True},
                }
            ],
        }

        normalized = normalize_team_draft(draft)

        slot = normalized["slots"][0]
        assert "loading" not in slot
        assert "selected" not in slot
        assert "ui_state" not in slot
        assert slot["spirit_name"] == "火神"

    def test_normalize_missing_schema_version_raises_error(self):
        """Missing schema_version should raise TeamAnalysisInputError."""
        draft = {"slots": []}

        with pytest.raises(TeamAnalysisInputError) as exc:
            normalize_team_draft(draft)

        assert "schema_version" in str(exc.value)

    def test_normalize_unsupported_schema_version_raises_error(self):
        """Unsupported schema_version should raise TeamAnalysisInputError."""
        draft = {"schema_version": "v2", "slots": []}

        with pytest.raises(TeamAnalysisInputError) as exc:
            normalize_team_draft(draft)

        assert "v2" in str(exc.value)

    def test_normalize_invalid_slots_raises_error(self):
        """Invalid slots should raise TeamAnalysisInputError."""
        draft = {"schema_version": "v1", "slots": "not a list"}

        with pytest.raises(TeamAnalysisInputError) as exc:
            normalize_team_draft(draft)

        assert "must be a list" in str(exc.value)

    def test_normalize_missing_slot_index_raises_error(self):
        """Missing slot_index should raise TeamAnalysisInputError."""
        draft = {
            "schema_version": "v1",
            "slots": [{"spirit_name": "火神"}],
        }

        with pytest.raises(TeamAnalysisInputError) as exc:
            normalize_team_draft(draft)

        assert "slot_index" in str(exc.value)


class TestTeamFingerprint:
    """Test team fingerprint building."""

    def test_fingerprint_consistent_for_same_team(self):
        """Same team should produce same fingerprint."""
        slots = [
            {"slot_index": 0, "spirit_name": "火神", "skills": []},
            {"slot_index": 1, "spirit_name": "水神", "skills": []},
        ]

        fp1 = build_team_fingerprint(slots)
        fp2 = build_team_fingerprint(slots)

        assert fp1 == fp2

    def test_fingerprint_respects_slot_order(self):
        """Different slot order should produce different fingerprint."""
        slots1 = [
            {"slot_index": 0, "spirit_name": "火神", "skills": []},
            {"slot_index": 1, "spirit_name": "水神", "skills": []},
        ]
        slots2 = [
            {"slot_index": 0, "spirit_name": "水神", "skills": []},
            {"slot_index": 1, "spirit_name": "火神", "skills": []},
        ]

        fp1 = build_team_fingerprint(slots1)
        fp2 = build_team_fingerprint(slots2)

        assert fp1 != fp2

    def test_fingerprint_includes_skills(self):
        """Fingerprint should include skill names."""
        slots = [
            {
                "slot_index": 0,
                "spirit_name": "火神",
                "skills": [{"name": "火球"}, {"name": "爆裂"}],
            }
        ]

        fp = build_team_fingerprint(slots)

        assert "火球" in fp
        assert "爆裂" in fp


class TestWikiLinkResolver:
    """Test wiki link resolution."""

    def test_build_wiki_link(self):
        """Wiki link should be built correctly."""
        link = build_wiki_link("火神")
        assert link == "https://wiki.biligame.com/rocokingdomworld/%E7%81%AB%E7%A5%9E"

    def test_build_wiki_link_empty_name(self):
        """Empty spirit name should return empty string."""
        link = build_wiki_link("")
        assert link == ""

    def test_build_wiki_targets(self):
        """Wiki targets should be built from profiles."""
        profiles = [
            {"canonical_name": "火神", "wiki_url": "https://example.com/fire"},
            {"canonical_name": "水神", "wiki_url": "https://example.com/water"},
        ]

        targets = build_wiki_targets(profiles)

        assert len(targets) == 2
        assert targets[0]["canonical_name"] == "火神"
        assert targets[1]["canonical_name"] == "水神"

    def test_build_wiki_targets_fallback_url(self):
        """Missing wiki_url should trigger fallback link building."""
        profiles = [{"canonical_name": "火神"}]

        targets = build_wiki_targets(profiles)

        assert len(targets) == 1
        assert targets[0]["canonical_name"] == "火神"
        assert targets[0]["wiki_url"].startswith("https://wiki.biligame.com/")


class TestSnapshotBuilder:
    """Test snapshot building logic."""

    def test_build_snapshot_with_full_data(self):
        """Full data should produce ready status for all sections."""
        normalized = {
            "schema_version": "v1",
            "slots": [
                {"slot_index": 0, "spirit_name": "火神", "skills": []},
                {"slot_index": 1, "spirit_name": "水神", "skills": []},
            ],
        }

        profiles = [
            {
                "canonical_name": "火神",
                "types": ["火"],
                "base_stats": {"hp": 100, "defense": 50, "magic_defense": 50},
                "wiki_url": "https://example.com/fire",
            },
            {
                "canonical_name": "水神",
                "types": ["水"],
                "base_stats": {"hp": 100, "defense": 50, "magic_defense": 50},
                "wiki_url": "https://example.com/water",
            },
        ]

        snapshot = analyze_team_draft(
            normalized_draft=normalized,
            spirit_profiles=profiles,
            missing_slots=[],
        )

        assert snapshot.schema_version == "v1"
        assert snapshot.attack_distribution.status == "ready"
        assert snapshot.attack_coverage.status == "ready"
        assert snapshot.defense_focus.status == "ready"
        assert snapshot.resistance_highlights.status == "ready"
        assert snapshot.pressure_points.status == "ready"
        assert len(snapshot.missing_data_notes) == 0
        assert len(snapshot.wiki_targets) == 2

    def test_build_snapshot_empty_team(self):
        """Empty team should produce insufficient_data status."""
        normalized = {"schema_version": "v1", "slots": []}

        snapshot = analyze_team_draft(
            normalized_draft=normalized,
            spirit_profiles=[],
            missing_slots=[],
        )

        assert snapshot.attack_distribution.status == "insufficient_data"
        assert snapshot.defense_focus.status == "insufficient_data"
        assert len(snapshot.missing_data_notes) == 0

    def test_build_snapshot_partial_data_gap(self):
        """Partial data gap should produce partial_unavailable status."""
        normalized = {
            "schema_version": "v1",
            "slots": [
                {"slot_index": 0, "spirit_name": "火神", "skills": []},
                {"slot_index": 1, "spirit_name": "水神", "skills": []},
            ],
        }

        profiles = [
            {
                "canonical_name": "火神",
                "types": ["火"],
                "base_stats": {"hp": 100, "defense": 50, "magic_defense": 50},
                "wiki_url": "https://example.com/fire",
            }
        ]

        snapshot = analyze_team_draft(
            normalized_draft=normalized,
            spirit_profiles=profiles,
            missing_slots=[1],
        )

        assert snapshot.attack_distribution.status == "partial_unavailable"
        assert snapshot.attack_coverage.status == "partial_unavailable"
        assert len(snapshot.missing_data_notes) == 1
        assert "槽位 1" in snapshot.missing_data_notes[0]

    def test_build_snapshot_all_data_missing_raises_error(self):
        """All data missing should raise TeamAnalysisDataGapError."""
        normalized = {
            "schema_version": "v1",
            "slots": [
                {"slot_index": 0, "spirit_name": "火神", "skills": []},
                {"slot_index": 1, "spirit_name": "水神", "skills": []},
            ],
        }

        with pytest.raises(TeamAnalysisDataGapError) as exc:
            analyze_team_draft(
                normalized_draft=normalized,
                spirit_profiles=[],
                missing_slots=[0, 1],
            )

        assert exc.value.missing_sections == ["all"]

    def test_attack_distribution_section_content(self):
        """Attack distribution should count types correctly."""
        normalized = {"schema_version": "v1", "slots": []}
        profiles = [
            {"types": ["火", "龙"]},
            {"types": ["火"]},
            {"types": ["水"]},
        ]

        snapshot = analyze_team_draft(
            normalized_draft=normalized,
            spirit_profiles=profiles,
            missing_slots=[],
        )

        items = snapshot.attack_distribution.items
        type_counts = {item["type"]: item["count"] for item in items}

        assert type_counts.get("火") == 2
        assert type_counts.get("水") == 1
        assert type_counts.get("龙") == 1

    def test_defense_focus_section_content(self):
        """Defense focus should identify dominant defensive stat."""
        normalized = {"schema_version": "v1", "slots": []}
        profiles = [
            {"base_stats": {"hp": 80, "defense": 100, "magic_defense": 60}},
            {"base_stats": {"hp": 80, "defense": 100, "magic_defense": 60}},
        ]

        snapshot = analyze_team_draft(
            normalized_draft=normalized,
            spirit_profiles=profiles,
            missing_slots=[],
        )

        items = snapshot.defense_focus.items
        assert len(items) == 1
        assert "物理防御" in items[0].get("focus", "")

    def test_missing_data_notes_formatting(self):
        """Missing data notes should be formatted correctly."""
        normalized = {"schema_version": "v1", "slots": []}

        # Single missing
        snapshot = analyze_team_draft(
            normalized_draft=normalized,
            spirit_profiles=[],
            missing_slots=[0],
        )
        assert "槽位 0" in snapshot.missing_data_notes[0]

        # Multiple missing
        snapshot = analyze_team_draft(
            normalized_draft=normalized,
            spirit_profiles=[],
            missing_slots=[0, 1, 2],
        )
        assert "槽位 0, 1, 2" in snapshot.missing_data_notes[0]

        # Many missing
        snapshot = analyze_team_draft(
            normalized_draft=normalized,
            spirit_profiles=[],
            missing_slots=[0, 1, 2, 3, 4],
        )
        assert "槽位 0, 1, 2" in snapshot.missing_data_notes[0]
        assert "5 个槽位" in snapshot.missing_data_notes[0]


class TestFacadeIntegration:
    """Test facade integration with analysis service."""

    @pytest.mark.asyncio
    async def test_facade_analyze_team_draft_calls_normalizer(self):
        """Facade should call normalizer and raise on invalid input."""
        facade = DataLayerFacade()

        invalid_draft = {"slots": []}  # Missing schema_version

        with pytest.raises(TeamAnalysisInputError):
            await facade.analyze_team_draft(invalid_draft)

    @pytest.mark.asyncio
    async def test_facade_analyze_team_draft_with_empty_slots(self):
        """Facade should handle empty slots gracefully."""
        facade = DataLayerFacade()

        draft = {"schema_version": "v1", "slots": []}

        result = await facade.analyze_team_draft(draft)

        assert result["schema_version"] == "v1"
        assert result["attack_distribution"]["status"] == "insufficient_data"

    @pytest.mark.asyncio
    async def test_facade_analyze_team_draft_with_missing_spirit_names(self):
        """Facade should handle missing spirit names."""
        facade = DataLayerFacade()

        draft = {
            "schema_version": "v1",
            "slots": [
                {"slot_index": 0, "spirit_name": "", "skills": []},
                {"slot_index": 1, "spirit_name": "", "skills": []},
            ],
        }

        result = await facade.analyze_team_draft(draft)

        assert result["schema_version"] == "v1"
        assert len(result["missing_data_notes"]) > 0
        assert result["attack_distribution"]["status"] == "insufficient_data"
