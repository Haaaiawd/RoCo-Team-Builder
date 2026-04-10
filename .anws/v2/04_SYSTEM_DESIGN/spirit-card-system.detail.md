# spirit-card-system — 实现细节 (L1)

> **文件性质**: L1 实现层 · **对应 L0**: [`spirit-card-system.md`](./spirit-card-system.md)
> 本文件仅在 `/forge` 任务明确引用时加载。日常阅读和任务规划请优先看 L0。
> **⚠️ 孤岛检查**: 本文件各节均须在 L0 有对应超链接入口，禁止孤岛内容。

---

## 版本历史

> 所有变更记录集中于此，不再散落在代码注释里。

| 版本 | 日期 | Changelog |
| ---- | ---- | --------- |
| v1.0 | 2026-04-07 | 初始版本 |

---

## 本文件章节索引

| § | 章节 | 对应 L0 入口 |
| :---: | ---- | :---: |
| §1 | [配置常量](#1-配置常量-config-constants) | L0 §6 数据模型 |
| §2 | [完整数据结构](#2-核心数据结构完整定义-full-data-structures) | L0 §6 数据模型 |
| §3 | [核心算法伪代码](#3-核心算法伪代码-non-trivial-algorithm-pseudocode) | L0 §5 操作契约表 |
| §4 | [决策树详细逻辑](#4-决策树详细逻辑-decision-tree-details) | L0 §4 数据流 |
| §5 | [边缘情况与注意事项](#5-边缘情况与注意事项-edge-cases--gotchas) | L0 §5 / §9 |

---

## §1 配置常量 (Config Constants)

> 所有配置类常量集中放在此处。
> **L0 对应入口**: L0 §6 末尾锚点 → *配置常量详见 [L1 §1](./spirit-card-system.detail.md#1-配置常量-config-constants)*

```python
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
```

---

## §2 核心数据结构完整定义 (Full Data Structures)

> 含方法体的完整类定义。L0 层只放属性声明和方法签名（`def foo(): ...`）。
> **L0 对应入口**: L0 §6.1 末尾锚点 → *完整方法实现详见 [L1 §2](./spirit-card-system.detail.md#2-核心数据结构完整定义-full-data-structures)*

```python
from dataclasses import dataclass, field
from html import escape
from typing import Literal


@dataclass
class SpiritCardModel:
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
        return any(item.get("value") is not None for item in self.stat_items)


@dataclass
class RenderPolicy:
    enable_chart_enhancement: bool = True
    max_visible_skills: int = 8
    allow_external_assets: bool = False
    prefer_compact_layout: bool = True
    theme_name: str = "roco_adventure_journal"


@dataclass
class RenderedSpiritCard:
    html: str
    fallback_text: str
    render_mode: Literal["rich_html", "html_with_text_fallback", "text_only"]
    metadata: dict = field(default_factory=dict)

    def is_renderable(self) -> bool:
        return bool(self.html or self.fallback_text)
```

---

## §3 核心算法伪代码 (Non-Trivial Algorithm Pseudocode)

> 每个小节对应 L0 §5 操作契约表的一行，提供完整函数体。

### §3.1 `build_spirit_card_model(profile, options)`

**对应契约**: L0 §5.1 — `build_spirit_card_model(profile, options)`
**准入理由**: 含多步骤字段映射 + 同事看签名猜不出实现

```python
def build_spirit_card_model(profile: dict, options: dict | None = None) -> SpiritCardModel:
    options = options or {}

    stat_items = [
        {"label": "HP", "value": profile.get("base_stats", {}).get("hp")},
        {"label": "攻击", "value": profile.get("base_stats", {}).get("attack")},
        {"label": "防御", "value": profile.get("base_stats", {}).get("defense")},
        {"label": "魔攻", "value": profile.get("base_stats", {}).get("magic_attack")},
        {"label": "魔抗", "value": profile.get("base_stats", {}).get("magic_defense")},
        {"label": "速度", "value": profile.get("base_stats", {}).get("speed")},
    ]

    return SpiritCardModel(
        display_name=profile.get("display_name") or profile.get("canonical_name") or "未知精灵",
        canonical_name=profile.get("canonical_name", ""),
        types=profile.get("types", []),
        stat_items=stat_items,
        skills=(profile.get("skills") or [])[: options.get("max_visible_skills", CARD_RENDER_POLICY["max_visible_skills"])],
        bloodline_type=profile.get("bloodline_type"),
        evolution_chain=profile.get("evolution_chain", []),
        wiki_url=profile.get("wiki_url", ""),
        source_label=options.get("source_label", "BWIKI"),
    )
```

> **注意事项**: 展示字段必须从结构化 profile 显式映射，不能在模板里到处访问原始 profile，避免模板层失控。

### §3.2 `sanitize_spirit_content(card_model)`

**对应契约**: L0 §5.1 — `sanitize_spirit_content(card_model)`
**准入理由**: 含安全规则 + 多步骤文本处理

```python
def sanitize_spirit_content(card_model: SpiritCardModel) -> SpiritCardModel:
    safe_url = ""
    if card_model.wiki_url.startswith("https://wiki.biligame.com/"):
        safe_url = card_model.wiki_url

    safe_skills = []
    for skill in card_model.skills:
        safe_skills.append(
            {
                "name": escape(str(skill.get("name", ""))),
                "type": escape(str(skill.get("type", ""))) if skill.get("type") else None,
                "description": escape(str(skill.get("description", "")))[: SANITIZATION_POLICY.get("max_skill_description_chars", 80)],
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
```

> **注意事项**: 链接必须白名单校验，不能因为“只是卡片跳转链接”就放松协议过滤。

### §3.3 `render_spirit_card(card_model, policy)`

**对应契约**: L0 §5.1 — `render_spirit_card(card_model, policy)`
**准入理由**: 含多步骤副作用链 + 降级路径

```python
def render_spirit_card(card_model: SpiritCardModel, policy: RenderPolicy, template_renderer) -> RenderedSpiritCard:
    safe_model = sanitize_spirit_content(card_model)
    stat_block = render_stats_visual(safe_model, {"script_runtime": policy.enable_chart_enhancement})
    fallback_text = build_fallback_text(safe_model)

    html = template_renderer.render(
        "spirit_card.html",
        {
            "card": safe_model,
            "stat_block": stat_block,
            "policy": policy,
        },
    )

    render_mode = "rich_html" if html else "text_only"
    if html and fallback_text:
        render_mode = "html_with_text_fallback"

    return RenderedSpiritCard(
        html=html,
        fallback_text=fallback_text,
        render_mode=render_mode,
        metadata={
            "chart_enabled": stat_block.get("mode") == "chart",
            "has_wiki_link": bool(safe_model.wiki_url),
        },
    )
```

> **注意事项**: fallback 文本应在 HTML 生成之前就准备好，不能把“生成失败再补救”当成主设计。

### §3.4 `render_stats_visual(card_model, sandbox_caps)`

**对应契约**: L0 §5.1 — `render_stats_visual(card_model, sandbox_caps)`
**准入理由**: 含条件分支 + 宿主能力判断

```python
def render_stats_visual(card_model: SpiritCardModel, sandbox_caps: dict) -> dict:
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
```

> **注意事项**: 图表模式只是增强层；数值网格必须始终可用。

### §3.5 `build_fallback_text(card_model)`

**对应契约**: L0 §5.1 — `build_fallback_text(card_model)`
**准入理由**: 含信息压缩与展示取舍

```python
def build_fallback_text(card_model: SpiritCardModel) -> str:
    type_text = " / ".join(card_model.types) if card_model.types else "未知系别"
    stat_lines = [f"{item['label']}:{item['value']}" for item in card_model.stat_items if item.get("value") is not None]
    skill_names = [skill.get("name") for skill in card_model.skills if skill.get("name")]

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
```

> **注意事项**: fallback 不是“第二份完整卡片”，而是用户在富展示失败时仍能继续决策的最小充分信息。

---

## §4 决策树详细逻辑 (Decision Tree Details)

> 对应 L0 Mermaid 数据流图的文字展开 + 伪代码。

### §4.1 卡片渲染路径选择

**对应 L0 Mermaid**: `spirit-card-system.md §4.3`

```python
def decide_card_render_flow(profile: dict, sandbox_caps: dict) -> str:
    if not profile:
        return "text_only_error"

    if sandbox_caps.get("rich_ui_available"):
        if sandbox_caps.get("script_runtime"):
            return "rich_html_with_chart"
        return "rich_html_without_chart"

    return "fallback_text_only"
```

---

## §5 边缘情况与注意事项 (Edge Cases & Gotchas)

| 场景 | 风险 | 处理方式 |
| ---- | ---- | -------- |
| `base_stats` 缺字段 | 图表或数值排版异常 | 用 `None` 占位并仅展示可用项 |
| 技能列表过长 | 卡片高度失控，消息区可读性变差 | 限制可见数量，其余折叠或省略 |
| wiki_url 缺失或非法 | 跳转按钮成为危险入口或坏链 | 仅允许白名单 https 链接，否则隐藏按钮 |
| Rich UI 脚本不可用 | 图表区空白 | 回退到数值网格 |
| 模板渲染异常 | 卡片整体消失 | 返回 `fallback_text` + 诊断 metadata |
| 卡片视觉退回默认平台样式 | 与主 UI 风格断裂 | 模板内联 token 固定 + 人工核对标题区、纸张底与标签样式 |

### §5.1 Rich UI 图表降级

```python
# ❌ 错误做法
# render_chart_only(stat_values)

# ✅ 正确做法
# if script_runtime:
#     render_chart(stat_values)
# else:
#     render_numeric_stat_grid(stat_values)
```

### §5.2 Card Visual Reference

```css
.spirit-card {
  background: #F9F8F4;
  color: #333333;
  border: 1px solid rgba(51, 51, 51, 0.10);
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(45, 44, 42, 0.10);
}

.spirit-card__title {
  border-left: 6px solid #F3C969;
  padding-left: 12px;
}

.spirit-card__skill-tag {
  background: rgba(243, 201, 105, 0.18);
  border: 1px dashed rgba(51, 51, 51, 0.28);
  border-radius: 9999px;
}
```

```txt
card_shell: rounded-[20px] bg-[var(--roco-surface)] border border-black/10 shadow-[0_10px_30px_rgba(45,44,42,0.10)]
card_title: flex items-center gap-3 text-[var(--roco-text-main)]
stat_grid: grid grid-cols-2 md:grid-cols-3 gap-3
skill_tag: rounded-full border border-dashed px-3 py-1
source_link: inline-flex items-center gap-2 text-sm text-[var(--roco-text-main)]
```

---
