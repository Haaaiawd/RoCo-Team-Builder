# ADR-003: 会话上下文管理策略

**状态**: Accepted
**日期**: 2026-04-07
**决策者**: 项目创始人

---

## 背景

`agent-backend-system` 需要在多轮对话中维护上下文（已确认的精灵列表、当前配队方案、用户偏好等）。OpenAI Agents SDK 提供多种 Session 实现，选型影响：
1. Docker Compose 配置（是否需要持久化存储）
2. 会话数据安全（PRD 要求"会话结束即清除"）
3. 多 worker 兼容性
4. 上下文窗口超限时的处理策略

---

## 决策

**v1 使用 Agents SDK 内存 `Session`（非持久化），单进程部署（uvicorn `--workers 1`）。**

会话 key：Open WebUI 转发的 `X-OpenWebUI-User-Id` header（或 chat_id）
会话生命周期：随进程内存存在，进程重启或用户长时间无操作（30分钟）后清除
上下文压缩：**不做自动压缩**，通过系统提示词约束 Agent 输出简洁，避免上下文膨胀

---

## 候选方案对比

| 方案 | 优势 | 劣势 |
|------|------|------|
| **内存 Session（无持久化）** ✅ | 零依赖，天然满足"会话结束即清除"，实现最简单 | 进程重启后丢失，不跨 worker |
| `SQLiteSession` | 跨重启持久化，会话可恢复 | 引入文件系统依赖，违反 PRD"不持久化用户数据"原则 |
| `OpenAIResponsesCompactionSession` | 自动压缩长对话历史，超长会话不截断 | 仅兼容 OpenAI Responses API，不兼容第三方 LLM（OpenRouter 等）⚠️ |
| Redis + 自定义 Session | 跨进程共享，横向扩展 | 引入 Redis 依赖，v1 过度工程化 |

---

## 权衡点

### TP-1: `OpenAIResponsesCompactionSession` 的兼容性陷阱
Agents SDK 源码确认：`OpenAIResponsesCompactionSession` 依赖 `/responses` API endpoint，而 OpenRouter 等第三方 Provider 仅支持 `/chat/completions`。我们的 BYOK 轨道允许用户接任意 Provider，因此**不能**将 Compaction Session 作为默认实现。

### TP-2: 上下文超限的处理
在不使用 Compaction 的情况下，对话轮数过多时上下文会超出模型窗口。缓解策略：
- Agent System Prompt 约束每轮回复简洁
- 工具调用返回精简结构化数据（不返回全文 wikitext）
- PRD US-005 的边界条件"自动压缩"在 v1 退化为：**超限时提示用户开启新对话**

### TP-3: 会话隔离实现
Open WebUI 通过 `ENABLE_FORWARD_USER_INFO_HEADERS=true` 在请求 header 中携带 `X-OpenWebUI-User-Id`。Agent 后端以此作为内存 Session 的隔离 key，不需要自己管理 token 认证。

---

## 后果

### 正面
- 完全满足 PRD NG2（不做用户账号体系）和数据安全要求（不持久化）
- 无额外基础设施依赖，Docker Compose 保持两服务
- 任意 LLM Provider 均兼容（无 Responses API 依赖）

### 负面
- 单 worker 约束：uvicorn 必须以 `--workers 1` 启动，否则不同 worker 进程间 session 不共享
- 进程重启（如 `docker restart`）导致所有进行中会话丢失
- 长对话（>20轮）可能触发上下文超限，需用户主动新开对话

### 升级路径（v2）
如需支持多 worker 或会话恢复，将 Session 后端替换为 Redis 自定义实现，仍以 `X-OpenWebUI-User-Id` 作为 key。`agent-backend-system` 接口层不变。
