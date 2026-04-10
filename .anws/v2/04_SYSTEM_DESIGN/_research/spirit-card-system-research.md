# 探索报告: spirit-card-system

**日期**: 2026-04-07
**探索者**: Cascade / Explorer
**系统**: `spirit-card-system`

---

## 1. 问题与范围

**核心问题**: 如何为 `spirit-card-system` 设计一个既能在 Open WebUI Rich UI 中呈现精灵资料卡片、又不会被 iframe sandbox 和上游不稳定输入拖垮的受控渲染系统，同时保证在富展示失败时用户仍能得到可操作的信息。

**探索范围**:
- 包含: Rich UI iframe 约束、Jinja2 模板生成、图表增强与文本降级、与 `agent-backend-system` / `data-layer-system` 的契约边界、卡片安全策略
- 不包含: `data-layer-system` 的 BWIKI 抓取与缓存实现、`agent-backend-system` 的流式协议细节、`web-ui-system` 的导航壳层裁剪

---

## 2. 核心洞察 (Key Insights)

1. **`spirit-card-system` 的本质不是“做得好看”，而是“稳定地把结构化资料转成可消费的富展示产物”**: PRD 的 [REQ-004] 要求在对话中展示精灵卡片，这使它成为一条真实产品链路，而不是装饰性 UI。
2. **Rich UI 必须被视为增强层，不是唯一展示路径**: Open WebUI Rich UI 运行在 sandboxed iframe 中，能力受宿主限制；因此卡片系统必须与富展示同时产出 fallback 文本，而不是在失败后临时补救。
3. **卡片系统只能消费结构化领域对象，不能直接消费 wiki 原始 HTML**: 原始页面结构不稳定、存在噪声和安全风险，而结构化对象更适合作为稳定契约。
4. **Chart.js 适合做种族值增强展示，但不能成为核心信息承载体**: 种族值的本质是 6 维数字，不是图表动画；图表失败时仍应保留数值网格。
5. **服务端模板渲染比“后端 JSON + 宿主前端拼 DOM”更符合当前边界**: `web-ui-system` 的职责是宿主，不应理解精灵卡片内部视觉逻辑；由卡片系统统一产出 HTML 更简单、更可控。

---

## 3. 详细发现

### 3.1 PRD 已把卡片 UI 变成刚性需求

**探索方式**: 🔍 PRD

**发现**:
- [REQ-004] 明确要求用户查询单只精灵资料时，系统不仅要返回种族值、技能、血脉、进化链和 BWIKI 链接，还要“在对话中展示精灵卡片 UI”。
- PRD 的完成标准进一步要求精灵卡片 UI 在 Chrome/Firefox/Safari 均正常渲染。

**结论**:
- `spirit-card-system` 不是附属视图，而是 [REQ-004] 验收的一部分。
- 该系统必须有独立的输入输出契约、测试策略和降级设计。

### 3.2 Architecture Overview 已明确输入输出边界

**探索方式**: 🔍 Architecture Overview

**发现**:
- `spirit-card-system` 的输入被定义为“精灵结构化数据（JSON）”，输出为“HTML 字符串”。
- 依赖关系明确为 `agent-backend-system` 和 `data-layer-system` 的下游，而非直接对接 BWIKI。

**结论**:
- 卡片系统应保持纯展示系统边界：只处理结构化数据到渲染产物的转换。
- 若它开始直接抓 BWIKI 或参与 Agent 推理，就会打穿现有架构分层。

### 3.3 Open WebUI Rich UI 对卡片设计形成反向约束

**探索方式**: 🔍 官方文档 + 现有系统研究文档

**发现**:
- Open WebUI Rich UI 通过 sandboxed iframe 承载富展示，脚本执行、same-origin 和父子通信均受宿主条件影响。
- 现有 `web-ui-system` / `agent-backend-system` 研究已经确认：图表和增强交互不能被视为必然能力。

**结论**:
- `spirit-card-system` 的首要目标是“信息保真 + 可读”，而不是“强交互”。
- 所有增强能力都必须有文本和数值级别的降级方案。

### 3.4 Jinja2 是 v2 最合适的模板生成方式

**探索方式**: 🔍 ADR + 技术栈约束

**发现**:
- Architecture Overview 已把 `spirit-card-system` 技术栈写为 “Jinja2 HTML 或等效字符串模板”。
- 项目整体后端基于 Python，`agent-backend-system` 也以 Python 为主。

**结论**:
- Jinja2 允许在当前技术栈内最小成本地完成模板生成。
- 与自建前端组件、SSR 服务或 JSON-to-DOM 协议相比，Jinja2 更符合 v2 简单优先原则。

### 3.5 图表增强应是可选项而非基础依赖

**探索方式**: 🔍 PRD + Rich UI 文档

