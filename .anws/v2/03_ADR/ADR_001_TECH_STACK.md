# ADR-001: 技术栈选择（v2）

**状态**: Accepted
**日期**: 2026-04-07
**决策者**: 项目创始人

---

## 背景

RoCo Team Builder 是一个面向公网用户的垂类 AI 产品，而不是通用 AI 平台。v2 对技术栈的核心修正不在 Agent 后端，而在前端定位：

1. 需要多用户并发访问与会话隔离
2. 需要 BYOK（用户自带 API Key）且 Key 不经过服务端
3. 需要多模态输入（截图识别）
4. 需要工具调用可视化与 Rich UI 精灵卡片
5. 需要低运维复杂度、个人开发者可维护
6. **需要一个聚焦配队场景的产品前端，而不是开放式通用 AI 工作台**

---

## 决策

### Agent 后端框架
**选择**: OpenAI Agents SDK + FastAPI

### Web UI 基座
**选择**: Open WebUI，作为**受控产品壳层的基座**，而不是原样暴露的全量平台。

### BYOK 实现方案
**选择**: Open WebUI Direct Connections + OpenRouter 推荐

### LLM Provider 路由
**选择**: OpenRouter（推荐）/ 任意 OpenAI 兼容端点

### 标准部署基线
**选择**: Docker Compose 作为 v2 的唯一标准部署基线

### 部署拓扑约束
**选择**: v2 默认不引入 Redis / DB / K8s / 额外基础设施作为默认前提

---

## 候选方案对比

### Web UI 基座方案

| 候选 | 优势 | 劣势 | 结论 |
|------|------|------|------|
| **Open WebUI 作为受控壳层** | BYOK、Rich UI、模型接入、Docker 部署能力成熟，可在已有基础上裁剪 | 需要理解并处理原生信息架构，存在裁剪成本 | ✅ 采用 |
| Chainlit | 纯 Python，集成简单 | BYOK、Rich UI、产品壳层能力不如 Open WebUI 丰富 | 不采用 |
| 自建 Next.js 前端 | 完全可控 | 开发量和维护成本显著上升 | 当前不采用 |

### Agent 后端方案

| 候选 | 优势 | 劣势 | 结论 |
|------|------|------|------|
| **OpenAI Agents SDK** | 轻量、provider-agnostic、tool orchestration 直接 | 生态较新 | ✅ 采用 |
| LangGraph | 状态图强大 | 概念重，对当前项目过度工程化 | 不采用 |
| CrewAI | 多 Agent 协作友好 | 与本项目单主 Agent 场景不完全匹配 | 不采用 |

---

## 权衡点

### TP-1: Open WebUI 的平台性 vs 产品聚焦性
- **风险**: Open WebUI 是通用 AI 前端，默认信息架构远大于本产品需求。
- **缓解**: 不把 Open WebUI 当最终产品，而是当作“可裁剪壳层基座”；终端用户只暴露保留能力。

### TP-2: 自建前端的高控制力 vs 成本
- **风险**: 自建前端虽然最可控，但会把当前项目重心从产品验证转移到基础设施重复建设。
- **缓解**: v2 先采用 Open WebUI 壳层化；当裁剪成本反向超过自建成本时，再评估迁移。

### TP-3: BYOK 与 CORS
- **风险**: 官方 OpenAI API 不适合浏览器直连。
- **缓解**: 推荐 OpenRouter 作为统一入口。

### TP-4: 前端裁剪工作量被低估
- **风险**: 如果仍把前端视为“配置文档”，将导致产品壳层、导航、能力暴露和回归验证无人负责。
- **缓解**: 在 v2 中正式将 `web-ui-system` 提升为核心系统，并新增专门 ADR 约束裁剪策略。

### TP-5: 为什么要定义“唯一标准部署基线”
- **风险**: 若同时把单机 Docker、手工启动、K8s、多副本都写成等价支持路径，交付文档、验收标准和问题定位会立刻分叉。
- **缓解**: v2 统一以 Docker Compose 作为唯一标准部署基线；更复杂拓扑留到后续版本再评估。

---

## 后果

### 正面
- 继续保留 Open WebUI 在 BYOK、Rich UI、快速部署上的成熟能力
- 避免过早自建前端导致的开发量爆炸
- 正式承认前端壳层是架构问题，后续设计和实现不再漂移
- 部署文档、验收环境与问题定位基线可统一到 Docker Compose

### 负面
- 需要持续跟踪 Open WebUI 升级带来的默认入口回流风险
- 需要额外进行前端可见性回归测试，防止无关功能重新暴露
- 对上游项目结构存在一定认知依赖
- v2 默认不覆盖更复杂的生产拓扑

### 需要的后续行动
- [ ] 创建 `web-ui-system` 详细设计文档
- [ ] 建立终端用户可见能力白名单
- [ ] 建立 Open WebUI 升级后的前端回归检查清单
- [ ] 产出基于 Docker Compose 的标准部署文档与冷启动验收路径

## 参考来源

- Open WebUI 项目: https://github.com/open-webui/open-webui （访问于 2026-04-07）
- Open WebUI Rich UI 文档: https://docs.openwebui.com/features/extensibility/plugin/development/rich-ui/ （访问于 2026-04-07）
- OpenAI Agents SDK: https://github.com/openai/openai-agents-python （访问于 2026-04-07）
