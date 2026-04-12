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

- **最新架构版本**: `.anws/v2`
- **活动任务清单**: `.anws/v2/05_TASKS.md`
- **待办任务数**: `8`（Level 3: 8, INT: 0）
- **最近一次更新**: `2026-04-12 — Wave 4C Web UI 壳层基础完成: T4.2.2 (白名单导航裁剪与复古手账主题覆写)`

### ✅ Wave 1 — Data Spine 基础脊柱 (COMPLETED)
`T1.1.1` ✅, `T1.1.2` ✅, `T1.2.1` ✅

### ✅ Wave 2 — Static Knowledge + Card Skeleton (COMPLETED)
`T1.2.2` ✅, `T2.1.1` ✅

### 🌊 Wave 3 — Agent Backend Foundation (COMPLETED)
`T3.1.1` ✅, `T3.1.2` ✅, `T2.2.1` ✅, `T3.2.1` ✅, `T3.2.2` ✅, `T3.2.3` ✅, `T3.2.4` ✅

### 🔧 Phase 3 Integration (COMPLETED)
`T3.3.1` ✅, `T3.3.2` ✅

### ✅ Wave 4A — S3 集成验证 (COMPLETED)
`INT-S3` ✅ (206 passed, 4 skipped; 验证报告: .anws/v2/INT_S3_VERIFICATION_REPORT.md)

### ✅ Wave 4B — 后端集成验证 (COMPLETED)
`INT-S1` ✅ (48 passed; 验证报告: .anws/v2/INT_S1_VERIFICATION_REPORT.md)
`INT-S2` ✅ (62 passed; 验证报告: .anws/v2/INT_S2_VERIFICATION_REPORT.md)

### ✅ Wave 4C — Web UI 壳层基础 (COMPLETED)
`T4.1.1` ✅ (产品壳层骨架 + VisibleFeaturePolicy 真理源 + 复古冒险者手账风主题)
`T4.1.2` ✅ (接入内置轨道与 BYOK 双轨设置)
`T4.2.1` ✅ (打通聊天时间线、工具折叠卡片与 Rich UI 宿主)
`T4.2.2` ✅ (白名单导航裁剪与复古手账主题覆写)

### 🔧 Data-Layer Facade 接线修复 (COMPLETED)
`DataLayerFacade` 4 个 NotImplementedError 接通 + `search_spirits` 新实现 + `NameResolver.canonical_names` 属性

---

## 🌳 项目结构 (Project Tree)

> **注意**: 此部分由 `/genesis` 维护。

```text
src/
├── __init__.py
└── data_layer/             ← data-layer-system 实现
    ├── app/
    │   ├── contracts.py        ← IDataLayerFacade + 6 领域数据类
    │   ├── errors.py           ← 8 结构化错误类
    │   └── facade.py           ← Facade 骨架
    ├── cache/
    │   ├── registry.py         ← CacheRegistry (ADR-002)
    │   └── key_builder.py      ← 统一缓存键
    ├── spirits/
    │   ├── name_resolver.py    ← 三级名称解析
    │   ├── fuzzy_matcher.py    ← rapidfuzz 模糊匹配
    │   ├── alias_index.py      ← 别名索引
    │   └── repository.py       ← 精灵仓储
    ├── wiki/
    │   ├── gateway.py          ← httpx BWIKI 网关 (含速率限制+去重+退避)
    │   ├── parser.py           ← wikitext 解析器
    │   └── endpoint_builder.py ← URL/API 参数构造 (rocokingdomworld)
    └── static/
        ├── type_chart.py           ← TypeMatchupStore
        ├── mechanism_knowledge.py  ← StaticKnowledgeStore
        └── data/               ← 静态知识文件
            ├── type_chart.json     ← 属性克制矩阵
            ├── nature_chart.json   ← 性格加成表
            └── ATTRIBUTION.md      ← 数据来源声明
├── spirit_card/                ← spirit-card-system 实现
│   ├── app/
│   │   ├── contracts.py        ← SpiritCardModel + RenderPolicy + RenderedSpiritCard
│   │   ├── facade.py           ← SpiritCardFacade
│   │   └── render_policy.py    ← 策略工厂 + 配置常量
│   ├── mapping/
│   │   └── view_model_builder.py ← SpiritProfile → SpiritCardModel
│   ├── rendering/
│   │   ├── template_renderer.py ← Jinja2 渲染器 + 种族值可视化
│   │   ├── sanitization.py     ← 内容清洗 (HTML 转义 + URL 白名单)
│   │   ├── fallback_builder.py ← 文本降级构建器
│   │   └── templates/spirit_card.html ← 手账风卡片模板
│   └── assets/
│       └── inline_tokens.py    ← 设计 Token (roco_adventure_journal)
├── agent_backend/              ← agent-backend-system 实现
│   ├── api/
│   │   └── routes_openai.py    ← /v1/models + /healthz + /readyz
│   ├── app/
│   │   ├── model_catalog.py    ← 受控虚拟模型目录
│   │   ├── session_service.py  ← 会话键解析 + 内存 Registry + 闲置清理
│   │   └── request_context.py  ← ChatRequestContext
│   ├── runtime/                ← Agent SDK 运行时 (待实现)
│   ├── integrations/           ← 跨系统客户端 (待实现)
│   └── main.py                 ← FastAPI 应用入口

.anws/
├── changelog/              (升级记录)
├── v1/                     (上一版架构文档)
└── v2/                     (当前架构文档)
    ├── 00_MANIFEST.md      ✅
    ├── 01_PRD.md           ✅
    ├── 02_ARCHITECTURE_OVERVIEW.md  ✅
    ├── 03_ADR/
    │   ├── ADR_001_TECH_STACK.md    ✅
    │   ├── ADR_002_DATA_LAYER_CACHE.md ✅
    │   ├── ADR_003_SESSION_MANAGEMENT.md ✅
    │   └── ADR_004_WEB_UI_PRUNING_STRATEGY.md ✅
    ├── 04_SYSTEM_DESIGN/
    │   ├── agent-backend-system.md  ✅
    │   └── _research/agent-backend-system-research.md ✅
    ├── 05_TASKS.md         ✅
    └── 06_CHANGELOG.md     ✅

design.md                   (早期草稿，已被 .anws/v2 取代)
concept_model.json          → .anws/v2/concept_model.json
```

