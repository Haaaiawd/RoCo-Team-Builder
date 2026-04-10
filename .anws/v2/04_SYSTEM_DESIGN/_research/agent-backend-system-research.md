# 探索报告: agent-backend-system

**日期**: 2026-04-07
**探索者**: Cascade / Explorer
**系统**: `agent-backend-system`

---

## 1. 问题与范围

**核心问题**: 如何为 `agent-backend-system` 设计一个可被 `web-ui-system` 作为 OpenAI 兼容端点接入、可处理多轮上下文、兼容第三方 OpenAI 兼容模型、支持多模态图片透传、并满足 v2 单进程内存会话约束的后端系统。

**探索范围**:
- 包含: Open WebUI 集成契约、OpenAI Chat Completions 流式协议、Agents SDK provider/session 约束、Rich UI 沙箱边界、v2 部署与异常处理策略
- 不包含: `data-layer-system` 的具体 BWIKI schema、`spirit-card-system` 的 HTML 细节、`web-ui-system` 的壳层裁剪细节

---

## 2. 核心洞察 (Key Insights)

1. **`/v1/chat/completions` 不是唯一必需接口，`/v1/models` 也必须提供**: Open WebUI 在注册/使用 OpenAI 兼容端点时会主动请求 `GET {base_url}/models` 拉取模型列表，因此后端至少需要实现 `GET /v1/models` 与 `POST /v1/chat/completions` 两个接口。
2. **v2 应强制使用 Chat Completions 路径，而不是 Responses API**: Agents SDK 官方模型文档与本地源码均表明，第三方 OpenAI 兼容 Provider 常常只支持 Chat Completions；`OpenAIProvider(base_url=..., use_responses=False)` 是必须约束，否则会误打 `/responses`。
3. **多模态图片必须原样保留在 `messages[].content[]` 中**: Agents SDK 仅在“官方 OpenAI 客户端”路径校验内容类型；非官方兼容端点不会做该校验。因此后端不应剥离 `image_url` / base64 data URL 内容，而应直接透传给上游模型。
4. **会话隔离应建立在 Open WebUI 转发头上，但不能只用 user id**: `X-OpenWebUI-User-Id` 能实现用户级隔离，但若同一用户并行开启多个聊天，仅用 user id 会串上下文。v2 最佳 key 为 `user_id + chat_id` 组合，缺失时再回退到 `user_id`。
5. **为满足 OpenAI 兼容流式协议，推荐手工输出 SSE 帧，而非通用对象流**: FastAPI 虽提供 `EventSourceResponse`，但本项目需要严格控制 `data: {json}\n\n` 与结束帧 `data: [DONE]\n\n` 的字节级格式，宜采用 `StreamingResponse` + 手工 SSE framing。

---

## 3. 详细发现

### 3.1 Open WebUI 集成契约

**探索方式**: 🔍 本地源码核验 + 官方文档

**发现**:
- Open WebUI 存在 `POST /chat/completions` 路由，并将请求负载转发到注册的 OpenAI 兼容上游。
- Open WebUI 拉取模型清单时会请求上游 `{url}/models`。
- 若开启 `ENABLE_FORWARD_USER_INFO_HEADERS=true`，Open WebUI 会附加用户头；默认头名包括:
  - `X-OpenWebUI-User-Id`
  - `X-OpenWebUI-User-Name`
  - `X-OpenWebUI-User-Email`
  - `X-OpenWebUI-User-Role`
- 若 metadata 中存在 chat_id，还会附加 `X-OpenWebUI-Chat-Id`。

**结论**:
- `agent-backend-system` 的 OpenAI 兼容面必须至少实现 `GET /v1/models` 与 `POST /v1/chat/completions`。
- 会话 key 设计必须消费这些 header，而不是自己发 token。

### 3.2 Agents SDK 的非 OpenAI Provider 集成方式

**探索方式**: 🔍 官方文档 + 本地源码核验

