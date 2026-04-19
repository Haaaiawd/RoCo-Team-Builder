# AGENTS.md - AI 协作协议

> **"如果你正在阅读此文档，你就是那个智能体 (The Intelligence)。"**
> 
> 这个文件是你的**锚点 (Anchor)**。它定义了项目的法则、领地的地图，以及记忆协议。
> 当你唤醒（开始新会话）时，**请首先阅读此文件**。

---

## 🧠 30秒恢复协议 (Quick Recovery)

**当你开始新会话或感到"迷失"时，立即执行**:

1. **读取根目录的 AGENTS.md** → 获取项目地图
2. **查看下方"当前状态"** → 找到最新架构版本
3. **读取 `.anws/v{N}/05_TASKS.md`** → 了解当前待办
4. **开始工作**

---

## 🗺️ 地图 (领地感知)

以下是这个项目的组织方式：

| 路径 | 描述 | 访问协议 |
|------|------|----------|
| `src/` | **实现层**。实际的代码库。 | 通过 Task 读/写。 |
| `.anws/` | **统一架构根目录**。包含版本化架构状态与升级记录。 | **只读**(旧版) / **写一次**(新版) / `changelog` 由 CLI 维护。 |
| `.anws/v{N}/` | **当前真理**。最新的架构定义。 | 永远寻找最大的 `v{N}`。 |
| `.anws/changelog/` | **升级记录**。`anws update` 生成的变更记录。 | 由 CLI 自动维护，请勿删除。 |
| `target-specific workflow projection` | **工作流**。`/genesis`, `/blueprint` 等。 | 读取当前 target 对应的原生投影文件。 |
| `target-specific skill projection` | **技能库**。原子能力。 | 调用当前 target 对应的原生投影文件。 |
| `.nexus-map/` | **知识库**。代码库结构映射。 | 由 nexus-mapper 生成。 |

## 🛠️ 工作流注册表

> [!IMPORTANT]
> **工作流优先原则**：当任务匹配某个工作流，或你判断当前任务**明显符合、基本符合、甚至只是疑似符合**某个工作流的适用场景时，**都必须先读取相应文件**，并严格遵循其中的步骤执行。工作流是经过精心设计的协议，而非可选参考。
>
> **触发流程**：
> 1. 用户提及工作流名称，或你判断当前任务明显符合、基本符合、甚至只是疑似符合某个工作流的适用场景时，都必须先读取相应文件
> 2. **立即读取** 相应工作流文件
> 3. **严格遵循**工作流中的步骤执行
> 4. 在检查点暂停等待用户确认

