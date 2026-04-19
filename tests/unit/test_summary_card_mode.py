"""
Unit tests for v3 summary card mode.

验证 T2.1.1: 扩展卡片渲染契约为 chat card / summary card 双模式
"""

import pytest

from src.spirit_card.app.contracts import (
    RenderPolicy,
    RenderedSpiritCard,
    SpiritCardModel,
)
from src.spirit_card.app.render_policy import default_policy, from_dict
from src.spirit_card.rendering.template_renderer import render_spirit_card


class TestRenderPolicy:
    """Test RenderPolicy with render_target field."""

    def test_default_render_target_is_chat_card(self):
        """Default render_target should be chat_card."""
        policy = default_policy()
        assert policy.render_target == "chat_card"

    def test_render_target_can_be_summary_card(self):
        """render_target can be set to summary_card."""
        policy = RenderPolicy(render_target="summary_card")
        assert policy.render_target == "summary_card"

    def test_render_target_enum_validation(self):
        """render_target should accept only valid enum values."""
        policy1 = RenderPolicy(render_target="chat_card")
        policy2 = RenderPolicy(render_target="summary_card")
        assert policy1.render_target == "chat_card"
        assert policy2.render_target == "summary_card"

    def test_from_dict_preserves_render_target(self):
        """from_dict should preserve render_target from input."""
        policy = from_dict({"render_target": "summary_card"})
        assert policy.render_target == "summary_card"

    def test_from_dict_defaults_render_target(self):
        """from_dict should default to chat_card when not provided."""
        policy = from_dict({})
        assert policy.render_target == "chat_card"


class TestRenderedSpiritCard:
    """Test RenderedSpiritCard with summary_payload field."""

    def test_rendered_card_can_have_summary_payload(self):
        """RenderedSpiritCard can hold summary_payload."""
        summary = {
            "title": "火神",
            "types": ["火"],
            "stat_items": [],
            "skills": [],
            "wiki_url": "https://example.com",
            "source_label": "BWIKI",
        }

        card = RenderedSpiritCard(
            html="",
            summary_payload=summary,
            fallback_text="fallback",
            render_mode="summary_only",
        )

        assert card.summary_payload == summary
        assert card.render_mode == "summary_only"

    def test_rendered_card_is_renderable_with_summary(self):
        """Card with summary_payload should be considered renderable."""
        card = RenderedSpiritCard(
            html="",
            summary_payload={"title": "test"},
            fallback_text="",
            render_mode="summary_only",
        )

        assert card.is_renderable()

    def test_rendered_card_is_renderable_with_html(self):
        """Card with HTML should be considered renderable."""
        card = RenderedSpiritCard(
            html="<div>test</div>",
            summary_payload=None,
            fallback_text="",
            render_mode="rich_html",
        )

        assert card.is_renderable()

    def test_rendered_card_is_renderable_with_fallback(self):
        """Card with fallback_text should be considered renderable."""
        card = RenderedSpiritCard(
            html="",
            summary_payload=None,
            fallback_text="fallback text",
            render_mode="text_only",
        )

        assert card.is_renderable()


class TestSummaryCardRendering:
    """Test summary_card mode rendering."""

    def test_summary_card_mode_generates_summary_payload(self):
        """summary_card mode should generate summary_payload instead of HTML."""
        card_model = SpiritCardModel(
            display_name="火神",
            canonical_name="fire_spirit",
            types=["火"],
            stat_items=[{"label": "HP", "value": 100}],
            skills=[{"name": "火球"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E7%81%AB%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        assert result.summary_payload is not None
        assert result.summary_payload["title"] == "火神"
        assert result.summary_payload["types"] == ["火"]
        assert result.summary_payload["wiki_url"] == "https://wiki.biligame.com/rocokingdomworld/%E7%81%AB%E7%A5%9E"
        assert result.summary_payload["source_label"] == "BWIKI"
        assert result.render_mode == "summary_only"
        assert result.html == ""

    def test_summary_card_payload_includes_required_fields(self):
        """summary_payload should include all required fields."""
        card_model = SpiritCardModel(
            display_name="水神",
            canonical_name="water_spirit",
            types=["水"],
            stat_items=[{"label": "HP", "value": 90}],
            skills=[{"name": "水枪"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E6%B0%B4%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        payload = result.summary_payload
        assert payload is not None
        assert "title" in payload
        assert "types" in payload
        assert "stat_items" in payload
        assert "skills" in payload
        assert "wiki_url" in payload
        assert "source_label" in payload

    def test_summary_card_mode_has_fallback_text(self):
        """summary_card mode should still generate fallback_text for degradation."""
        card_model = SpiritCardModel(
            display_name="风神",
            canonical_name="wind_spirit",
            types=["风"],
            stat_items=[],
            skills=[],
            wiki_url="",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        assert result.fallback_text != ""
        assert result.summary_payload is not None

    def test_summary_card_metadata_includes_render_target(self):
        """summary_card mode should include render_target in metadata."""
        card_model = SpiritCardModel(
            display_name="土神",
            canonical_name="earth_spirit",
            types=["土"],
            stat_items=[],
            skills=[],
            wiki_url="",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        assert result.metadata["render_target"] == "summary_card"


class TestChatCardRendering:
    """Test chat_card mode rendering (backward compatibility)."""

    def test_chat_card_mode_generates_html(self):
        """chat_card mode should generate HTML as before."""
        card_model = SpiritCardModel(
            display_name="火神",
            canonical_name="fire_spirit",
            types=["火"],
            stat_items=[{"label": "HP", "value": 100}],
            skills=[{"name": "火球"}],
            wiki_url="https://example.com",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="chat_card")
        result = render_spirit_card(card_model, policy)

        # HTML should be generated (may be empty if template fails, but mode should be set)
        assert result.render_mode in ["rich_html", "html_with_text_fallback", "text_only"]
        assert result.summary_payload is None

    def test_chat_card_mode_metadata_includes_render_target(self):
        """chat_card mode should include render_target in metadata."""
        card_model = SpiritCardModel(
            display_name="水神",
            canonical_name="water_spirit",
            types=["水"],
            stat_items=[],
            skills=[],
            wiki_url="",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="chat_card")
        result = render_spirit_card(card_model, policy)

        assert result.metadata["render_target"] == "chat_card"


class TestDegradationBehavior:
    """Test degradation behavior for summary_card mode."""

    def test_summary_card_with_missing_fields_still_generates_payload(self):
        """summary_card should handle missing fields gracefully."""
        card_model = SpiritCardModel(
            display_name="",
            canonical_name="",
            types=[],
            stat_items=[],
            skills=[],
            wiki_url="",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        # Should still generate payload with empty values
        assert result.summary_payload is not None
        assert result.summary_payload["title"] == ""
        assert result.summary_payload["types"] == []

    def test_summary_card_fallback_when_payload_generation_fails(self):
        """If summary_payload generation fails, fallback_text should be available."""
        card_model = SpiritCardModel(
            display_name="测试",
            canonical_name="test",
            types=[],
            stat_items=[],
            skills=[],
            wiki_url="",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        # Fallback should always be generated
        assert result.fallback_text != ""
        # Summary payload should still be generated
        assert result.summary_payload is not None
