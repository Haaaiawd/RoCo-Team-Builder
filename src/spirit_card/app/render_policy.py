"""
渲染策略工厂 — 提供默认策略与策略构建方法。

对齐: spirit-card-system.detail.md §1 CARD_RENDER_POLICY
"""

from __future__ import annotations

from .contracts import RenderPolicy

CARD_RENDER_POLICY = {
    "max_visible_skills": 8,
    "max_skill_description_chars": 80,
    "max_evolution_nodes": 12,
    "prefer_compact_layout": True,
}

SANITIZATION_POLICY = {
    "allowed_link_hosts": ["wiki.biligame.com"],
    "allowed_link_schemes": ["https"],
    "escape_all_text_fields": True,
    "max_skill_description_chars": 80,
}

CHART_POLICY = {
    "enabled_by_default": True,
    "requires_script_runtime": True,
    "fallback_mode": "numeric_stat_grid",
}

CARD_THEME_TOKENS = {
    "theme_name": "roco_adventure_journal",
    "card_bg": "#F9F8F4",
    "card_border": "rgba(51, 51, 51, 0.10)",
    "card_title_accent": "#F3C969",
    "card_text": "#333333",
}


def default_policy() -> RenderPolicy:
    """返回 v2 默认渲染策略。"""
    return RenderPolicy(
        enable_chart_enhancement=CHART_POLICY["enabled_by_default"],
        max_visible_skills=CARD_RENDER_POLICY["max_visible_skills"],
        allow_external_assets=False,
        prefer_compact_layout=CARD_RENDER_POLICY["prefer_compact_layout"],
        theme_name=CARD_THEME_TOKENS["theme_name"],
    )


def from_dict(data: dict | None) -> RenderPolicy:
    """从 dict 构建 RenderPolicy，缺失字段用默认值。"""
    if not data:
        return default_policy()

    base = default_policy()
    return RenderPolicy(
        enable_chart_enhancement=data.get(
            "enable_chart_enhancement", base.enable_chart_enhancement
        ),
        max_visible_skills=data.get("max_visible_skills", base.max_visible_skills),
        allow_external_assets=data.get(
            "allow_external_assets", base.allow_external_assets
        ),
        prefer_compact_layout=data.get(
            "prefer_compact_layout", base.prefer_compact_layout
        ),
        theme_name=data.get("theme_name", base.theme_name),
    )
