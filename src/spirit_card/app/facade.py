"""
spirit-card-system 统一 Facade

agent-backend-system 的唯一卡片渲染入口。
实现 ISpiritCardService 协议。

对齐: spirit-card-system.md §4.2 Spirit Card Facade、§5.1 操作契约表
"""

from __future__ import annotations

from .contracts import (
    ISpiritCardService,
    RenderedSpiritCard,
    SpiritCardModel,
)
from . import render_policy as rp
from ..mapping.view_model_builder import build_spirit_card_model


class SpiritCardFacade:
    """精灵卡片 Facade — T2.1.1 骨架。

    当前已接通:
    - build_spirit_card_model: profile → view model
    - render_spirit_card: 占位骨架 (T2.2.1 will implement full rendering)
    """

    def build_spirit_card_model(
        self, profile: dict, options: dict | None = None
    ) -> SpiritCardModel:
        """将 SpiritProfile 转换为卡片视图模型。"""
        return build_spirit_card_model(profile, options)

    def render_spirit_card(
        self, profile: dict, policy: dict | None = None
    ) -> RenderedSpiritCard:
        """一站式渲染入口 — 当前返回文本降级，T2.2.1 接入模板渲染。"""
        card_model = build_spirit_card_model(profile)
        render_p = rp.from_dict(policy)

        fallback_text = self._build_fallback_text(card_model)

        return RenderedSpiritCard(
            html="",
            fallback_text=fallback_text,
            render_mode="text_only",
            metadata={
                "chart_enabled": False,
                "has_wiki_link": bool(card_model.wiki_url),
                "policy_theme": render_p.theme_name,
            },
        )

    @staticmethod
    def _build_fallback_text(card_model: SpiritCardModel) -> str:
        """构建文本降级摘要。

        对齐: spirit-card-system.detail.md §3.5
        """
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


# 类型断言: SpiritCardFacade 满足 ISpiritCardService 协议
def _assert_protocol_compliance() -> None:
    facade: ISpiritCardService = SpiritCardFacade()  # noqa: F841