**发现**:
- PRD 提到精灵卡片应展示“种族值数值/图表”，表述上已经把“数值”置于前位，并未要求图表是唯一形态。
- Rich UI 文档说明 Chart.js 等增强能力和宿主策略相关，不应无条件假设可用。

**结论**:
- 最稳妥的设计是：服务端始终输出数值视图；当宿主能力允许时，再附加 Chart.js 增强。
- 这样能避免图表失败导致卡片核心价值丢失。

### 3.6 安全边界必须收紧到“结构化字段 + 白名单链接”

**探索方式**: 🔍 架构分析

**发现**:
- 如果把来自外部 wiki 的原始 HTML 或富文本不加控制地拼入模板，等价于把不受控内容塞进 Rich UI iframe。
- 即使 iframe 有 sandbox，这也会放大模板污染、错误排版和潜在脚本风险。

**结论**:
- `spirit-card-system` 应只接受结构化字段，并在渲染前统一做 escape 和链接协议校验。
- BWIKI 跳转应保留，但必须约束为受控 `https://wiki.biligame.com/...`。

---

## 4. 方案清单

| 方案 | 描述 | 可行性 | 风险 | 推荐度 |
|------|------|:------:|:----:|:------:|
| A | Jinja2 服务端模板 + Rich UI HTML + 同步生成 fallback 文本 + 可选 Chart.js 增强 | 高 | 低中 | ⭐⭐⭐⭐⭐ |
| B | 后端只返回 JSON，由 `web-ui-system` 宿主前端拼装卡片 | 中 | 中 | ⭐⭐ |
| C | 直接嵌入 wiki 原始 HTML/页面片段 | 低 | 高 | ⭐ |
| D | 独立前端微应用专门渲染卡片 | 中 | 中高 | ⭐⭐ |

**推荐**: 方案 A

---

## 5. 行动建议

| 优先级 | 建议 | 理由 |
|:------:|------|------|
| P0 | 定义 `RenderedSpiritCard` 契约，至少包含 `html` 与 `fallback_text` | 锁定降级路径，避免宿主异常时整条链路断裂 |
| P0 | 只接受 `data-layer-system` 的结构化对象作为输入 | 守住展示系统边界 |
| P0 | 所有文本字段统一 escape，所有跳转链接做白名单校验 | 避免不可信内容进入卡片 |
| P0 | 把种族值数值展示作为基础能力，把图表视为可选增强 | 满足可读性优先原则 |
| P1 | 为模板输出建立 DOM 级契约测试 | 防止后续改版破坏核心字段显示 |
| P1 | 记录 Rich UI 降级次数和渲染错误次数 | 为后续宿主兼容性优化提供数据 |
| P2 | 若未来出现更多卡片类型，再评估抽象为通用 card renderer | 避免 v2 过度工程化 |

---

## 6. 局限性与待探索

- 尚未在真实 Open WebUI 页面中逐浏览器实测同一份卡片 HTML 的最终视觉表现。
- 尚未验证 `allowSameOrigin` 开/关两种模式下 Chart.js 增强的全部边界行为。
- 当前结论默认卡片以单精灵资料展示为主，尚未覆盖“对比卡片”“队伍卡片”等未来形态。
- 尚未形成最终视觉规范（颜色 token、移动端排版细则），这应在 `/forge` 编码阶段基于真实样例再收敛。

---

## 7. 参考来源

1. PRD: `d:\PROJECTALL\ROCO\.anws\v2\01_PRD.md`
2. Architecture Overview: `d:\PROJECTALL\ROCO\.anws\v2\02_ARCHITECTURE_OVERVIEW.md`
3. ADR-001: `d:\PROJECTALL\ROCO\.anws\v2\03_ADR\ADR_001_TECH_STACK.md`
4. ADR-004: `d:\PROJECTALL\ROCO\.anws\v2\03_ADR\ADR_004_WEB_UI_PRUNING_STRATEGY.md`
5. Open WebUI Rich UI: https://docs.openwebui.com/features/extensibility/plugin/development/rich-ui/ （访问于 2026-04-07）
6. Jinja2 Documentation: https://jinja.palletsprojects.com/en/stable/ （访问于 2026-04-07）
7. Chart.js Documentation: https://www.chartjs.org/docs/latest/ （访问于 2026-04-07）
8. 本地参考: `d:\PROJECTALL\ROCO\.anws\v2\04_SYSTEM_DESIGN\web-ui-system.md`
9. 本地参考: `d:\PROJECTALL\ROCO\.anws\v2\04_SYSTEM_DESIGN\agent-backend-system.md`
10. 本地参考: `d:\PROJECTALL\ROCO\.anws\v2\04_SYSTEM_DESIGN\data-layer-system.md`
