"""
T2.2.1 测试 — 卡片模板、内容清洗与文本降级。

验收标准:
  - Given 完整 SpiritProfile → 返回包含名称/系别/种族值/技能/进化链/BWIKI 来源的 HTML 卡片
  - Given Rich UI 不支持脚本或渲染失败 → 返回非空 fallback_text
  - Given 输入含潜在危险文本或链接 → 不透传不可信 HTML 与危险协议
"""

from __future__ import annotations


from spirit_card.app.contracts import RenderedSpiritCard
from spirit_card.app.facade import SpiritCardFacade
from spirit_card.app.render_policy import default_policy
from spirit_card.mapping.view_model_builder import build_spirit_card_model
from spirit_card.rendering.sanitization import sanitize_spirit_content
from spirit_card.rendering.fallback_builder import build_fallback_text
from spirit_card.rendering.template_renderer import render_spirit_card, render_stats_visual


MOCK_PROFILE: dict = {
    "canonical_name": "火神",
    "display_name": "火神",
    "types": ["火"],
    "base_stats": {
        "hp": 85,
        "attack": 90,
        "defense": 75,
        "magic_attack": 120,
        "magic_defense": 80,
        "speed": 95,
    },
    "skills": [
        {"name": "烈焰冲击", "type": "火", "description": "释放高温火焰攻击对手"},
        {"name": "火焰旋涡", "type": "火"},
        {"name": "灭世火焰", "type": "火"},
        {"name": "凤凰涅槃", "type": "火"},
    ],
    "bloodline_type": "神火",
    "evolution_chain": [
        {"stage_name": "火花", "condition": "等级进化"},
        {"stage_name": "焰火", "condition": "等级进化"},
        {"stage_name": "火神"},
    ],
    "wiki_url": "https://wiki.biligame.com/rocokingdomworld/%E7%81%AB%E7%A5%9E",
}


XSS_PROFILE: dict = {
    "canonical_name": '<script>alert("xss")</script>',
    "display_name": '<img src=x onerror="alert(1)">',
    "types": ['<b>fire</b>'],
    "base_stats": {"hp": 100},
    "skills": [{"name": '<a href="javascript:void(0)">hack</a>', "type": "fire"}],
    "bloodline_type": '<svg onload="alert(1)">',
    "evolution_chain": [{"stage_name": '<script>alert("evo")</script>', "condition": "level"}],
    "wiki_url": "javascript:alert(1)",
}


# ---------------------------------------------------------------------------
# 内容清洗
# ---------------------------------------------------------------------------


class TestSanitization:
    def test_xss_in_display_name(self):
        """危险标签被转义。"""
        model = build_spirit_card_model(XSS_PROFILE)
        safe = sanitize_spirit_content(model)
        assert "<script>" not in safe.display_name
        assert "<img" not in safe.display_name
        assert "&lt;" in safe.display_name

    def test_xss_in_types(self):
        model = build_spirit_card_model(XSS_PROFILE)
        safe = sanitize_spirit_content(model)
        assert "<b>" not in safe.types[0]

    def test_xss_in_skills(self):
        model = build_spirit_card_model(XSS_PROFILE)
        safe = sanitize_spirit_content(model)
        assert "<a " not in safe.skills[0]["name"]

    def test_xss_in_bloodline(self):
        model = build_spirit_card_model(XSS_PROFILE)
        safe = sanitize_spirit_content(model)
        assert "<svg" not in safe.bloodline_type

    def test_xss_in_evolution(self):
        model = build_spirit_card_model(XSS_PROFILE)
        safe = sanitize_spirit_content(model)
        assert "<script>" not in safe.evolution_chain[0]["stage_name"]

    def test_dangerous_url_removed(self):
        """非白名单 URL 被清空。"""
        model = build_spirit_card_model(XSS_PROFILE)
        safe = sanitize_spirit_content(model)
        assert safe.wiki_url == ""

    def test_safe_url_preserved(self):
        """白名单 URL 保留。"""
        model = build_spirit_card_model(MOCK_PROFILE)
        safe = sanitize_spirit_content(model)
        assert safe.wiki_url.startswith("https://wiki.biligame.com/")

    def test_skill_description_truncation(self):
        """技能描述超过 80 字符被截断。"""
        long_desc_profile = {
            **MOCK_PROFILE,
            "skills": [{"name": "test", "description": "x" * 200}],
        }
        model = build_spirit_card_model(long_desc_profile)
        safe = sanitize_spirit_content(model)
        assert len(safe.skills[0]["description"]) <= 80


