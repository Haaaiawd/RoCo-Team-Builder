"""
内容清洗器 — 处理文本转义、链接协议和富文本限制。

对齐: spirit-card-system.md §4.2 Content Sanitizer
     spirit-card-system.detail.md §3.2 sanitize_spirit_content
     spirit-card-system.detail.md §1 SANITIZATION_POLICY

不允许原样注入不可信 HTML。链接必须白名单校验。
sanitization 层负责 HTML 转义，Jinja2 模板中对已转义字段使用 |safe 防止双重转义。
"""

from __future__ import annotations

from html import escape

from ..app.contracts import SpiritCardModel
from ..app.render_policy import SANITIZATION_POLICY


def sanitize_spirit_content(card_model: SpiritCardModel) -> SpiritCardModel:
    """清洗卡片视图模型中的所有文本字段。

    - 所有文本字段 HTML 转义（sanitization 层负责安全）
    - wiki_url 白名单校验 (仅允许 https://wiki.biligame.com/)
    - 技能描述截断到 max_skill_description_chars
    - Jinja2 模板需对已转义字段使用 |safe 过滤器，防止双重转义
    """
    safe_url = ""
    if card_model.wiki_url.startswith("https://wiki.biligame.com/"):
        safe_url = card_model.wiki_url

    max_desc = SANITIZATION_POLICY.get("max_skill_description_chars", 80)

    safe_skills = []
    for skill in card_model.skills:
        safe_skills.append(
            {
                "name": escape(str(skill.get("name", ""))),
                "type": escape(str(skill.get("type", ""))) if skill.get("type") else None,
                "description": escape(str(skill.get("description", "")))[:max_desc],
            }
        )

    return SpiritCardModel(
        display_name=escape(card_model.display_name),
        canonical_name=escape(card_model.canonical_name),
        types=[escape(str(item)) for item in card_model.types],
        stat_items=card_model.stat_items,
        skills=safe_skills,
        bloodline_type=escape(card_model.bloodline_type) if card_model.bloodline_type else None,
        evolution_chain=[
            {
                "stage_name": escape(str(node.get("stage_name", ""))),
                "condition": escape(str(node.get("condition", ""))) if node.get("condition") else None,
                "branch_label": escape(str(node.get("branch_label", ""))) if node.get("branch_label") else None,
            }
            for node in card_model.evolution_chain
        ],
        wiki_url=safe_url,
        source_label=escape(card_model.source_label),
    )
