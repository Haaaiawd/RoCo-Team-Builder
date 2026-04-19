# ADR-001: 技术栈选择

**状态**: Accepted
**日期**: 2026-04-07
**决策者**: 项目创始人

---

## 背景

「洛克王国世界配队 Agent」是一个面向公网用户的 AI 问答应用，具备以下核心约束：

1. **多用户并发访问**，需要会话隔离
2. **BYOK（用户自带 API Key）**，Key 不得经过或存储在服务端
3. **多模态输入**（截图识别），需要支持视觉模型
4. **工具调用可视化**，用户需要看到 Agent 的推理过程
5. **Rich UI 精灵卡片**，工具调用结果需要以自定义 UI 呈现
6. **Docker 部署**，个人开发者维护，追求低运维复杂度
7. **个人独立开发**，Python 技术栈，学习成本是约束

---

## 决策

### 🏗️ Agent 后端框架：**OpenAI Agents SDK**

**GitHub**: `openai/openai-agents-python` ⭐19k（2025-03 发布）

### 🖥️ Web UI 框架：**Open WebUI**

**GitHub**: `open-webui/open-webui` ⭐129k

### 🔑 BYOK 实现方案：**Open WebUI Direct Connections + OpenRouter 推荐**

用户在前端配置 API Key，Key 存 `localStorage`，通过 Open WebUI Direct Connections 直接从浏览器发往 LLM Provider；推荐用户使用 OpenRouter 作为统一入口（解决 CORS 问题，支持 200+ 模型）。

### 🌐 LLM Provider 路由：**OpenRouter（推荐）/ 任意 OpenAI 兼容端点**

---

## 候选方案对比

### Agent 后端框架

| 候选 | 加权总分(/125) | 优势 | 劣势 |
|------|:------------:|------|------|
| **OpenAI Agents SDK** ✅ | 115 | 最轻量，code-first，provider-agnostic，低学习曲线 | 2025年发布，相对较新 |
| LangGraph | 88 | 企业级，状态图强大 | 概念重，过度工程化 |
| CrewAI | 96 | 多 Agent 协作友好 | 角色扮演范式与本项目不匹配 |

### Web UI 框架

| 候选 | 加权总分(/135) | 优势 | 劣势 |
|------|:------------:|------|------|
| **Open WebUI** ✅ | 126 | BYOK 原生支持（Direct Connections），Rich UI 嵌入，Docker 一键部署，129k stars 社区 | Python Tools 插件集成需适配 |
| Chainlit | 96 | 纯 Python，工具调用 `@cl.step` 可视化天然友好 | BYOK 需自行实现，无内置用户管理 |
| 自建 Next.js | 99 | 完全自定义 | 开发量 ×5，运维复杂度高 |

### BYOK 实现路径

| 方案 | 加权总分(/90) | 优势 | 劣势 |
|------|:------------:|------|------|
| **Open WebUI Direct Connections + OpenRouter** ✅ | 90 | Key 不经服务端，原生支持，OpenRouter 解决 CORS | 用户需注册 OpenRouter（轻微门槛） |
| 无状态后端代理（自建） | 76 | 提供商兼容性最高 | Key 必须经过服务端（即使不存储，安全风险更高） |
| 直连官方 OpenAI | 70 | 最直接 | 官方 OpenAI API 有 CORS 限制，浏览器直连失败 |

---

## 权衡点（ATAM 分析）

### TP-1：Open WebUI 工具调用集成复杂度
- **风险**: Open WebUI 的 Tools 是插件系统，与 OpenAI Agents SDK 的 Agent 运行时并非天然一体
- **缓解**: OpenAI Agents SDK 作为独立后端服务运行，通过 OpenAI 兼容 API 暴露给 Open WebUI；Open WebUI 将其注册为自定义模型端点
- **替代触发条件**: 如果集成复杂度超出预期，可切换到 Chainlit（纯 Python 深度集成更直接）

### TP-2：BYOK 与 CORS
- **风险**: 官方 OpenAI API 不支持浏览器直连（CORS 限制），Direct Connections 对严格 Provider 失效
- **缓解**: 推荐用户使用 **OpenRouter**（`https://openrouter.ai/api/v1`）作为统一入口，天然支持 CORS，兼容 200+ 模型（包括 GPT-4o、Gemini、Claude、DeepSeek 等）
- **用户指引**: 在 UI 中提供 OpenRouter 配置教程

### TP-3：内置模型 Key 防薅
- **风险**: 公开 Web 应用，内置模型 API Key 可能被大量调用导致费用失控
- **缓解**: 
  - Open WebUI 支持 Admin 设置每用户 Token 配额
  - 或通过 LiteLLM Proxy 做统一限流（作为内置模型轨道的中间层）
  - 超出配额时引导用户使用 BYOK

---

## 最终技术栈全景

```
用户浏览器 (Chrome/Firefox/Safari)
    │
    ├─ [BYOK 路径] → 用户自配 API Key (localStorage) → OpenRouter → LLM Provider
    │
    └─ [内置路径] → Open WebUI 服务端 → 内置 API Key → LLM Provider
         │
         ↓
    Open WebUI (Docker, Port 3000)
    ├─ 对话 UI（ChatGPT 风格）
    ├─ Rich UI（精灵卡片 HTML/iframe 内嵌）
    ├─ Direct Connections（BYOK 管理）
    └─ 注册自定义端点 → Agent 后端服务
              │
              ↓
    OpenAI Agents SDK 后端 (FastAPI, Port 8000)
    ├─ Agent 主循环（多轮对话，上下文管理）
    ├─ get_spirit_info → BWIKI MediaWiki API + 本地缓存
    ├─ get_type_matchup → 本地 JSON（17×17 克制矩阵）
    ├─ suggest_team → LLM 推理
    ├─ adjust_team_skills → LLM 推理 + BWIKI
    └─ search_wiki → BWIKI MediaWiki API
              │
              ↓
    BWIKI (wiki.biligame.com/rocom/api.php)
    本地缓存层 (Redis 或内存 TTL Cache)
```

---

## 后果

### 正面
- Open WebUI BYOK（Direct Connections）完全满足"Key 不上服务端"要求，且已有官方文档支撑
- OpenRouter 作为 CORS 代理层，用户可用任意主流模型（GPT-4o/Gemini/Claude/DeepSeek），解耦 LLM Provider
- OpenAI Agents SDK 轻量，Agent 逻辑代码量少，维护成本低
- Docker Compose 可将 Open WebUI + Agent 后端打包为一键部署

### 负面
- Open WebUI + OpenAI Agents SDK 需要自定义集成（非零代码量）
- 用户使用 BYOK 需注册 OpenRouter（轻微门槛，但推荐）
- Open WebUI 是 JavaScript/Python 混合项目，深度定制 UI 需了解其前端结构

### 需要的后续行动
- [ ] ADR-002：数据层设计（BWIKI 缓存策略、精灵数据模型）
- [ ] ADR-003：Agent 与 Open WebUI 集成方案（Tools 插件 vs OpenAI 兼容端点）
- [ ] 验证 OpenRouter CORS 支持（实测 Direct Connections + OpenRouter 端点）
- [ ] 评估内置模型轨道是否需要 LiteLLM Proxy 做限流
