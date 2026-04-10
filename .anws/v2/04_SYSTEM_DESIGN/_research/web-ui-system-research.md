# 探索报告: web-ui-system

**日期**: 2026-04-07
**探索者**: Cascade / Explorer
**系统**: `web-ui-system`

---

## 1. 问题与范围

**核心问题**: 如何把 Open WebUI 从“通用 AI 平台”收敛为一个面向洛克王国世界配队场景的受控产品壳层，同时保留对话、截图上传、BYOK、Rich UI 展示和自定义 OpenAI 兼容后端接入能力。

**探索范围**:
- 包含: Open WebUI 的能力面、Direct Connections、管理员连接配置、自定义 OpenAI 兼容端点接入、Rich UI iframe 边界、品牌与产品壳层约束、升级回流风险
- 不包含: `agent-backend-system` 的推理编排细节、`data-layer-system` 的 BWIKI schema、`spirit-card-system` 的 HTML 视觉实现细节

---

## 2. 核心洞察 (Key Insights)

1. **Open WebUI 默认是平台，不是垂类产品**: 官方 Features 文档明确覆盖 Chat、Knowledge、Models & Agents、Notes、Channels、Open Terminal、Extensibility、Administration 等多类能力；这与本产品“单用途、低噪音、强聚焦”的前端目标天然冲突。
2. **`web-ui-system` 的核心不是“做 UI”，而是“控制能力暴露面”**: v2 最重要的设计对象是终端用户可见路径，而不是视觉主题本身。是否允许进入 Notes、Channels、Open Terminal、Knowledge、Admin 等入口，决定了产品边界是否成立。
3. **BYOK 在 Open WebUI 中是正式能力，不必自造协议**: 本地源码显示系统级和用户级都存在 Direct Connections 入口，配置核心是 `OPENAI_API_BASE_URLS`、`OPENAI_API_KEYS`、`OPENAI_API_CONFIGS`，并由 `features.enable_direct_connections` 控制启用。
4. **“内置模型轨道”与“BYOK 轨道”必须在壳层中被显式分离**: 内置轨道由管理员注册 `agent-backend-system` 作为 OpenAI 兼容连接；BYOK 轨道由用户在浏览器本地配置 Direct Connections。这两条链路的信任边界、故障模式和支持提示都不同，不能混成一个模糊入口。
5. **Rich UI 是产品差异化能力，但必须服从 sandbox 边界**: Open WebUI 的 Rich UI 通过 sandboxed iframe 嵌入，默认仅保证 `allow-scripts`、`allow-popups`、`allow-downloads`。与父页面的数据交互依赖 `postMessage` 和 payload 注入，某些增强能力还受 `allowSameOrigin` 影响。
6. **升级风险主要不是“代码跑不起来”，而是“被隐藏的入口重新出现”**: ADR-004 已指出上游升级会带来能力回流。对 `web-ui-system` 而言，最重要的回归验证不是 API，而是终端用户路径快照与白名单校验。
7. **品牌化必须克制**: Open WebUI 官方品牌规范强调产品名应正确指称为 “Open WebUI”；本项目应将其作为技术基座进行说明，而不是把终端产品命名混成 Open WebUI 变体。

---

## 3. 详细发现

### 3.1 Open WebUI 的默认能力面远大于本项目需求

**探索方式**: 🔍 官方文档

**发现**:
- Features 文档将 Open WebUI 描述为覆盖 Chat & Conversations、Knowledge & RAG、Models & Agents、Notes、Channels、Open Terminal、Extensibility、Authentication & Access、Administration 的统一平台。
- 这意味着默认信息架构天然面向“通用 AI 工作台”，而非垂类问答产品。

**结论**:
- `web-ui-system` 必须以“能力白名单”设计，而不是在默认全开的平台上被动隐藏几个按钮。
- 需要把“允许出现哪些能力”提升为一等架构对象。

### 3.2 Direct Connections 是 BYOK 的正式实现路径

**探索方式**: 🔍 本地源码核验

**发现**:
- `src/lib/stores/index.ts` 中存在 `config.features.enable_direct_connections`。
- `src/lib/components/admin/Settings/Connections.svelte` 提供系统级 OpenAI 连接管理和 `Direct Connections` 开关。
- `src/lib/components/chat/Settings/Connections.svelte` 提供用户侧 `Manage Direct Connections`，配置直接写入 `OPENAI_API_BASE_URLS`、`OPENAI_API_KEYS`、`OPENAI_API_CONFIGS`。
- 文案明确指出 Direct Connections 用于连接“用户自己的 OpenAI compatible API endpoints”，并要求 Provider 正确配置 CORS。

**结论**:
- 本项目的 BYOK 设计应直接建立在 Open WebUI Direct Connections 上。
- `web-ui-system` 需要提供一个“可见但受控”的 BYOK 入口，而不是重新发明 Key 管理机制。
- 对 BYOK 轨道需要显式提示: Key 仅保存在浏览器本地、Provider 必须允许浏览器跨域访问、推荐 OpenRouter 一类兼容入口。

### 3.3 系统级 OpenAI 连接可用于接入 `agent-backend-system`

**探索方式**: 🔍 本地源码核验

**发现**:
- `admin/Settings/Connections.svelte` 和 `lib/utils/connections.ts` 表明，Open WebUI 支持添加系统级 OpenAI 兼容连接，核心配置包含 URL、可选 key、config 对象。
- 连接列表采用数组和按索引映射的 config 结构。

**结论**:
- 管理员可将 `agent-backend-system` 注册为系统级 OpenAI 兼容端点，形成“内置模型轨道”。
- `web-ui-system` 不应让终端用户进入这类系统级配置路径；它属于管理员维护边界。

### 3.4 Rich UI 是可用能力，但受 iframe sandbox 约束

