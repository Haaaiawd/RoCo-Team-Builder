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
from ..rendering.template_renderer import render_spirit_card as _render


class SpiritCardFacade:
    """精灵卡片 Facade — 完整渲染管线。

    已接通:
    - build_spirit_card_model: profile → view model
    - render_spirit_card: profile → 清洗 → 模板渲染 → RenderedSpiritCard
    """

    def build_spirit_card_model(
        self, profile: dict, options: dict | None = None
    ) -> SpiritCardModel:
        """将 SpiritProfile 转换为卡片视图模型。"""
        return build_spirit_card_model(profile, options)

    def render_spirit_card(
        self, profile: dict, policy: dict | None = None
    ) -> RenderedSpiritCard:
        """一站式渲染: profile → 清洗 → fallback + HTML → 产物包。"""
        card_model = build_spirit_card_model(profile)
        render_p = rp.from_dict(policy)
        return _render(card_model, render_p)


# 类型断言: SpiritCardFacade 满足 ISpiritCardService 协议
def _assert_protocol_compliance() -> None:
    facade: ISpiritCardService = SpiritCardFacade()  # noqa: F841