---

## 🧭 导航指南 (Navigation Guide)

> **注意**: 此部分由 `/genesis` 维护。

- **当前架构总览**: `.anws/v2/02_ARCHITECTURE_OVERVIEW.md`
- **ADR**: `.anws/v2/03_ADR/` (跨系统决策的唯一记录源)
- **详细设计**: `.anws/v2/04_SYSTEM_DESIGN/`
- **任务清单**: `.anws/v2/05_TASKS.md`
- **遇到架构问题**: 先查 `.anws/v2/03_ADR/`，再查对应 `04_SYSTEM_DESIGN/`

---

### 技术栈决策
- **Agent 后端**: OpenAI Agents SDK + FastAPI（Python 3.11）
- **Web UI**: Open WebUI（Docker）作为受控产品壳层，而非全量平台
- **BYOK**: Open WebUI Direct Connections + OpenRouter（Key 仅存 localStorage）
- **数据层**: httpx + cachetools（BWIKI API）
- **精灵卡片**: Jinja2 HTML + Chart.js（Open WebUI Rich UI 嵌入）
- **部署**: Docker Compose

### 系统边界
- `web-ui-system`: 基于 Open WebUI 的受控产品壳层，负责对话 UI、截图上传、BYOK 与终端用户能力收敛 — 详细设计见 `.anws/v2/04_SYSTEM_DESIGN/web-ui-system.md`
- `agent-backend-system`: FastAPI + Agents SDK，OpenAI 兼容接口、Agent 推理与工具调用编排 — 详细设计见 `.anws/v2/04_SYSTEM_DESIGN/agent-backend-system.md`
- `data-layer-system`: BWIKI 客户端 + 本地缓存 + 静态知识，负责名称解析与结构化数据适配 — 详细设计见 `.anws/v2/04_SYSTEM_DESIGN/data-layer-system.md`
- `spirit-card-system`: HTML 精灵卡片生成器

### 活跃 ADR
- **ADR-001**: 技术栈选型（OpenAI Agents SDK + Open WebUI 受控壳层 + OpenRouter BYOK）✅
- **ADR-002**: 数据层缓存策略（cachetools 内存 TTL Cache）✅
- **ADR-003**: 会话上下文管理（内存 Session + 单进程 + `user_id:chat_id`）✅
- **ADR-004**: Web UI 裁剪与收敛策略（能力白名单，终端用户不可见无关入口）✅

### 当前任务状态
- 任务清单: .anws/v2/05_TASKS.md
- 总任务数: 24, 已完成: 3, 待办: 21
- Sprint 数: 4
- Wave 1: ✅ 已完成 (T1.1.1, T1.1.2, T1.2.1)
- Wave 2 建议: T1.2.2, T2.1.1, T2.1.2
- 最近更新: 2026-04-10 Wave 1 完成

<!-- AUTO:END -->

---
> **状态自检**: 准备好了？提醒用户运行 `/quickstart` 开始吧。