**发现**:
- Agents SDK 官方文档明确建议：对 OpenAI 兼容第三方 Provider，可直接使用 `AsyncOpenAI(base_url=..., api_key=...)` 或 `ModelProvider` 集成。
- 官方文档特别说明：很多第三方 Provider 仍只支持 Chat Completions，因此示例采用 Chat Completions 模型。
- 本地源码表明 `OpenAIProvider.get_model()` 在 `use_responses=False` 时返回 `OpenAIChatCompletionsModel`。

**结论**:
- v2 必须将 provider 初始化写死为 `use_responses=False`。
- 不应在 v2 中使用 `OpenAIResponsesCompactionSession` 等依赖 Responses API 的能力。

### 3.3 多模态图片透传约束

**探索方式**: 🔍 本地源码核验

**发现**:
- `OpenAIChatCompletionsModel._validate_official_openai_input_content_types()` 仅在客户端被识别为官方 OpenAI 且输入是 message list 时才执行。
- 非官方 OpenAI 兼容 endpoint（如 OpenRouter）不会触发这一官方内容类型限制。

**结论**:
- 后端不应在兼容层重新定义或缩减消息内容类型。
- 对含图片的用户消息，应保留 `messages[].content[]` 中的 `text` / `image_url` part 原样结构，直接转给模型层转换器。

### 3.4 Session 实现与生命周期

**探索方式**: 🔍 ADR + 本地源码核验

**发现**:
- Agents SDK `Session` 协议只要求 `get_items/add_items/pop_item/clear_session` 等最小接口。
- `SQLiteSession` 即使默认 `:memory:` 也引入 sqlite 连接与表结构管理，本质仍是一个数据库实现，不适合作为 v2 默认最简路径。
- ADR-003 已明确：v2 使用非持久化内存 Session，`uvicorn --workers 1`，优先 `user_id:chat_id`。

**结论**:
- v2 采用自定义 `InMemorySessionStore` + `Session` 适配层，比直接引入 `SQLiteSession` 更简单、边界更清晰。
- 必须实现 30 分钟闲置清理与进程重启即丢失的显式语义。

### 3.5 SSE 流式输出与错误处理

**探索方式**: 🔍 官方文档 + 第三方兼容端点官方文档

**发现**:
- FastAPI 官方文档说明 SSE 可以运行在 `POST` 上，并强调 keep-alive ping、`Cache-Control: no-cache`、`X-Accel-Buffering: no` 等实践。
- OpenRouter 官方流式文档说明：
  - 若错误发生在首 token 前，返回普通 JSON 错误 + 非 200 HTTP 状态
  - 若错误发生在流中，HTTP 状态已锁定为 `200 OK`，只能以 SSE chunk 形式回传错误，并以 `finish_reason: "error"` 终止流
- OpenAI 官方 streaming 文档正文由于抓取器 403 未能直接读取，但搜索摘要已明确 Chat Completions 支持 `stream=True`；这一点由 Agents SDK 本地测试与模型实现进一步交叉验证。

**结论**:
- 后端需要区分“流前错误”和“流中错误”两套返回路径。
- 为兼容 Open WebUI 透传，响应头必须稳定为 `Content-Type: text/event-stream`。
- 推荐手工输出 OpenAI chunk 结构，而非抽象成自定义事件名。

### 3.6 Rich UI 沙箱对精灵卡片的反向约束

**探索方式**: 🔍 官方文档 + 本地源码线索

**发现**:
- Open WebUI Rich UI iframe 默认开启 sandbox，默认启用 `allow-scripts`、`allow-popups`、`allow-downloads`。
- `allowSameOrigin` 默认关闭；关闭时 iframe 与父页面完全隔离，只能通过 `postMessage` 通信。
- 当 `allowSameOrigin` 开启时，Open WebUI 会自动注入 Chart.js / Alpine.js（检测到 `new Chart(` 等特征时）。