**探索方式**: 🔍 官方文档

**发现**:
- Rich UI 文档说明工具和动作都可返回 HTML/iframe 嵌入。
- 默认 sandbox flags 包含 `allow-scripts`、`allow-popups`、`allow-downloads`。
- iframe 可通过 `postMessage` 请求 payload；Tool embed 还可拿到 `window.args`。
- 当 `allowSameOrigin` 开启时，系统可按 HTML 特征自动注入 Chart.js / Alpine.js。

**结论**:
- `web-ui-system` 必须把 Rich UI 视为一级保留能力，因为精灵卡片和工具结果可视化直接依赖它。
- 但设计不能假设 same-origin 总是开启；所有富展示都必须支持“纯文本/纯数值”降级。
- 前端对工具结果的视觉增强应建立在“安全 sandbox + postMessage 协议 + 可降级”三原则之上。

### 3.5 产品壳层的关键问题是“主路径收敛”，不是“后台能力消失”

**探索方式**: 🔍 ADR + 本地源码核验

**发现**:
- ADR-004 明确区分“终端用户必须保留能力”“必须隐藏、禁用或不可达的能力”“管理员可保留但不得进入终端用户主路径的能力”。
- Open WebUI 本身包含管理员设置、广义平台功能和团队协作功能；这些能力很可能仍存在于代码与管理视图中。

**结论**:
- `web-ui-system` 的验收条件不是“上游功能全部被物理删除”，而是“终端用户主路径上不可见、不可达、不可误触”。
- 设计应明确三层控制手段：配置关闭、导航裁剪、访问控制/路径隔离。

### 3.6 回归测试必须以“入口快照”驱动

**探索方式**: 🔍 ADR + 架构分析

**发现**:
- ADR-004 已将“上游升级导致默认入口重新暴露”定义为主要风险。
- 这类问题往往不会出现在单元测试中，而会体现在首页、侧边栏、设置面板、聊天工具栏和模型选择器中。

**结论**:
- `web-ui-system` 需要一份明确的终端用户白名单与禁止入口清单。
- 发布前需要 UI 回归检查：主页、侧栏、顶部栏、聊天输入区、设置面板、空状态页、移动端导航都必须检查。

### 3.7 品牌表述应保持“产品名优先，技术基座退后”

**探索方式**: 🔍 官方品牌文档

**发现**:
- Open WebUI 品牌文档要求在引用品牌时使用“Open WebUI”标准写法，不应制造混合变体。

**结论**:
- 终端用户前台应以 `RoCo Team Builder` 为产品主名。
- 文档和部署说明中可以说明“基于 Open WebUI 构建”，但不应把终端产品命名与 Open WebUI 品牌混用。

---

## 4. 方案清单

| 方案 | 描述 | 可行性 | 风险 | 推荐度 |
|------|------|:------:|:----:|:------:|
| A | Open WebUI 受控壳层 + 能力白名单 + 双轨模型路由 + UI 回归清单 | 高 | 中 | ⭐⭐⭐⭐⭐ |
| B | Open WebUI 默认能力开放，仅做轻主题替换 | 高 | 高 | ⭐ |
| C | 彻底自建前端替代 Open WebUI | 中 | 中高 | ⭐⭐ |
| D | Open WebUI 仅作为管理员后台，终端用户前台另建最小壳层 | 中 | 中 | ⭐⭐⭐ |

**推荐**: 方案 A

---

## 5. 行动建议

| 优先级 | 建议 | 理由 |
|:------:|------|------|
| P0 | 定义终端用户能力白名单 | 这是产品边界的唯一可信基线 |
| P0 | 明确定义内置轨道与 BYOK 轨道的入口、提示和回退策略 | 避免用户理解混乱 |
| P0 | 将管理员连接配置与终端用户主路径彻底分离 | 避免误暴露系统级能力 |
| P0 | 将 Rich UI、截图上传、聊天输入列为不可裁掉的核心能力 | 直接支撑 REQ-001/002/004/006 |
| P1 | 建立 UI 回归清单与入口快照 | 防止上游升级回流 |
| P1 | 建立“配置关闭 / 导航裁剪 / 不可达兜底”三层防线 | 降低单点失效风险 |
| P2 | 当裁剪成本持续升高时重新评估自建前端 | 为 v3+ 保留演进路径 |

---

## 6. 局限性与待探索

- 尚未对当前 Open WebUI 版本的所有终端用户导航项做浏览器逐页实测。
- 尚未验证 Rich UI 在 `allowSameOrigin` 关闭时的全部交互细节。
- 未对 Open WebUI 商业/品牌授权条款做法律级解释；当前仅依据公开品牌文档和项目公开信息作产品命名约束。
- 尚未形成最终实现清单，哪些入口通过配置关闭、哪些通过前端裁剪、哪些通过权限隔离，仍需在编码阶段精确落表。

---

## 7. 参考来源

1. Open WebUI Features: https://docs.openwebui.com/features/ （访问于 2026-04-07）
2. Open WebUI Rich UI: https://docs.openwebui.com/features/extensibility/plugin/development/rich-ui/ （访问于 2026-04-07）
3. Open WebUI Brand Guidelines: https://docs.openwebui.com/brand/ （访问于 2026-04-07）
4. 本地源码: `d:\PROJECTALL\ROCO\references\open-webui\src\lib\stores\index.ts`
5. 本地源码: `d:\PROJECTALL\ROCO\references\open-webui\src\lib\components\admin\Settings\Connections.svelte`
6. 本地源码: `d:\PROJECTALL\ROCO\references\open-webui\src\lib\components\chat\Settings\Connections.svelte`
7. 本地源码: `d:\PROJECTALL\ROCO\references\open-webui\src\lib\utils\connections.ts`