# ---------------------------------------------------------------------------
# 文本降级
# ---------------------------------------------------------------------------


class TestFallbackBuilder:
    def test_contains_key_info(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        text = build_fallback_text(model)
        assert "火神" in text
        assert "火" in text
        assert "HP:85" in text
        assert "神火" in text
        assert "烈焰冲击" in text
        assert "wiki.biligame.com" in text

    def test_empty_profile_fallback(self):
        model = build_spirit_card_model({})
        text = build_fallback_text(model)
        assert "未知精灵" in text
        assert "未知系别" in text
        assert "暂无" in text

    def test_no_bloodline(self):
        profile = {**MOCK_PROFILE}
        del profile["bloodline_type"]
        model = build_spirit_card_model(profile)
        text = build_fallback_text(model)
        assert "血脉" not in text


# ---------------------------------------------------------------------------
# 种族值可视化模式
# ---------------------------------------------------------------------------


class TestRenderStatsVisual:
    def test_chart_mode_when_script_enabled(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_stats_visual(model, {"script_runtime": True})
        assert result["mode"] == "chart"
        assert len(result["labels"]) == 6

    def test_grid_mode_when_script_disabled(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_stats_visual(model, {"script_runtime": False})
        assert result["mode"] == "numeric_stat_grid"

    def test_empty_mode_no_stats(self):
        model = build_spirit_card_model({})
        result = render_stats_visual(model, {"script_runtime": True})
        assert result["mode"] == "empty"


# ---------------------------------------------------------------------------
# 完整渲染管线
# ---------------------------------------------------------------------------


class TestRenderSpiritCard:
    def test_full_render_produces_html(self):
        """完整渲染产出非空 HTML。"""
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert isinstance(result, RenderedSpiritCard)
        assert result.html
        assert "spirit-card" in result.html

    def test_html_contains_display_name(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert "火神" in result.html

    def test_html_contains_stats(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert "85" in result.html
        assert "120" in result.html

    def test_html_contains_skills(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert "烈焰冲击" in result.html

    def test_html_contains_evolution(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert "火花" in result.html

    def test_html_contains_source(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert "wiki.biligame.com" in result.html

    def test_render_mode_is_html_with_fallback(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert result.render_mode == "html_with_text_fallback"

    def test_fallback_still_present(self):
        """HTML 和 fallback 同时产出。"""
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert result.fallback_text
        assert "火神" in result.fallback_text

    def test_xss_not_in_html(self):
        """XSS 标签不出现在最终 HTML 中。"""
        model = build_spirit_card_model(XSS_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert "<script>" not in result.html
        assert 'href="javascript:' not in result.html
        assert "<img " not in result.html
        assert "<svg " not in result.html

    def test_metadata_fields(self):
        model = build_spirit_card_model(MOCK_PROFILE)
        result = render_spirit_card(model, default_policy())
        assert "chart_enabled" in result.metadata
        assert "has_wiki_link" in result.metadata


# ---------------------------------------------------------------------------
# Facade 集成
# ---------------------------------------------------------------------------


class TestFacadeFullRender:
    def test_facade_produces_html(self):
        facade = SpiritCardFacade()
        result = facade.render_spirit_card(MOCK_PROFILE)
        assert isinstance(result, RenderedSpiritCard)
        assert result.html
        assert result.fallback_text
        assert result.render_mode == "html_with_text_fallback"

    def test_facade_xss_safe(self):
        facade = SpiritCardFacade()
        result = facade.render_spirit_card(XSS_PROFILE)
        assert "<script>" not in result.html
        assert 'href="javascript:' not in result.html
        assert "<img " not in result.html
