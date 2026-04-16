"""
Spirit-Card 适配器 — 将 SpiritCardFacade 包装为 ISpiritCardClient 协议。

职责：
- 将 spirit-card-system 的渲染器包装为 agent-backend 的接口
- 统一错误处理，渲染失败时返回带 fallback_text 的降级信息
- 确保 RenderedSpiritCard 的 html/fallback_text/render_mode/metadata 结构完整

对齐: agent-backend-system.md §5.2 ISpiritCardClient
"""

from __future__ import annotations

from typing import Protocol

from spirit_card.app.facade import SpiritCardFacade


class ISpiritCardClient(Protocol):
    """精灵卡片渲染客户端协议 — agent-backend 对 spirit-card 的抽象接口。"""

    async def render_spirit_card(self, spirit_payload: dict, policy: dict | None = None) -> dict:
        """渲染精灵卡片。

        Returns:
            {
                "success": bool,
                "html": str | None,
                "fallback_text": str,
                "render_mode": str,
                "metadata": dict,
                "error_message": str | None,
            }
        """
        ...


class SpiritCardClient:
    """SpiritCardFacade 的适配器 — 实现 ISpiritCardClient 协议。"""

    def __init__(self, facade: SpiritCardFacade) -> None:
        self._facade = facade

    async def render_spirit_card(self, spirit_payload: dict, policy: dict | None = None) -> dict:
        """渲染精灵卡片。

        失败时返回带 fallback_text 的降级信息，不泄漏内部异常堆栈。
        """
        try:
            rendered = self._facade.render_spirit_card(spirit_payload, policy=policy)
            return {
                "success": True,
                "html": rendered.html,
                "fallback_text": rendered.fallback_text,
                "render_mode": rendered.render_mode,
                "metadata": rendered.metadata,
                "error_message": None,
            }
        except Exception:
            # 渲染失败时，构建最小 fallback
            if isinstance(spirit_payload, dict):
                display_name = spirit_payload.get("display_name", spirit_payload.get("canonical_name", "未知精灵"))
            else:
                display_name = getattr(spirit_payload, "display_name", getattr(spirit_payload, "canonical_name", "未知精灵"))
            fallback = f"[卡片渲染失败] {display_name} - 资料查询成功但卡片生成异常"
            return {
                "success": False,
                "html": None,
                "fallback_text": fallback,
                "render_mode": "text_only",
                "metadata": {},
                "error_message": "卡片渲染失败",
            }