**结论**:
- `agent-backend-system` 不能假设精灵卡片总能从外部 CDN 加载脚本。
- 对 `spirit-card-system` 的接口必须支持“纯 HTML/CSS + 可选图表增强”策略；若 same-origin 未开启，图表应允许优雅降级为纯数值展示。

---

## 4. 方案清单

| 方案 | 描述 | 可行性 | 风险 | 推荐度 |
|------|------|:------:|:----:|:------:|
| A | FastAPI + `StreamingResponse` 手工 OpenAI SSE framing + 自定义内存 Session Store | 高 | 中 | ⭐⭐⭐⭐⭐ |
| B | FastAPI + `EventSourceResponse` + SDK 默认对象序列化 | 中 | 中高 | ⭐⭐ |
| C | 直接暴露 Responses API，再由 Open WebUI 兼容 | 低 | 高 | ⭐ |
| D | 使用 `SQLiteSession` 统一会话实现 | 中 | 中 | ⭐⭐ |

**推荐**: 方案 A

---

## 5. 行动建议

| 优先级 | 建议 | 理由 |
|:------:|------|------|
| P0 | 实现 `GET /v1/models` + `POST /v1/chat/completions` | 这是 Open WebUI 接入最小可用契约 |
| P0 | Provider 固定 `use_responses=False` | 避免第三方 Provider 调用 `/responses` 失败 |
| P0 | Session key 使用 `user_id:chat_id` 组合 | 避免同一用户多对话串上下文 |
| P0 | 流式接口手工输出 OpenAI chunk 与 `[DONE]` | 保证协议兼容与可测试性 |
| P1 | 增加 session janitor 与最大会话数上限 | 避免内存泄漏 |
| P1 | 增加流前/流中错误映射测试 | 锁定兼容行为 |
| P2 | 为 v3+ 预留 Redis Session 接口 | 后续多 worker 横向扩展时平滑升级 |

---

## 6. 局限性与待探索

- OpenAI 官方 streaming 文档正文未能直接抓取，相关结论依赖搜索摘要与本地 SDK 源码交叉验证。
- 尚未对 Open WebUI Admin 注册自定义模型时的 UI 行为做浏览器实测。
- 尚未实测 Open WebUI 在 mid-stream error chunk 上的最终前端展示方式。
- 尚未验证所有 OpenRouter 多模态模型对 base64 data URL 的兼容差异。

---

## 7. 参考来源

1. FastAPI SSE 文档: https://fastapi.tiangolo.com/tutorial/server-sent-events/ （访问于 2026-04-07）
2. OpenAI Agents SDK Models 文档: https://openai.github.io/openai-agents-python/models/ （访问于 2026-04-07）
3. Open WebUI Rich UI 文档: https://docs.openwebui.com/features/extensibility/plugin/development/rich-ui/ （访问于 2026-04-07）
4. OpenRouter Streaming 文档: https://openrouter.ai/docs/api/reference/streaming （访问于 2026-04-07）
5. OpenAI Streaming 文档入口: https://developers.openai.com/api/docs/guides/streaming-responses （访问于 2026-04-07，正文抓取 403）
6. 本地源码: `d:\PROJECTALL\ROCO\references\open-webui\backend\open_webui\routers\openai.py`
7. 本地源码: `d:\PROJECTALL\ROCO\references\open-webui\backend\open_webui\env.py`
8. 本地源码: `d:\PROJECTALL\ROCO\references\open-webui\backend\open_webui\utils\headers.py`
9. 本地源码: `d:\PROJECTALL\ROCO\references\openai-agents-python\src\agents\models\openai_provider.py`
10. 本地源码: `d:\PROJECTALL\ROCO\references\openai-agents-python\src\agents\models\openai_chatcompletions.py`
11. 本地源码: `d:\PROJECTALL\ROCO\references\openai-agents-python\src\agents\memory\session.py`
12. 本地源码: `d:\PROJECTALL\ROCO\references\openai-agents-python\src\agents\memory\sqlite_session.py`
