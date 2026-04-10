# web-ui-system — 实现细节 (L1)

> **文件性质**: L1 实现层 · **对应 L0**: [`web-ui-system.md`](./web-ui-system.md)
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
| §4 | [决策树详细逻辑](#4-决策树详细逻辑-decision-tree-details) | L0 §4 数据流 / 决策说明 |
| §5 | [边缘情况与注意事项](#5-边缘情况与注意事项-edge-cases--gotchas) | L0 §5 / §9 |

---

## §1 配置常量 (Config Constants)

> 所有配置类常量集中放在此处。
> **L0 对应入口**: L0 §6 末尾锚点 → *配置常量详见 [L1 §1](./web-ui-system.detail.md#1-配置常量-config-constants)*

```python
VISIBLE_FEATURE_KEYS = [
    "chat_enabled",
    "image_upload_enabled",
    "builtin_route_enabled",
    "byok_enabled",
    "tool_result_enabled",
    "rich_ui_enabled",
]

FORBIDDEN_ENTRY_GROUPS = {
    "workspace": ["knowledge", "notes", "documents"],
    "collaboration": ["channels"],
    "terminal": ["open_terminal"],
    "platform_ops": ["models_admin", "agents_admin", "experiments"],
    "admin": ["system_connections", "global_settings"],
}

ROUTE_MODE = {
    "builtin": "agent-backend-system via system OpenAI-compatible connection",
    "byok": "user-managed direct connection via localStorage",
}

BUILTIN_QUOTA_STATUS = ["available", "exhausted", "unknown"]
CAPABILITY_ERROR_CODES = {
    "vision_unsupported": "CAPABILITY_VISION_UNSUPPORTED",
}
VISIBLE_FEATURE_SNAPSHOT_SCOPE = [
    "home",
    "sidebar",
    "topbar",
    "settings",
    "mobile_navigation",
]

THEME_ROOT_TOKENS = {
    "--roco-bg-paper": "#EFEBE1",
    "--roco-bg-sidebar": "#2D2C2A",
    "--roco-accent": "#F3C969",
    "--roco-surface": "#F9F8F4",
    "--roco-text-main": "#333333",
    "--roco-text-inverse": "#F0F0F0",
}

DOM_SELECTOR_MAP = {
    "sidebar": ["aside", ".bg-gray-900", "[data-testid='history-sidebar']"],
    "main_surface": ["main", "[role='main']", ".bg-black", ".bg-neutral-950"],
    "chat_input": ["form textarea", "[data-testid='chat-input'] textarea"],
    "history_item": ["aside button", "aside a[role='button']"],
    "rich_ui_host": ["iframe", ".artifact-panel", "[data-testid='tool-result']"],
}

COMPONENT_CLASSMAP = {
    "shell": ["min-h-screen", "bg-[var(--roco-bg-paper)]", "text-[var(--roco-text-main)]"],
    "history_tag": ["rounded-xl", "border", "px-3", "py-2", "transition-all"],
    "chat_input": ["rounded-full", "bg-[var(--roco-surface)]", "border-0", "px-4", "py-3"],
}
```

---

## §2 核心数据结构完整定义 (Full Data Structures)

> 含方法体的完整类定义。L0 层只放属性声明和方法签名（`def foo(): ...`）。
> **L0 对应入口**: L0 §6.1 末尾锚点 → *完整方法实现详见 [L1 §2](./web-ui-system.detail.md#2-核心数据结构完整定义-full-data-structures)*

```python
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class VisibleFeaturePolicy:
    chat_enabled: bool
    image_upload_enabled: bool
    builtin_route_enabled: bool
    byok_enabled: bool
    tool_result_enabled: bool
    rich_ui_enabled: bool
    forbidden_entries: list[str] = field(default_factory=list)
    policy_version: str = "v2"
    snapshot_scope: list[str] = field(default_factory=lambda: VISIBLE_FEATURE_SNAPSHOT_SCOPE.copy())
    expected_visible_entries: list[str] = field(default_factory=list)
    expected_hidden_entries: list[str] = field(default_factory=list)
    validation_baseline_id: str | None = None

    def allows(self, feature_key: str) -> bool:
        if feature_key == "chat":
            return self.chat_enabled
        if feature_key == "image_upload":
            return self.image_upload_enabled
        if feature_key == "builtin_route":
            return self.builtin_route_enabled
        if feature_key == "byok":
            return self.byok_enabled
        if feature_key == "tool_result":
            return self.tool_result_enabled
        if feature_key == "rich_ui":
            return self.rich_ui_enabled
        return False

    def to_snapshot(self) -> dict:
        return {
            "policy_version": self.policy_version,
            "snapshot_scope": self.snapshot_scope,
            "expected_visible_entries": self.expected_visible_entries,
            "expected_hidden_entries": self.expected_hidden_entries,
            "validation_baseline_id": self.validation_baseline_id,
        }


@dataclass
class UiRouteState:
    active_route: Literal["builtin", "byok"]
    active_model_id: str | None
    chat_id: str | None
    is_uploading: bool = False
    rich_ui_available: bool = False
    active_model_supports_vision: bool | None = None
    builtin_quota_status: Literal["available", "exhausted", "unknown"] = "unknown"

    def can_send(self) -> bool:
        return self.active_model_id is not None and not self.is_uploading


@dataclass
class ThemeOverrideConfig:
    theme_name: Literal["roco_adventure_journal"]
    root_tokens: dict[str, str] = field(default_factory=dict)
    selector_map: dict[str, list[str]] = field(default_factory=dict)
    texture_strategy: str = "paper_texture_svg_overlay"
    sidebar_edge_style: str = "torn_paper_mask"
    bubble_style_mode: str = "journal_bubbles"

    def selector_count(self) -> int:
        return sum(len(items) for items in self.selector_map.values())
```

---

## §3 核心算法伪代码 (Non-Trivial Algorithm Pseudocode)

> 每个小节对应 L0 §5 操作契约表的一行，提供完整函数体。

### §3.1 `filter_navigation(user_role, policy)`

**对应契约**: L0 §5.1 — `filter_navigation(user_role, policy)`
**准入理由**: 含不明显的业务规则 + 多步骤副作用链

```python
def filter_navigation(user_role: str, policy: VisibleFeaturePolicy, nav_items: list[dict]) -> list[dict]:
    visible_items = []

    for item in nav_items:
        key = item.get("key")

        if user_role != "admin" and key in policy.forbidden_entries:
            continue

        if key == "chat" and not policy.chat_enabled:
            continue
        if key == "upload" and not policy.image_upload_enabled:
            continue
        if key == "byok" and not policy.byok_enabled:
            continue
        if key == "tool_result" and not policy.tool_result_enabled:
            continue
        if key == "rich_ui" and not policy.rich_ui_enabled:
            continue

        visible_items.append(item)

    return visible_items
```

> **注意事项**: 需要同时覆盖桌面侧边栏、移动导航、空状态页快捷入口，避免“隐藏了 A 但 B 入口仍然可达”。

### §3.2 `select_route(route_state, builtin_ready, direct_ready)`

**对应契约**: L0 §5.1 — `select_route(route_state, builtin_ready, direct_ready)`
**准入理由**: 同事看签名猜不出实现 + 含多步骤副作用链

```python
def select_route(route_state: UiRouteState, builtin_ready: bool, direct_ready: bool) -> str:
    if route_state.active_route == "builtin":
        if builtin_ready:
            return "builtin"
        if direct_ready:
            return "byok"
        raise RuntimeError("No available route")

    if route_state.active_route == "byok":
        if direct_ready:
            return "byok"
        if builtin_ready:
            return "builtin"
        raise RuntimeError("No available route")

    raise ValueError("Invalid route mode")
```

> **注意事项**: 回退时必须向用户显式提示，不能静默切轨导致用户误以为仍在使用自己的 Key。

### §3.3 `render_message_artifacts(message, policy)`

**对应契约**: L0 §5.1 — `render_message_artifacts(message, policy)`
**准入理由**: 含多步骤副作用链

```python
def render_message_artifacts(message: dict, policy: VisibleFeaturePolicy) -> dict:
    output = {"text": message.get("text")}

    if policy.tool_result_enabled and message.get("tool_calls"):
        output["tool_cards"] = message["tool_calls"]

    if policy.rich_ui_enabled and message.get("rich_ui_payload"):
        output["rich_ui"] = {
            "mode": "iframe",
            "payload": message["rich_ui_payload"],
        }
    elif message.get("rich_ui_payload"):
        output["fallback_card"] = message["rich_ui_payload"].get("fallback_text")

    return output
```

> **注意事项**: Rich UI 渲染失败不能吞掉文本主消息，必须保底保留纯文本答案。

### §3.4 `submit_text_message(text, route_state)`

**对应契约**: L0 §5.1 — `submit_text_message(text, route_state)`
**准入理由**: 含多步骤副作用链

```python
def submit_text_message(text: str, route_state: UiRouteState, transport) -> dict:
    if not text.strip():
        raise ValueError("empty message")
    if not route_state.can_send():
        raise RuntimeError("route not ready")

    payload = {
        "messages": [{"role": "user", "content": text}],
        "model": route_state.active_model_id,
        "chat_id": route_state.chat_id,
    }
    return transport.send(payload)
```

> **注意事项**: 发送前必须读取当前轨道状态，避免 UI 显示与实际请求目标不一致。

### §3.5 `submit_image_message(file, route_state)`

**对应契约**: L0 §5.1 — `preflight_image_capability(route_state, model_capability)` / `submit_image_message(file, route_state)`
**准入理由**: 含多步骤校验 + 多模态副作用链

```python
def submit_image_message(file, route_state: UiRouteState, uploader, transport) -> dict:
    if not route_state.can_send():
        raise RuntimeError("route not ready")
    if not uploader.is_supported_image(file):
        raise ValueError("unsupported image type")

    supports_vision = route_state.active_model_supports_vision is True
    if not supports_vision:
        raise CapabilityError(
            code=CAPABILITY_ERROR_CODES["vision_unsupported"],
            message="当前轨道/模型不支持截图识别，请切换支持视觉的模型或切回内置轨道",
        )

    image_part = uploader.to_openai_image_part(file)
    payload = {
        "messages": [{"role": "user", "content": [image_part]}],
        "model": route_state.active_model_id,
        "chat_id": route_state.chat_id,
    }
    return transport.send(payload)
```

> **注意事项**: 不能在前端把图片内容提前压平成普通文本描述，也不能在能力不满足时静默切轨代用户发送。


### §3.6 `persist_direct_connection(base_url, api_key, config)`

**对应契约**: L0 §5.1 — `persist_direct_connection(base_url, api_key, config)`
**准入理由**: 含不明显的业务规则（仅本地保存）

```python
def persist_direct_connection(base_url: str, api_key: str, config: dict, storage) -> None:
    normalized_url = base_url.rstrip("/")
    storage.save(
        "direct_connection",
        {
            "base_url": normalized_url,
            "api_key": api_key,
            "config": config,
            "storage_scope": "localStorage",
        },
    )
```

> **注意事项**: 只能写浏览器本地存储，不能把 Key 上送到 `agent-backend-system`。

### §3.7 `register_builtin_connection(base_url, config)`

**对应契约**: L0 §5.1 — `register_builtin_connection(base_url, config)`
**准入理由**: 含多步骤副作用链 + 管理员权限边界

```python
def register_builtin_connection(base_url: str, config: dict, admin_api) -> dict:
    normalized_url = base_url.rstrip("/")
    return admin_api.create_openai_connection(
        {
            "url": normalized_url,
            "config": config,
            "managed_by": "system_admin",
        }
    )
```

> **注意事项**: 该操作只属于管理员维护面，不得从终端用户主路径触发。

### §3.8 `build_theme_override_css(theme_config, selector_map)`

**对应契约**: L0 §5.1 — `build_theme_override_css(theme_config, selector_map)`
**准入理由**: 含多阶段样式拼装 + DOM 锚点策略

```python
def build_theme_override_css(theme_config: ThemeOverrideConfig, selector_map: dict[str, list[str]]) -> str:
    root_block = [":root {"]
    for token_name, token_value in theme_config.root_tokens.items():
        root_block.append(f"  {token_name}: {token_value};")
    root_block.append("}")

    sidebar_selectors = ",\n".join(selector_map["sidebar"])
    main_selectors = ",\n".join(selector_map["main_surface"])
    input_selectors = ",\n".join(selector_map["chat_input"])
    history_selectors = ",\n".join(selector_map["history_item"])

    css_chunks = ["\n".join(root_block)]
    css_chunks.append(
        f"""
{sidebar_selectors} {{
  background: var(--roco-bg-sidebar) !important;
  color: var(--roco-text-inverse) !important;
}}

{main_selectors} {{
  background: var(--roco-bg-paper) !important;
  color: var(--roco-text-main) !important;
}}

{input_selectors} {{
  background: var(--roco-surface) !important;
  border-radius: 9999px !important;
  border: none !important;
}}

{history_selectors}:hover,
{history_selectors}[aria-current='page'] {{
  background: var(--roco-accent) !important;
}}
""".strip()
    )

    return "\n\n".join(css_chunks)
```

> **注意事项**: 必须优先依赖语义容器和有限的 selector map，避免把实现完全绑死到 Open WebUI 的瞬时类名上。

---

## §4 决策树详细逻辑 (Decision Tree Details)

> 对应 L0 Mermaid 决策图的文字展开 + 伪代码。

### §4.1 发送前轨道决策

**对应 L0 Mermaid**: `web-ui-system.md §4.3`

```python
def decide_send_path(user_prefers_byok: bool, builtin_ready: bool, direct_ready: bool) -> str:
    if user_prefers_byok:
        if direct_ready:
            return "byok"
        if builtin_ready:
            return "builtin_with_warning"
        return "block"

    if builtin_ready:
        return "builtin"
    if direct_ready:
        return "byok_with_warning"
    return "block"
```

### §4.2 图片发送前能力决策

**对应 L0 Mermaid**: `web-ui-system.md §4.3`

```python
def decide_image_send(route_state: UiRouteState) -> str:
    if route_state.builtin_quota_status == "exhausted":
        return "block_quota_exhausted"

    if route_state.active_model_supports_vision is not True:
        return "block_capability_unsupported"

    if route_state.active_route == "builtin":
        return "send_builtin"

    if route_state.active_route == "byok":
        return "send_byok"

    return "block"
```

---

## §5 边缘情况与注意事项 (Edge Cases & Gotchas)

| 场景 | 风险 | 处理方式 |
| ---- | ---- | -------- |
| 上游升级后入口回流 | 用户重新看到平台化入口 | 对首页、侧栏、设置、移动导航做 UI 回归检查，并与 `VisibleFeaturePolicy` 导出快照比对 |
| BYOK 连接存在但 CORS 不通过 | 用户误以为系统异常 | 明确提示是 Provider 跨域限制，而非产品后端故障 |
| BYOK 当前模型不支持视觉 | 截图请求回流为 Provider 默认报错 | 发送前返回 `CAPABILITY_` 错误，提示换模型或切 builtin |
| 内置轨道额度耗尽 | 用户误以为是 provider 限流或网络问题 | 显式提示内置额度已耗尽，引导切换 BYOK 或等待窗口重置 |
| Rich UI iframe 加载失败 | 消息区空白 | 回退为结构化文本卡片 |
| 管理员入口误暴露给普通用户 | 权限边界破坏 | 角色校验 + 路由隔离 + 导航过滤三层防线 |
| 用户切换轨道后状态不清晰 | 误解当前消耗的是谁的 Key | 在设置区与消息区显示当前轨道状态 |
| Open WebUI 升级后 DOM 类名变化 | 主题样式失效或局部回退 | 优先语义选择器 + selector map 集中维护 + 发布前人工回归 |

### §5.1 Rich UI 降级

```python
# ❌ 错误做法
# if rich_ui_payload:
#     render_iframe_only()

# ✅ 正确做法
# if rich_ui_payload and iframe_ready:
#     render_iframe()
# else:
#     render_structured_text_fallback()
```

### §5.2 UI Theme Override Reference

```css
:root {
  --roco-bg-paper: #EFEBE1;
  --roco-bg-sidebar: #2D2C2A;
  --roco-accent: #F3C969;
  --roco-surface: #F9F8F4;
  --roco-text-main: #333333;
  --roco-text-inverse: #F0F0F0;
}

html.dark aside,
html.dark .bg-gray-900,
html.dark [data-testid="history-sidebar"] {
  background: var(--roco-bg-sidebar) !important;
  color: var(--roco-text-inverse) !important;
}

html.dark form textarea,
html.dark [data-testid="chat-input"] textarea {
  background: var(--roco-surface) !important;
  border-radius: 9999px !important;
  border: none !important;
}
```

```txt
shell: min-h-screen bg-[var(--roco-bg-paper)] text-[var(--roco-text-main)]
history_tag: rounded-xl border px-3 py-2 transition-all hover:bg-[var(--roco-accent)]
chat_input: rounded-full bg-[var(--roco-surface)] border-0 px-4 py-3
user_bubble: bg-[var(--roco-surface)] shadow-[0_4px_6px_rgba(0,0,0,0.05)] px-4 py-3
agent_text: bg-transparent shadow-none border-0 px-0 py-0
```

---
