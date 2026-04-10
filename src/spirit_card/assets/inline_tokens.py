"""
卡片设计 Token — 管理卡片色票、圆角、纹理与分区样式。

对齐: spirit-card-system.detail.md §5.2 Card Visual Reference
与 web-ui-system 视觉同源: roco_adventure_journal 主题。
"""

from __future__ import annotations

THEME_TOKENS: dict[str, str] = {
    # 表面
    "card_bg": "#F9F8F4",
    "card_border": "rgba(51, 51, 51, 0.10)",
    "card_shadow": "0 10px 30px rgba(45, 44, 42, 0.10)",
    "card_radius": "20px",
    # 文字
    "text_main": "#333333",
    "text_muted": "#999999",
    # 强调
    "accent_gold": "#F3C969",
    "accent_gold_bg": "rgba(243, 201, 105, 0.18)",
    # 技能标签
    "skill_tag_border": "rgba(51, 51, 51, 0.28)",
    "skill_tag_radius": "9999px",
    # 分区
    "section_divider": "rgba(51, 51, 51, 0.15)",
}


def get_token(key: str, fallback: str = "") -> str:
    """获取设计 token 值。"""
    return THEME_TOKENS.get(key, fallback)
