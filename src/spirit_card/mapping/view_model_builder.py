"""
视图模型构建器 — SpiritProfile → SpiritCardModel 映射。

对齐: spirit-card-system.detail.md §3.1 build_spirit_card_model
展示字段必须从结构化 profile 显式映射，不能在模板里到处访问原始 profile。
"""

from __future__ import annotations

from ..app.contracts import SpiritCardModel
from ..app.render_policy import CARD_RENDER_POLICY


def build_spirit_card_model(
    profile: dict, options: dict | None = None
) -> SpiritCardModel:
    """将 SpiritProfile dict 映射为 SpiritCardModel。

    Args:
        profile: data-layer-system 返回的精灵资料 dict
        options: 可选覆盖 (max_visible_skills, source_label)

    Returns:
        展示友好的 SpiritCardModel
    """
    options = options or {}

    stat_items = [
        {"label": "HP", "value": profile.get("base_stats", {}).get("hp")},
        {"label": "攻击", "value": profile.get("base_stats", {}).get("attack")},
        {"label": "防御", "value": profile.get("base_stats", {}).get("defense")},
        {"label": "魔攻", "value": profile.get("base_stats", {}).get("magic_attack")},
        {"label": "魔抗", "value": profile.get("base_stats", {}).get("magic_defense")},
        {"label": "速度", "value": profile.get("base_stats", {}).get("speed")},
    ]

    max_skills = options.get(
        "max_visible_skills", CARD_RENDER_POLICY["max_visible_skills"]
    )

    return SpiritCardModel(
        display_name=profile.get("display_name")
        or profile.get("canonical_name")
        or "未知精灵",
        canonical_name=profile.get("canonical_name", ""),
        types=profile.get("types", []),
        stat_items=stat_items,
        skills=(profile.get("skills") or [])[:max_skills],
        bloodline_type=profile.get("bloodline_type"),
        evolution_chain=profile.get("evolution_chain", []),
        wiki_url=profile.get("wiki_url", ""),
        source_label=options.get("source_label", "BWIKI"),
    )
