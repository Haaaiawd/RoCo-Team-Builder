"""
Jinja2 模板渲染器 — 生成精灵卡片 HTML。

对齐: spirit-card-system.md §4.2 HTML Template Renderer
     spirit-card-system.detail.md §3.3 render_spirit_card
     spirit-card-system.detail.md §3.4 render_stats_visual

不依赖远程资源。模板内联所有样式。
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..app.contracts import RenderPolicy, RenderedSpiritCard, SpiritCardModel
from ..app.render_policy import CHART_POLICY
from .sanitization import sanitize_spirit_content
from .fallback_builder import build_fallback_text


_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def _create_jinja_env() -> Environment:
    """创建 Jinja2 环境 — autoescape 开启，防止双重转义需注意。"""
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


_env = _create_jinja_env()


def render_stats_visual(card_model: SpiritCardModel, sandbox_caps: dict) -> dict:
    """生成种族值展示数据。

    对齐: spirit-card-system.detail.md §3.4
    图表模式只是增强层；数值网格必须始终可用。
    """
    if not card_model.has_chartable_stats():
        return {
            "mode": "empty",
            "items": card_model.stat_items,
        }

    if sandbox_caps.get("script_runtime") and CHART_POLICY["enabled_by_default"]:
        return {
            "mode": "chart",
            "labels": [item["label"] for item in card_model.stat_items],
            "values": [item["value"] for item in card_model.stat_items],
        }

    return {
        "mode": CHART_POLICY["fallback_mode"],
        "items": card_model.stat_items,
    }


def render_spirit_card(
    card_model: SpiritCardModel,
    policy: RenderPolicy,
) -> RenderedSpiritCard:
    """一站式卡片渲染: 清洗 → 统计块 → fallback → HTML。

    对齐: spirit-card-system.detail.md §3.3
    fallback 文本在 HTML 生成之前就准备好，不是"失败再补救"。
    """
    safe_model = sanitize_spirit_content(card_model)
    stat_block = render_stats_visual(
        safe_model,
        {"script_runtime": policy.enable_chart_enhancement},
    )
    fallback_text = build_fallback_text(safe_model)

    try:
        template = _env.get_template("spirit_card.html")
        html = template.render(
            card=safe_model,
            stat_block=stat_block,
            policy=policy,
        )
    except Exception:
        html = ""

    render_mode: str
    if html and fallback_text:
        render_mode = "html_with_text_fallback"
    elif html:
        render_mode = "rich_html"
    else:
        render_mode = "text_only"

    return RenderedSpiritCard(
        html=html,
        fallback_text=fallback_text,
        render_mode=render_mode,
        metadata={
            "chart_enabled": stat_block.get("mode") == "chart",
            "has_wiki_link": bool(safe_model.wiki_url),
        },
    )
