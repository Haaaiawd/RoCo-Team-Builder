"""
文本降级构建器 — 为 Rich UI 失败时提供最小充分信息。

对齐: spirit-card-system.detail.md §3.5 build_fallback_text

fallback 不是"第二份完整卡片"，而是用户在富展示失败时仍能继续决策的最小充分信息。
"""

from __future__ import annotations

from ..app.contracts import SpiritCardModel


def build_fallback_text(card_model: SpiritCardModel) -> str:
    """构建文本降级摘要。"""
    type_text = " / ".join(card_model.types) if card_model.types else "未知系别"
    stat_lines = [
        f"{item['label']}:{item['value']}"
        for item in card_model.stat_items
        if item.get("value") is not None
    ]
    skill_names = [
        skill.get("name") for skill in card_model.skills if skill.get("name")
    ]

    lines = [
        f"精灵：{card_model.display_name}",
        f"系别：{type_text}",
        f"种族值：{'，'.join(stat_lines) if stat_lines else '暂无'}",
    ]

    if card_model.bloodline_type:
        lines.append(f"血脉：{card_model.bloodline_type}")
    if skill_names:
        lines.append(f"技能：{'、'.join(skill_names)}")
    if card_model.wiki_url:
        lines.append(f"BWIKI：{card_model.wiki_url}")

    return "\n".join(lines)
