"""
Integration tests for Summary Card Mode field selection and degradation.

验证 T2.1.2: Summary Card Mode 展示字段、降级文本与 token 对齐
"""

import pytest

from src.spirit_card.app.contracts import (
    RenderPolicy,
    SpiritCardModel,
)
from src.spirit_card.rendering.template_renderer import render_spirit_card


class TestSummaryCardFields:
    """Test summary card mode returns minimal sufficient fields."""

    def test_summary_payload_contains_required_fields(self):
        """Summary payload should contain title, types, stats, skills, wiki link."""
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

        payload = result.summary_payload
        assert payload is not None
        assert "title" in payload
        assert "types" in payload
        assert "stat_items" in payload
        assert "skills" in payload
        assert "wiki_url" in payload
        assert "source_label" in payload

    def test_summary_payload_field_semantics_match_chat_card(self):
        """Summary payload should use same field names as chat card model."""
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

        # 字段名应与 SpiritCardModel 一致，不出现第二套命名
        assert payload["title"] == card_model.display_name
        assert payload["types"] == card_model.types
        assert payload["stat_items"] == card_model.stat_items
        # 技能经过 sanitization 会添加 type 和 description 字段，但核心语义一致
        assert len(payload["skills"]) == len(card_model.skills)
        assert payload["skills"][0]["name"] == card_model.skills[0]["name"]
        assert payload["wiki_url"] == card_model.wiki_url
        assert payload["source_label"] == card_model.source_label


class TestSummaryCardDegradation:
    """Test summary mode degradation behavior."""

    def test_summary_mode_with_chart_disabled_still_readable(self):
        """Summary mode should be readable even when chart enhancement is disabled."""
        card_model = SpiritCardModel(
            display_name="风神",
            canonical_name="wind_spirit",
            types=["风"],
            stat_items=[{"label": "HP", "value": 80}],
            skills=[{"name": "风刃"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E9%A3%8E%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(
            render_target="summary_card",
            enable_chart_enhancement=False,
        )
        result = render_spirit_card(card_model, policy)

        # summary_payload 应该仍然包含关键字段
        payload = result.summary_payload
        assert payload is not None
        assert payload["title"] == "风神"
        assert payload["types"] == ["风"]
        assert payload["stat_items"] == [{"label": "HP", "value": 80}]

    def test_summary_mode_fallback_text_always_generated(self):
        """Fallback text should always be generated for summary mode."""
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

        # fallback_text 应该始终存在
        assert result.fallback_text != ""
        assert "土神" in result.fallback_text

    def test_summary_mode_preserves_wiki_link_entry(self):
        """Wiki link entry should be preserved in summary mode."""
        card_model = SpiritCardModel(
            display_name="光神",
            canonical_name="light_spirit",
            types=["光"],
            stat_items=[],
            skills=[],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E5%85%89%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        # wiki_url 应该在 summary_payload 和 fallback_text 中都存在
        payload = result.summary_payload
        assert payload is not None
        assert payload["wiki_url"] == "https://wiki.biligame.com/rocokingdomworld/%E5%85%89%E7%A5%9E"
        assert "wiki.biligame.com" in result.fallback_text


class TestSummaryTokens:
    """Test summary mode visual tokens."""

    def test_summary_tokens_exist(self):
        """Summary mode should have dedicated visual tokens."""
        from src.spirit_card.assets.inline_tokens import SUMMARY_TOKENS, get_summary_token

        # 验证 summary token 字典存在
        assert SUMMARY_TOKENS is not None
        assert len(SUMMARY_TOKENS) > 0

        # 验证关键字段存在
        assert "summary_bg" in SUMMARY_TOKENS
        assert "summary_border" in SUMMARY_TOKENS
        assert "summary_title_color" in SUMMARY_TOKENS

        # 验证获取函数工作正常
        bg = get_summary_token("summary_bg")
        assert bg == "#FFFFFF"

    def test_summary_tokens_distinct_from_chat_card_tokens(self):
        """Summary tokens should be distinct from chat card theme tokens."""
        from src.spirit_card.assets.inline_tokens import SUMMARY_TOKENS, THEME_TOKENS

        # Summary tokens 应该是独立的字典
        assert SUMMARY_TOKENS is not THEME_TOKENS

        # Summary tokens 应该有不同的值（例如背景色）
        assert SUMMARY_TOKENS.get("summary_bg") != THEME_TOKENS.get("card_bg")


class TestSummaryRenderMode:
    """Test summary mode render mode metadata."""

    def test_summary_mode_sets_render_mode_correctly(self):
        """Summary mode should set render_mode to summary_only."""
        card_model = SpiritCardModel(
            display_name="暗神",
            canonical_name="dark_spirit",
            types=["暗"],
            stat_items=[],
            skills=[],
            wiki_url="",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        assert result.render_mode == "summary_only"
        assert result.html == ""
        assert result.summary_payload is not None

    def test_summary_mode_metadata_includes_render_target(self):
        """Summary mode metadata should include render_target."""
        card_model = SpiritCardModel(
            display_name="冰神",
            canonical_name="ice_spirit",
            types=["冰"],
            stat_items=[],
            skills=[],
            wiki_url="",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        assert result.metadata["render_target"] == "summary_card"
