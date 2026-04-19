"""
spirit-card-system 核心契约定义

包含卡片系统的领域数据类和 Service 协议。
agent-backend-system 只依赖此文件中的类型定义，不依赖具体实现。

数据类定义对齐: spirit-card-system.md §6.1 Core Entities
协议定义对齐: spirit-card-system.md §5.2 Cross-System Interface
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


# ---------------------------------------------------------------------------
# 6.1 Core Entities
# ---------------------------------------------------------------------------


@dataclass
class SpiritCardModel:
    """精灵卡片视图模型 — 展示层领域对象。

    从 SpiritProfile 显式映射而来，不等同于数据层原始结构。
    """

    display_name: str
    canonical_name: str
    types: list[str]
    stat_items: list[dict] = field(default_factory=list)
    skills: list[dict] = field(default_factory=list)
    bloodline_type: str | None = None
    evolution_chain: list[dict] = field(default_factory=list)
    wiki_url: str = ""
    source_label: str = "BWIKI"

    def has_chartable_stats(self) -> bool:
        """是否有可用于图表渲染的种族值。"""
        return any(item.get("value") is not None for item in self.stat_items)


@dataclass
class RenderPolicy:
    """渲染策略 — 控制卡片增强/降级行为。

    agent-backend-system 可基于宿主条件动态调整。
    v3 新增 render_target 字段支持 chat_card / summary_card 双模式。
    v2 默认值锁定 'roco_adventure_journal' 主题。
    """

    render_target: Literal["chat_card", "summary_card"] = "chat_card"
    enable_chart_enhancement: bool = True
    max_visible_skills: int = 8
    allow_external_assets: bool = False
    prefer_compact_layout: bool = True
    theme_name: str = "roco_adventure_journal"


@dataclass
class RenderedSpiritCard:
    """渲染产物包 — HTML + summary_payload + 降级文本 + 元数据。

    不是单一 HTML 字符串，便于上游在失败时仍保住可读性。
    v3 新增 summary_payload 字段用于工作台摘要模式。
    """

    html: str
    summary_payload: dict | None = None
    fallback_text: str = ""
    render_mode: Literal["rich_html", "html_with_text_fallback", "text_only", "summary_only"] = "rich_html"
    metadata: dict = field(default_factory=dict)

    def is_renderable(self) -> bool:
        """是否有可展示的内容。"""
        return bool(self.html or self.summary_payload or self.fallback_text)


# ---------------------------------------------------------------------------
# 5.2 Cross-System Interface Protocol
# ---------------------------------------------------------------------------


class ISpiritCardService(Protocol):
    """精灵卡片服务对外统一契约 — agent-backend-system 入口。"""

    def build_spirit_card_model(
        self, profile: dict, options: dict | None = None
    ) -> SpiritCardModel:
        """将 SpiritProfile 转换为卡片视图模型。"""
        ...

    def render_spirit_card(
        self, profile: dict, policy: dict | None = None
    ) -> RenderedSpiritCard:
        """一站式渲染: profile → 卡片产物包。"""
        ...
