"""
T2.1.1 单元测试 — 精灵卡片渲染骨架与视图模型。

验收标准:
  - Given 已有 SpiritProfile → SpiritCardModel 与 RenderedSpiritCard 契约可实例化
  - Given 模板与 facade 已建立 → 导入不出现缺失模板或循环依赖错误
  - agent-backend-system 可按协议消费 html/fallback_text/render_mode/metadata
"""

from __future__ import annotations

from pathlib import Path

import pytest

from spirit_card.app.contracts import (
    ISpiritCardService,
    RenderedSpiritCard,
    RenderPolicy,
    SpiritCardModel,
)
from spirit_card.app.facade import SpiritCardFacade
from spirit_card.app import render_policy as rp
from spirit_card.mapping.view_model_builder import build_spirit_card_model
from spirit_card.assets.inline_tokens import THEME_TOKENS, get_token


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
        {"name": "烈焰冲击", "type": "火"},
        {"name": "火焰旋涡", "type": "火"},
        {"name": "灭世火焰", "type": "火"},
        {"name": "凤凰涅槃", "type": "火"},
    ],
    "bloodline_type": "神火",
    "evolution_chain": [{"stage_name": "火花", "condition": "等级进化"}],
    "wiki_url": "https://wiki.biligame.com/rocokingdomworld/%E7%81%AB%E7%A5%9E",
}


# ---------------------------------------------------------------------------
# 模块导入与循环依赖检查
# ---------------------------------------------------------------------------


class TestModuleImports:
    def test_contracts_importable(self):
        """核心契约类可正常导入。"""
        assert SpiritCardModel is not None
        assert RenderPolicy is not None
        assert RenderedSpiritCard is not None
        assert ISpiritCardService is not None

    def test_facade_importable(self):
        """Facade 可正常导入且实例化。"""
        facade = SpiritCardFacade()
        assert facade is not None

    def test_facade_satisfies_protocol(self):
        """Facade 满足 ISpiritCardService 协议。"""
        facade: ISpiritCardService = SpiritCardFacade()
        assert hasattr(facade, "build_spirit_card_model")
        assert hasattr(facade, "render_spirit_card")

    def test_template_exists(self):
        """Jinja2 模板文件存在且可读。"""
        tpl_dir = Path(__file__).resolve().parent.parent.parent / "src" / "spirit_card" / "rendering" / "templates"
        spirit_card_html = tpl_dir / "spirit_card.html"
        assert spirit_card_html.exists()
        content = spirit_card_html.read_text(encoding="utf-8")
        assert "spirit-card" in content


# ---------------------------------------------------------------------------
# SpiritCardModel 视图模型
# ---------------------------------------------------------------------------


class TestBuildSpiritCardModel:
    def test_basic_mapping(self):
        """profile 正确映射为 SpiritCardModel。"""
        model = build_spirit_card_model(MOCK_PROFILE)
        assert isinstance(model, SpiritCardModel)
        assert model.display_name == "火神"
        assert model.canonical_name == "火神"
        assert model.types == ["火"]
        assert model.bloodline_type == "神火"
        assert model.wiki_url
        assert model.source_label == "BWIKI"

    def test_stat_items_mapping(self):
        """种族值正确映射为 6 项 stat_items。"""
        model = build_spirit_card_model(MOCK_PROFILE)
        assert len(model.stat_items) == 6
        labels = {item["label"] for item in model.stat_items}
        assert labels == {"HP", "攻击", "防御", "魔攻", "魔抗", "速度"}
        hp_item = next(i for i in model.stat_items if i["label"] == "HP")
        assert hp_item["value"] == 85

    def test_has_chartable_stats(self):
        """有种族值时 has_chartable_stats 为 True。"""
        model = build_spirit_card_model(MOCK_PROFILE)
        assert model.has_chartable_stats() is True

    def test_empty_stats(self):
        """缺少种族值时 has_chartable_stats 为 False。"""
        model = build_spirit_card_model({"canonical_name": "测试", "display_name": "测试"})
        assert model.has_chartable_stats() is False

    def test_skills_truncation(self):
        """技能数超出限制时应截断。"""
        profile = {**MOCK_PROFILE, "skills": [{"name": f"技能{i}"} for i in range(20)]}
        model = build_spirit_card_model(profile, {"max_visible_skills": 3})
        assert len(model.skills) == 3

    def test_missing_display_name_fallback(self):
        """display_name 缺失时回退到 canonical_name。"""
        model = build_spirit_card_model({"canonical_name": "冰龙王"})
        assert model.display_name == "冰龙王"

    def test_completely_empty_profile(self):
        """完全空 profile 不崩溃，返回默认值。"""
        model = build_spirit_card_model({})
        assert model.display_name == "未知精灵"
        assert model.types == []


# ---------------------------------------------------------------------------
# RenderPolicy
# ---------------------------------------------------------------------------


class TestRenderPolicy:
    def test_default_policy(self):
        policy = rp.default_policy()
        assert isinstance(policy, RenderPolicy)
        assert policy.theme_name == "roco_adventure_journal"
        assert policy.allow_external_assets is False

    def test_from_dict_partial(self):
        policy = rp.from_dict({"max_visible_skills": 4})
        assert policy.max_visible_skills == 4
        assert policy.theme_name == "roco_adventure_journal"

    def test_from_dict_none(self):
        policy = rp.from_dict(None)
        assert policy == rp.default_policy()


# ---------------------------------------------------------------------------
# Facade 骨架 — render_spirit_card
# ---------------------------------------------------------------------------


class TestFacadeRender:
    def test_render_returns_rendered_card(self):
        """Facade 返回 RenderedSpiritCard 包含所有必要字段。"""
        facade = SpiritCardFacade()
        result = facade.render_spirit_card(MOCK_PROFILE)
        assert isinstance(result, RenderedSpiritCard)
        assert result.render_mode in ("rich_html", "html_with_text_fallback", "text_only")
        assert result.fallback_text
        assert "火神" in result.fallback_text
        assert isinstance(result.metadata, dict)

    def test_fallback_contains_key_info(self):
        """降级文本包含精灵核心信息。"""
        facade = SpiritCardFacade()
        result = facade.render_spirit_card(MOCK_PROFILE)
        assert "火神" in result.fallback_text
        assert "火" in result.fallback_text
        assert "HP:85" in result.fallback_text
        assert "神火" in result.fallback_text
        assert "烈焰冲击" in result.fallback_text
        assert "wiki.biligame.com" in result.fallback_text

    def test_is_renderable(self):
        """结果必须可展示。"""
        facade = SpiritCardFacade()
        result = facade.render_spirit_card(MOCK_PROFILE)
        assert result.is_renderable() is True

    def test_metadata_fields(self):
        """metadata 包含 chart_enabled 和 has_wiki_link。"""
        facade = SpiritCardFacade()
        result = facade.render_spirit_card(MOCK_PROFILE)
        assert "chart_enabled" in result.metadata
        assert "has_wiki_link" in result.metadata
        assert result.metadata["has_wiki_link"] is True


# ---------------------------------------------------------------------------
# Theme Tokens
# ---------------------------------------------------------------------------


class TestThemeTokens:
    def test_token_keys_exist(self):
        assert "card_bg" in THEME_TOKENS
        assert "accent_gold" in THEME_TOKENS

    def test_get_token_with_fallback(self):
        assert get_token("card_bg") == "#F9F8F4"
        assert get_token("nonexistent", "default") == "default"