| 工作流 | 触发时机 | 产出 |
|--------|---------|------|
| `/quickstart` | 新用户入口 / 不知道从哪开始 | 编排其他工作流 |
| `/genesis` | 新项目 / 重大重构 | PRD, Architecture, ADRs |
| `/probe` | 变更前 / 接手项目 | `.anws/v{N}/00_PROBE_REPORT.md` |
| `/design-system` | genesis 后 | 04_SYSTEM_DESIGN/*.md |
| `/blueprint` | genesis 后 | 05_TASKS.md + AGENTS.md 初始 Wave |
| `/change` | 进入 forge 编码后的任务局部修订 | 更新 TASKS + SYSTEM_DESIGN (仅修改) + CHANGELOG |
| `/explore` | 调研时 | 探索报告 |
| `/challenge` | 决策前质疑 | 07_CHALLENGE_REPORT.md (含问题总览目录) |
| `/forge` | 编码执行 | 代码 + 更新 AGENTS.md Wave 块 |
| `/craft` | 创建工作流/技能/提示词 | Workflow / Skill / Prompt 文档 |
| `/upgrade` | `anws update` 后做升级编排 | 判断 Minor / Major，并路由到 `/change` 或 `/genesis` |

---

## 📜 宪法 (The Constitution)

1. **版本即法律**: 不"修补"架构文档，只"演进"。变更必须创建新版本。
2. **显式上下文**: 决策写入 ADR，不留在"聊天记忆"里。
3. **交叉验证**: 编码前对照 `05_TASKS.md`。我在做计划好的事吗？
4. **美学**: 文档应该是美的。善用 Markdown 和 Emoji。

---
## 🔄 项目状态保留区

<!-- AUTO:BEGIN — 项目状态保留区（升级时唯一保留的部分，请勿手动修改区块边界） -->

## 📍 当前状态 (由 Workflow 自动更新)

> **注意**: 这是项目文件中的保留部分，由 `/genesis`、`/blueprint` 和 `/forge` 自动维护。

- **最新架构版本**: `.anws/v3`
- **活动任务清单**: `.anws/v3/05_TASKS.md`
- **待办任务数**: 20
- **最近一次更新**: `2026-04-19 — v3 Blueprint 完成：05_TASKS.md 已生成，Sprint / INT / User Story Overlay 已落盘`

### 🌱 Genesis v3 — 配队工作台闭环架构 (COMPLETED)
- `01_PRD.md` ✅：双入口工作台、单草稿、JSON 主格式、站内摘要 + Wiki 深读、AI 分析评价与建议
- `02_ARCHITECTURE_OVERVIEW.md` ✅：维持 4 系统边界，新增 `Team Workbench Host / Hand-off Layer`
- `ADR_001_TECH_STACK.md` ✅：v3 采用“现有系统内结构升级”而非新增独立工作台系统
- `ADR_005_WORKBENCH_SHARED_CONTRACT.md` ✅：定义 `TeamDraft / HandOff / ImportExport` 共享契约与 JSON 版本策略
- `_research/genesis-team-workbench-research.md` ✅：完成对 `rocom.aoe.top` 与前端最佳实践的研究收敛

---
> **注意**: 此部分由 `/genesis` 维护。

- **架构总览**: `.anws/v3/02_ARCHITECTURE_OVERVIEW.md`
- **ADR**: `.anws/v3/03_ADR/` (跨系统决策的唯一记录源)
- **研究结论**: `.anws/v3/04_SYSTEM_DESIGN/_research/genesis-team-workbench-research.md`
- **详细设计**:
  - `web-ui-system`: 源码 `src/web-ui-shell/` → 设计 `.anws/v3/04_SYSTEM_DESIGN/web-ui-system.md`（待 /design-system 校准）
  - `agent-backend-system`: 源码 `src/agent-backend/` → 设计 `.anws/v3/04_SYSTEM_DESIGN/agent-backend-system.md`（待 /design-system 校准）
  - `data-layer-system`: 源码 `src/data-layer/` → 设计 `.anws/v3/04_SYSTEM_DESIGN/data-layer-system.md`（待 /design-system 校准）
  - `spirit-card-system`: 源码 `src/spirit-card/` → 设计 `.anws/v3/04_SYSTEM_DESIGN/spirit-card-system.md`（待 /design-system 校准）
- **任务清单**: `.anws/v3/05_TASKS.md`

### ADR ↔ SYSTEM_DESIGN 关系
- **ADR** 记录跨系统决策（如技术栈、工作台共享契约）
- **SYSTEM_DESIGN** §8 Trade-offs 引用 ADR，不复制决策内容
- 修改 ADR 时，检查“影响范围”章节，确认引用该 ADR 的系统

### 技术栈决策
- **Web UI**: Open WebUI 受控壳层 + Team Workbench Host
- **Agent 后端**: OpenAI Agents SDK + FastAPI（Python 3.11）
- **数据层**: httpx + cachetools + 静态知识 + Team Analysis
- **精灵卡片**: Jinja2 HTML + Summary Card Mode
- **部署**: Docker Compose

### 系统边界
- `web-ui-system`: 双入口工作台、壳层导航、BYOK 受限直连、工作台动作编排
- `agent-backend-system`: Agent 推理、Workbench Hand-off、AI 分析评价与建议
- `data-layer-system`: 精灵结构化资料、Wiki 标识、队伍级结构化分析真理源
- `spirit-card-system`: 聊天卡片与工作台摘要卡片统一渲染层

### 当前任务状态
- 任务清单: `.anws/v3/05_TASKS.md`
- 当前阶段: v3 `/forge` Wave 1 执行中
- 最近更新: 2026-04-19 v3 Blueprint 落盘

### 🌊 Wave 1 — 共享契约与真理源收口 ✅
T1.1.1, T1.1.2, T2.1.1 (Completed 2026-04-19)

### 🌊 Wave 2 — Wiki 标识与摘要字段对齐 ✅
T1.2.1 (Completed 2026-04-19)

### 🌊 Wave 3 — Summary Card Mode 展示字段 ✅
T2.1.2 (Completed 2026-04-19)

### 🌊 Wave 4 — 卡片渲染契约测试与降级测试 ✅
T2.2.1 (Completed 2026-04-19)

### 🌊 Wave 5 — S1 集成验证 (Milestone) ✅
INT-S1 (Completed 2026-04-19)

<!-- AUTO:END -->

---
> **状态自检**: 准备好了？提醒用户运行 `/quickstart` 开始吧。
