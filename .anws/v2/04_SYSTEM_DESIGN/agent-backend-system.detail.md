# agent-backend-system — 实现细节 (L1)

> **文件性质**: L1 实现层 · **对应 L0**: [`agent-backend-system.md`](./agent-backend-system.md)
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

> 所有硬编码配置、枚举映射、查找表集中放在此处。
> **L0 对应入口**: L0 §6 末尾锚点 → *配置常量详见 [L1 §1](./agent-backend-system.detail.md#1-配置常量-config-constants)*

```python
STREAM_SETTINGS = {
    "content_type": "text/event-stream",
    "done_marker": "data: [DONE]\\n\\n",
    "chunk_object": "chat.completion.chunk",
}

SESSION_POLICY = {
    "idle_ttl_minutes": 30,
    "max_messages_per_session": 40,
    "key_format": "user_id:chat_id",
    "missing_identity_action": "reject_400",
}

MODEL_CATALOG_POLICY = {
    "owned_by": "roco-agent",
    "default_visibility": "controlled",
    "supports_vision_flag": True,
}

PRODUCT_ERROR_CODE_PREFIX = {
    "quota": "QUOTA_",
    "capability": "CAPABILITY_",
    "rate_limit": "RATE_LIMIT_",
}

QUOTA_POLICY_DEFAULTS = {
    "owner_scope": "session",
    "window_seconds": 1800,
    "limit_tokens": 120000,
    "exhaustion_action": "suggest_byok",
}
```

---

## §2 核心数据结构完整定义 (Full Data Structures)

> 含方法体的完整类定义。L0 层只放属性声明和方法签名（`def foo(): ...`）。
> **L0 对应入口**: L0 §6.1 末尾锚点 → *完整方法实现详见 [L1 §2](./agent-backend-system.detail.md#2-核心数据结构完整定义-full-data-structures)*

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import asyncio


@dataclass
class ModelCatalogEntry:
    public_model_id: str
    provider_model_name: str
    provider_base_url: str
    supports_vision: bool
    enabled: bool
    default_temperature: float | None = None

    def can_accept_image(self) -> bool:
        return self.enabled and self.supports_vision


@dataclass
class BuiltinQuotaPolicy:
    owner_scope: Literal["ip", "session"]
    window_seconds: int
    limit_tokens: int
    exhaustion_action: Literal["suggest_byok"]

    def owner_key_for(self, context: "ChatRequestContext") -> str:
        if self.owner_scope == "ip":
            return context.request_headers.get("x-forwarded-for", "unknown_ip")
        return context.session_key


@dataclass
class BuiltinQuotaState:
    owner_key: str
    window_started_at: datetime
    tokens_used: int
    tokens_remaining: int
    status: Literal["available", "exhausted"]

    def is_exhausted(self) -> bool:
        return self.status == "exhausted"


@dataclass
class QuotaDecision:
    allowed: bool
    error_code: str | None
    retry_after_seconds: int | None
    suggested_route: Literal["builtin", "byok"] | None


@dataclass
class ChatRequestContext:
    request_id: str
    session_key: str
    model_entry: ModelCatalogEntry
    messages: list[dict[str, Any]]
    stream: bool
    user_id: str
    chat_id: str | None
    request_headers: dict[str, str] = field(default_factory=dict)

    def normalized_token_budget(self) -> int | None:
        return None


@dataclass
class SessionRecord:
    session_key: str
    items: list[dict[str, Any]] = field(default_factory=list)
    last_access_at: datetime = field(default_factory=datetime.utcnow)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def touch(self) -> None:
        self.last_access_at = datetime.utcnow()
```

---

## §3 核心算法伪代码 (Non-Trivial Algorithm Pseudocode)

> 每个小节对应 L0 §5 操作契约表的一行，提供完整函数体。

### §3.1 `resolve_session_key(headers, body)`

**对应契约**: L0 §5.1 — `resolve_session_key(headers, body)`
**准入理由**: 含不明显的业务规则 + 会话边界约束

```python
def resolve_session_key(headers: dict, body: dict) -> str:
    user_id = headers.get("X-OpenWebUI-User-Id")
    chat_id = headers.get("X-OpenWebUI-Chat-Id")

    if not user_id or not chat_id:
        raise ValueError("missing session identity")

    return f"{user_id}:{chat_id}"
```

> **注意事项**: 不允许回退到 `user_id`、`external_session_id` 或随机 key；否则会直接破坏 ADR-003 定义的会话隔离边界。


### §3.2 `normalize_chat_request(payload, catalog)`

**对应契约**: L0 §5.1 — `normalize_chat_request(payload, headers, catalog)`
**准入理由**: 含多步骤校验与消息结构保真约束

```python
def normalize_chat_request(payload: dict, headers: dict, catalog: dict) -> ChatRequestContext:
    model_id = payload["model"]
    model_entry = catalog.get(model_id)
    if not model_entry or not model_entry.enabled:
        raise LookupError("unknown model")

    messages = payload.get("messages", [])
    if not messages:
        raise ValueError("messages required")

    if contains_image_part(messages) and not model_entry.supports_vision:
        raise CapabilityError(
            code=f"{PRODUCT_ERROR_CODE_PREFIX['capability']}VISION_UNSUPPORTED",
            message="当前模型不支持截图识别，请切换支持视觉的模型或切回内置轨道",
        )

    session_key = resolve_session_key(headers, payload)
    return ChatRequestContext(
        request_id=make_request_id(),
        session_key=session_key,
        model_entry=model_entry,
        messages=messages,
        stream=bool(payload.get("stream", False)),
        user_id=headers.get("X-OpenWebUI-User-Id", ""),
        chat_id=headers.get("X-OpenWebUI-Chat-Id"),
        request_headers=headers,
    )
```

> **注意事项**: 不能把 `messages[].content[]` 压平成纯文本，也不能把视觉能力不支持混同为普通 `VALIDATION_` 或 Provider 原始报错。


### §3.3 `stream_runtime_events(events, model_id)`

**对应契约**: L0 §5.1 — `stream_runtime_events(events, model_id)`
**准入理由**: 含多步骤副作用链 + mid-stream error 特判

```python
def stream_runtime_events(events, model_id: str):
    chunk_id = make_completion_id()
    for event in events:
        if event.type == "token":
            yield encode_chunk(chunk_id, model_id, delta=event.text)
            continue
        if event.type == "tool_result":
            yield encode_tool_chunk(chunk_id, model_id, event.payload)
            continue
        if event.type == "error":
            yield encode_error_chunk(chunk_id, model_id, event.error)
            yield STREAM_SETTINGS["done_marker"]
            return

    yield STREAM_SETTINGS["done_marker"]
```

> **注意事项**: 首 token 之后不能再切回普通 JSON 错误响应，只能发错误 chunk 再收尾。

### §3.4 `list_models(catalog)`

**对应契约**: L0 §5.1 — `list_models(catalog)`
**准入理由**: 含不明显的业务规则（受控虚拟模型过滤）

```python
def list_models(catalog: dict[str, ModelCatalogEntry]) -> list[dict]:
    visible_models = []
    for entry in catalog.values():
        if not entry.enabled:
            continue
        visible_models.append(
            {
                "id": entry.public_model_id,
                "object": "model",
                "owned_by": MODEL_CATALOG_POLICY["owned_by"],
                "metadata": {
                    "supports_vision": entry.supports_vision,
                },
            }
        )

    return visible_models
```

> **注意事项**: 不能把 provider 原生模型名直接暴露给前端，否则会破坏受控模型目录边界。

### §3.5 `run_agent_turn(context, session_items)`

**对应契约**: L0 §5.1 — `run_agent_turn(context, session_items)`
**准入理由**: 含多步骤副作用链 + 同事看签名猜不出实现

```python
def run_agent_turn(context: ChatRequestContext, session_items: list[dict]):
    runtime_input = build_runtime_input(context.messages, session_items)
    provider = build_provider_for_model(context.model_entry)
    tools = build_tool_registry(context.model_entry)

    return runner.run_streamed(
        input=runtime_input,
        model=provider,
        tools=tools,
        session_key=context.session_key,
    )
```

> **注意事项**: 历史消息与本轮输入的拼接顺序必须稳定，否则会导致多轮对话语义漂移。

### §3.6 `evict_idle_sessions(registry, now)`

**对应契约**: L0 §5.1 — `evict_idle_sessions(registry, now)`
**准入理由**: 含 TTL 截止时间计算 + 遍历删除顺序约束

```python
def evict_idle_sessions(registry: dict[str, SessionRecord], now: datetime) -> list[str]:
    cutoff = now - timedelta(minutes=SESSION_POLICY["idle_ttl_minutes"])
    evicted_keys = []

    for session_key, record in registry.items():
        if record.last_access_at <= cutoff:
            evicted_keys.append(session_key)

    for session_key in evicted_keys:
        del registry[session_key]

    return evicted_keys
```

> **注意事项**: 不能在遍历 `registry.items()` 的同时原地删除；必须先收集待清理 key，再统一删除，否则会破坏 janitor 的稳定性与可预测性。

### §3.7 `enforce_builtin_quota(context, policy, state_store)`

**对应契约**: L0 §5.1 — `enforce_builtin_quota(context, quota_state)`
**准入理由**: 含额度 owner 计算、窗口判断和产品级错误决策

```python
def enforce_builtin_quota(context: ChatRequestContext, policy: BuiltinQuotaPolicy, state_store) -> QuotaDecision:
    owner_key = policy.owner_key_for(context)
    state = state_store.get_or_create(owner_key, policy)

    if state.is_exhausted():
        return QuotaDecision(
            allowed=False,
            error_code=f"{PRODUCT_ERROR_CODE_PREFIX['quota']}WINDOW_EXHAUSTED",
            retry_after_seconds=seconds_until_window_reset(state, policy),
            suggested_route="byok",
        )

    return QuotaDecision(
        allowed=True,
        error_code=None,
        retry_after_seconds=None,
        suggested_route="builtin",
    )
```

> **注意事项**: 这是产品额度，不是 Provider `RATE_LIMIT_`；v2 只定义单机内存态最小模型，不引入分布式共享额度。


---

## §4 决策树详细逻辑 (Decision Tree Details)

> 对应 L0 Mermaid 数据流图的文字展开 + 完整伪代码。
> **L0 对应入口**: L0 §4.3 数据流 → *完整决策逻辑见 [L1 §4](./agent-backend-system.detail.md#4-决策树详细逻辑-decision-tree-details)*

### §4.1 请求处理路径选择

**对应 L0 Mermaid**: `agent-backend-system.md §4.3`

```python
def handle_request_flow(payload, headers, catalog, quota_policy, quota_store, session_store, runtime):
    context = normalize_chat_request(payload, headers, catalog)
    quota_decision = enforce_builtin_quota(context, quota_policy, quota_store)
    if not quota_decision.allowed:
        raise ProductError(
            code=quota_decision.error_code,
            retry_after_seconds=quota_decision.retry_after_seconds,
            suggested_route=quota_decision.suggested_route,
        )

    session = session_store.get_or_create(context.session_key)

    with session.lock:
        session.touch()
        runtime_events = runtime.run(context, session.items)
        return stream_runtime_events(runtime_events, context.model_entry.public_model_id)
```

---

## §5 边缘情况与注意事项 (Edge Cases & Gotchas)

> 实现时必须处理的非显而易见情况。
> **L0 对应入口**: L0 §5 或 §9 安全性章节的锚点

| 场景 | 风险 | 处理方式 |
| ---- | ---- | -------- |
| 同一 `session_key` 并发请求 | 上下文串写、历史乱序 | 会话级 `asyncio.Lock` 串行化 |
| 图片消息发送到非视觉模型 | 运行时 provider 报错 | 在请求归一化阶段返回 `CAPABILITY_` 产品错误 |
| builtin route 额度耗尽 | 被误判为 provider 限流 | 在进入 runtime 前返回 `QUOTA_` 错误，并附 `suggested_route=byok` |
| 流中途 provider 失败 | 客户端收不到标准结束帧 | 发送错误 chunk 后补 `[DONE]` |
| 缺少 `chat_id` 或 `user_id` | 同用户多聊天可能串上下文 | 直接 400 拒绝，不做回退 |
| 会话无限增长 | 内存膨胀、上下文超窗 | TTL 清理 + 消息条数上限 |

### §5.1 mid-stream error 处理

```python
# ❌ 错误做法
# raise provider_error  # 直接断流，客户端只能看到网络错误

# ✅ 正确做法
# yield encode_error_chunk(...)
# yield "data: [DONE]\n\n"
```

---
