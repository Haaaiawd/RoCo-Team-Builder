"""
Integration tests for Card Rendering Contract and Degradation.

验证 T2.2.1: 卡片渲染契约测试与降级测试
对齐: spirit-card-system.md §11.3 契约测试, §11.2 集成测试
"""

import pytest

from src.spirit_card.app.contracts import (
    RenderPolicy,
    RenderedSpiritCard,
    SpiritCardModel,
)
from src.spirit_card.rendering.template_renderer import render_spirit_card


class TestRenderedSpiritCardContract:
    """Test RenderedSpiritCard contract compliance (§11.3)."""

    def test_rendered_card_contains_required_contract_fields(self):
        """RenderedSpiritCard must contain html, fallback_text, render_mode, metadata."""
        card_model = SpiritCardModel(
            display_name="火神",
            canonical_name="fire_spirit",
            types=["火"],
            stat_items=[{"label": "HP", "value": 100}],
            skills=[{"name": "火球"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E7%81%AB%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="chat_card")
        result = render_spirit_card(card_model, policy)

        # 契约字段必须完整
        assert hasattr(result, "html")
        assert hasattr(result, "fallback_text")
        assert hasattr(result, "render_mode")
        assert hasattr(result, "metadata")

        # 字段类型检查
        assert isinstance(result.html, str)
        assert isinstance(result.fallback_text, str)
        assert isinstance(result.render_mode, str)
        assert isinstance(result.metadata, dict)

    def test_rendered_card_summary_mode_contract(self):
        """Summary mode must include summary_payload in contract."""
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

        # summary_payload 应该存在
        assert hasattr(result, "summary_payload")
        assert result.summary_payload is not None
        assert isinstance(result.summary_payload, dict)

    def test_card_contains_essential_spirit_info(self):
        """Card must contain spirit name, types, stats, skills, BWIKI link."""
        card_model = SpiritCardModel(
            display_name="风神",
            canonical_name="wind_spirit",
            types=["风"],
            stat_items=[
                {"label": "HP", "value": 80},
                {"label": "攻击", "value": 70},
            ],
            skills=[{"name": "风刃"}, {"name": "狂风"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E9%A3%8E%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="chat_card")
        result = render_spirit_card(card_model, policy)

        # 检查 HTML 包含关键信息
        assert "风神" in result.html or "风神" in result.fallback_text
        assert "风" in result.html or "风" in result.fallback_text

        # 检查 fallback 包含种族值和技能
        assert "HP" in result.fallback_text or "80" in result.fallback_text
        assert "风刃" in result.fallback_text or "狂风" in result.fallback_text

        # 检查 wiki 链接
        assert "wiki.biligame.com" in result.fallback_text

    def test_wiki_url_presence_requires_source_label(self):
        """When wiki_url exists, source label and jump entry must not be missing."""
        card_model = SpiritCardModel(
            display_name="土神",
            canonical_name="earth_spirit",
            types=["土"],
            stat_items=[{"label": "HP", "value": 85}],
            skills=[{"name": "地裂"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E5%9C%9F%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="chat_card")
        result = render_spirit_card(card_model, policy)

        # HTML 或 fallback 应该包含来源标签
        assert "BWIKI" in result.html or "BWIKI" in result.fallback_text
        assert "wiki.biligame.com" in result.html or "wiki.biligame.com" in result.fallback_text

    def test_render_failure_must_not_return_double_empty(self):
        """Render failure must not return empty html AND empty fallback."""
        card_model = SpiritCardModel(
            display_name="光神",
            canonical_name="light_spirit",
            types=["光"],
            stat_items=[],
            skills=[],
            wiki_url="",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="chat_card")
        result = render_spirit_card(card_model, policy)

        # 至少 fallback 不应为空
        assert result.fallback_text != ""
        # 即使 HTML 为空，fallback 也应提供可读信息
        if result.html == "":
            assert "光神" in result.fallback_text


class TestCardHTMLStructure:
    """Test card HTML structure compliance (§11.3)."""

    def test_html_contains_identifiable_sections(self):
        """Card HTML must contain title, data, and source sections."""
        card_model = SpiritCardModel(
            display_name="暗神",
            canonical_name="dark_spirit",
            types=["暗"],
            stat_items=[{"label": "HP", "value": 95}],
            skills=[{"name": "暗影"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E6%9A%97%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="chat_card")
        result = render_spirit_card(card_model, policy)

        if result.html:
            # HTML 应该包含结构化标记（至少有标题和来源）
            # 由于我们使用 Jinja2 模板，检查是否包含关键内容
            assert "暗神" in result.html
            assert "BWIKI" in result.html or "wiki" in result.html.lower()


class TestDegradationBehavior:
    """Test degradation behavior (§11.2, §11.3)."""

    def test_html_render_failure_fallback_still_readable(self):
        """When HTML render fails, fallback text should still be readable."""
        card_model = SpiritCardModel(
            display_name="冰神",
            canonical_name="ice_spirit",
            types=["冰"],
            stat_items=[{"label": "HP", "value": 88}],
            skills=[{"name": "冰锥"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E5%86%B0%E7%A5%9E",
            source_label="BWIKI",
        )

        # 模拟图表禁用场景
        policy = RenderPolicy(
            render_target="chat_card",
            enable_chart_enhancement=False,
        )
        result = render_spirit_card(card_model, policy)

        # fallback 应该可读
        assert result.fallback_text != ""
        assert "冰神" in result.fallback_text
        assert "HP" in result.fallback_text or "88" in result.fallback_text

    def test_chart_disabled_preserves_numeric_stats(self):
        """When chart capability is disabled, card should still show 6-dim numeric stats."""
        card_model = SpiritCardModel(
            display_name="雷神",
            canonical_name="thunder_spirit",
            types=["雷"],
            stat_items=[
                {"label": "HP", "value": 92},
                {"label": "攻击", "value": 85},
                {"label": "防御", "value": 78},
                {"label": "魔攻", "value": 88},
                {"label": "魔抗", "value": 82},
                {"label": "速度", "value": 90},
            ],
            skills=[{"name": "雷击"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E9%9B%B7%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(
            render_target="chat_card",
            enable_chart_enhancement=False,
        )
        result = render_spirit_card(card_model, policy)

        # fallback 应该包含所有种族值
        assert "HP" in result.fallback_text
        assert "攻击" in result.fallback_text
        assert "防御" in result.fallback_text
        assert "魔攻" in result.fallback_text
        assert "魔抗" in result.fallback_text
        assert "速度" in result.fallback_text

    def test_missing_fields_still_produce_readable_card(self):
        """Missing fields should still produce readable card."""
        card_model = SpiritCardModel(
            display_name="幻神",
            canonical_name="illusion_spirit",
            types=[],
            stat_items=[],
            skills=[],
            wiki_url="",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="chat_card")
        result = render_spirit_card(card_model, policy)

        # 至少应该有名称
        assert "幻神" in result.fallback_text
        assert result.fallback_text != ""


class TestSummaryPayloadConsumability:
    """Test summary payload can be consumed by upstream host (§11.2)."""

    def test_summary_payload_is_consumable_dict(self):
        """Summary payload should be a consumable dict structure."""
        card_model = SpiritCardModel(
            display_name="龙神",
            canonical_name="dragon_spirit",
            types=["龙"],
            stat_items=[{"label": "HP", "value": 120}],
            skills=[{"name": "龙息"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E9%BE%99%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(render_target="summary_card")
        result = render_spirit_card(card_model, policy)

        # summary_payload 应该是可被上游直接消费的 dict
        payload = result.summary_payload
        assert isinstance(payload, dict)

        # 检查字段可访问
        assert "title" in payload
        assert "types" in payload
        assert "stat_items" in payload
        assert "skills" in payload
        assert "wiki_url" in payload

        # 检查字段值类型正确
        assert isinstance(payload["title"], str)
        assert isinstance(payload["types"], list)
        assert isinstance(payload["stat_items"], list)
        assert isinstance(payload["skills"], list)
        assert isinstance(payload["wiki_url"], str)

    def test_summary_payload_shared_semantics_with_chat_card(self):
        """Summary payload should share field semantics with chat card (§11.2)."""
        card_model = SpiritCardModel(
            display_name="凤神",
            canonical_name="phoenix_spirit",
            types=["火", "飞行"],
            stat_items=[{"label": "HP", "value": 110}],
            skills=[{"name": "涅槃"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E5%87%A4%E7%A5%9E",
            source_label="BWIKI",
        )

        # 生成 chat card 和 summary card
        chat_policy = RenderPolicy(render_target="chat_card")
        summary_policy = RenderPolicy(render_target="summary_card")

        chat_result = render_spirit_card(card_model, chat_policy)
        summary_result = render_spirit_card(card_model, summary_policy)

        # 字段语义应该一致（字段名相同）
        summary_payload = summary_result.summary_payload

        # 核心字段名应该与 SpiritCardModel 一致
        assert summary_payload["title"] == card_model.display_name
        assert summary_payload["types"] == card_model.types
        # 技能经过 sanitization，但核心语义一致
        assert len(summary_payload["skills"]) == len(card_model.skills)
        assert summary_payload["skills"][0]["name"] == card_model.skills[0]["name"]


class TestRenderModeMetadata:
    """Test render_mode and metadata accuracy."""

    def test_render_mode_reflects_actual_rendering(self):
        """render_mode should accurately reflect the actual rendering result."""
        card_model = SpiritCardModel(
            display_name="兽神",
            canonical_name="beast_spirit",
            types=["兽"],
            stat_items=[{"label": "HP", "value": 100}],
            skills=[{"name": "猛击"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E5%85%BD%E7%A5%9E",
            source_label="BWIKI",
        )

        # Chat card with HTML
        chat_policy = RenderPolicy(render_target="chat_card")
        chat_result = render_spirit_card(card_model, chat_policy)
        assert chat_result.render_mode in [
            "rich_html",
            "html_with_text_fallback",
            "text_only",
        ]

        # Summary card
        summary_policy = RenderPolicy(render_target="summary_card")
        summary_result = render_spirit_card(card_model, summary_policy)
        assert summary_result.render_mode == "summary_only"

    def test_metadata_includes_render_target(self):
        """Metadata should include render_target for tracking."""
        card_model = SpiritCardModel(
            display_name="灵神",
            canonical_name="spirit_spirit",
            types=["灵"],
            stat_items=[{"label": "HP", "value": 95}],
            skills=[{"name": "灵击"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E7%81%B5%E7%A5%9E",
            source_label="BWIKI",
        )

        chat_policy = RenderPolicy(render_target="chat_card")
        chat_result = render_spirit_card(card_model, chat_policy)

        assert "render_target" in chat_result.metadata
        assert chat_result.metadata["render_target"] == "chat_card"

        summary_policy = RenderPolicy(render_target="summary_card")
        summary_result = render_spirit_card(card_model, summary_policy)

        assert "render_target" in summary_result.metadata
        assert summary_result.metadata["render_target"] == "summary_card"

    def test_metadata_includes_chart_status(self):
        """Metadata should include chart_enabled status."""
        card_model = SpiritCardModel(
            display_name="星神",
            canonical_name="star_spirit",
            types=["星"],
            stat_items=[{"label": "HP", "value": 98}],
            skills=[{"name": "星光"}],
            wiki_url="https://wiki.biligame.com/rocokingdomworld/%E6%98%9F%E7%A5%9E",
            source_label="BWIKI",
        )

        policy = RenderPolicy(
            render_target="chat_card",
            enable_chart_enhancement=True,
        )
        result = render_spirit_card(card_model, policy)

        assert "chart_enabled" in result.metadata
        assert isinstance(result.metadata["chart_enabled"], bool)
