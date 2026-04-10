# 系统设计: web-ui-system
 
 | 字段 | 值 |
 | ---- | --- |
 | **System ID** | `web-ui-system` |
 | **Project** | RoCo Team Builder |
 | **Version** | v2 |
 | **Status** | `Draft` |
 | **Author** | Cascade |
 | **Date** | 2026-04-07 |
 | **L1 Detail** | [web-ui-system.detail.md](./web-ui-system.detail.md) |
 | **Research** | [`_research/web-ui-system-research.md`](./_research/web-ui-system-research.md) |
 
 > [!IMPORTANT]
 > **文档分层说明**
 > - **本文件 (L0 导航层)**: 架构图、操作契约、设计决策。面向快速理解与任务规划。
 > - **[web-ui-system.detail.md](./web-ui-system.detail.md) (L1 实现层)**: 配置常量、完整数据结构、伪代码、边缘情况。仅 `/forge` 明确引用时加载。
 
 ---
 
 ## 📋 目录 (Table of Contents)
 
 | § | 章节 | 关键内容 |
 | :---: | ---- | ---- |
 | 1 | [概览](#1-概览-overview) | 系统目的、边界、职责 |
 | 2 | [目标与非目标](#2-目标与非目标-goals--non-goals) | Goals / Non-Goals |
 | 3 | [背景与上下文](#3-背景与上下文-background--context) | 关联需求、约束、依赖 |
 | 4 | [系统架构](#4-系统架构-architecture) | Mermaid 架构图、组件、数据流 |
 | 5 | [接口设计](#5-接口设计-interface-design) | 操作契约、跨系统协议 |
 | 6 | [数据模型](#6-数据模型-data-model) | 属性字段声明、关系图、L1 锚点 |
 | 7 | [技术选型](#7-技术选型-technology-stack) | 核心技术、关键依赖 |
 | 8 | [Trade-offs](#8-trade-offs--alternatives) | 决策理由、备选方案 |
 | 9 | [安全性考虑](#9-安全性考虑-security-considerations) | 风险与缓解 |
 | 10 | [性能考虑](#10-性能考虑-performance-considerations) | 性能目标、优化策略 |
 | 11 | [测试策略](#11-测试策略-testing-strategy) | 单测、集成、回归 |
 | 12 | [部署与运维](#12-部署与运维-deployment--operations) | 部署、上线检查、监控 |
 | 13 | [未来考虑](#13-未来考虑-future-considerations) | 扩展性、演进路径 |
 | 14 | [附录](#14-附录-appendix) | 参考资料、拆分检测 |
 
 **L1 实现层** → [web-ui-system.detail.md](./web-ui-system.detail.md)
 > [§1 配置常量](./web-ui-system.detail.md#1-配置常量-config-constants) · [§2 数据结构](./web-ui-system.detail.md#2-核心数据结构完整定义-full-data-structures) · [§3 算法](./web-ui-system.detail.md#3-核心算法伪代码-non-trivial-algorithm-pseudocode) · [§4 决策树](./web-ui-system.detail.md#4-决策树详细逻辑-decision-tree-details) · [§5 边缘情况](./web-ui-system.detail.md#5-边缘情况与注意事项-edge-cases--gotchas)
 
 ---
 
 ## 1. 概览 (Overview)
 
 ### 1.1 System Purpose (系统目的)
 
 `web-ui-system` 是 RoCo Team Builder 面向终端用户的**受控产品壳层**。它基于 Open WebUI 构建，但其职责不是暴露一个“全功能 AI 平台”，而是把 Open WebUI 收敛成一个围绕洛克王国世界配队与精灵问答场景的 Chat-first Web 产品。
 
 ### 1.2 System Boundary (系统边界)
 
 - **输入 (Input)**: 用户文本消息、截图上传、模型选择、BYOK 配置、管理员连接配置
 - **输出 (Output)**: 对话界面、OpenAI 兼容请求、Rich UI 消息展示
 - **依赖系统 (Dependencies)**: `agent-backend-system`、Open WebUI 基座能力、外部 LLM Provider
 - **被依赖系统 (Dependents)**: 终端用户主路径、管理员配置路径
 
 ### 1.3 System Responsibilities (系统职责)
 
 **负责**:
 - 为用户提供文本输入、截图上传、模型选择、结果展示的主交互面
 - 区分“内置模型轨道（完整产品路径）”和“BYOK 轨道（受限直连模式）”，并为两条链路提供清晰入口与能力差异标识（BYOK 下显式降级 Agent 增强 UI）
 - 承接 `agent-backend-system` 的 OpenAI 兼容对话能力
 - 展示工具调用折叠卡片与 Rich UI 精灵卡片
 - 对 Open WebUI 原生平台能力进行裁剪、隐藏、禁用、隔离或重命名
- 展示截图识别后的候选精灵清单，承接用户确认，并把确认后的拥有列表提交给 `agent-backend-system`
- 在会话界面显式提示“当前推荐基于已确认拥有列表”，避免把识别候选误呈现为已确认事实
 
 **不负责**:
 - Agent 推理、工具编排和会话状态实现细节
 - BWIKI 接口访问与缓存
 - 精灵卡片 HTML 模板生成
 - 外部 LLM Provider 的具体模型能力与定价
- `ConfirmedOwnedSpiritList` 的权威存储与推荐约束判定
 
 ---
 
 ## 2. 目标与非目标 (Goals & Non-Goals)

 ### 2.1 目标
 - 支撑 [REQ-001], [REQ-002], [REQ-003], [REQ-004], [REQ-005], [REQ-006]
 - 让终端用户默认只接触与配队问答、截图识别、BYOK、Rich UI 展示直接相关的功能
 - 为 `agent-backend-system` 提供稳定的内置轨道接入方式
 - 为用户自带 Key 提供清晰、可解释、仅存本地浏览器的 BYOK 路径
 - 支持桌面优先、移动兼容的响应式对话体验
 - 将“可见能力白名单”固化为可测试的发布约束

 ### 2.2 非目标
 - 不把 Open WebUI 的知识库、频道、笔记、开放终端、实验入口等通用平台能力暴露给终端用户
 - 不在服务端存储用户 API Key
 - 不在本系统内承接 Agent 推理、BWIKI 数据获取、精灵卡片 HTML 生成逻辑
 - 不在 v2 中自建全新前端框架替代 Open WebUI
 - 不保证对 Open WebUI 所有上游功能进行物理删除；v2 只要求终端用户路径不可见、不可达、不可误触

 ---
 
 ## 3. 背景与上下文 (Background & Context)

 ### 3.1 Why This System? (为什么需要这个系统？)

 `web-ui-system` 的核心不是“做一个能聊天的页面”，而是**把 Open WebUI 从通用平台收敛为垂类产品壳层**。如果不显式控制能力暴露面，用户会看到 Notes、Channels、Knowledge、Open Terminal 等与本产品无关的入口，直接破坏 [REQ-006] 要求的单用途体验。

 **关联 PRD 需求**: [REQ-001], [REQ-002], [REQ-003], [REQ-004], [REQ-005], [REQ-006]

 ### 3.2 Current State (现状分析)

 当前设计已经明确了产品壳层、双轨模型路由、Rich UI 降级和白名单策略，但在严格模板层面仍有两类风险：

 - 部分操作契约仍未挂到 `L1`，影响 L0 / L1 闭环
 - `§1 / §3 / §4` 的标题与子结构和 `agent-backend-system` 尚未完全统一
 - 尚未把产品视觉语言、Open WebUI DOM 覆写策略和 Rich UI 宿主风格写成可执行约束，导致后续实现容易退回默认平台风格

 ### 3.3 Constraints (约束条件)

 - **技术约束**: 前端基座固定为 Open WebUI；BYOK 必须走 Direct Connections；Rich UI 必须服从 iframe sandbox
 - **性能约束**: 默认首屏直达聊天主路径；截图上传和富展示失败必须可快速降级
 - **资源约束**: v2 不自建全新前端框架，只在 Open WebUI 上进行受控裁剪与壳层化
 - **安全约束**: 用户 API Key 仅保存在浏览器 `localStorage`；管理员能力不得进入终端用户主路径
 - **视觉约束**: 整体 UI 必须收敛为“复古冒险者手账风”，采用炭黑侧栏、羊皮纸主区、暖金强调、低透明度地图纹理和手账标签式控件；沉浸感不得破坏聊天主路径的可读性与可操作性

 ---
 
 ## 4. 系统架构 (Architecture)

 ### 4.1 Architecture Diagram (架构图)

 ```mermaid
 flowchart TD
     A[终端用户 Browser] --> B[Product Shell Layout]
     B --> C[Chat Workspace]
     B --> D[Entry Guard / Navigation Filter]
     C --> E[Input Composer]
     C --> F[Attachment Upload]
     C --> G[Message Timeline]
     C --> H[Model & Key Settings]

     H --> I{Route Selector}
     I -->|内置轨道| J[OpenAI-Compatible Connection]
     I -->|BYOK 轨道| K[Direct Connections]

     J --> L[agent-backend-system]
     K --> M[External OpenAI-Compatible Provider]

     G --> N[Tool Call Fold Cards]
     G --> O[Rich UI Embed Host]
     O --> P[spirit-card-system HTML via backend payload]

     D --> Q[Whitelist Policy]
     Q --> C
     D --> R[Admin / Platform Features]
     R -->|终端用户不可达| S[Hidden / Disabled / Isolated]
 ```

 ### 4.2 Core Components (核心组件)

 | Component Name | Responsibility | Tech Stack | Notes |
 | ------ | ------ | ------ | ------ |
 | `Product Shell Layout` | 承载产品标题、默认布局、主路径结构 | Open WebUI Layout | 聚焦后的页面框架 |
 | `Entry Guard / Navigation Filter` | 隐藏或移除与产品无关入口 | Svelte / config gating | 白名单第一道防线 |
 | `Chat Workspace` | 提供对话主工作区 | Open WebUI chat runtime | 主交互面 |
 | `Theme Override Layer` | 把 Open WebUI 默认平台风格强制覆写为产品手账风 | CSS Variables + scoped override CSS | 视觉基线与 DOM 锚点集中管理 |
 | `Model & Key Settings` | 管理内置轨道选择和 BYOK 配置 | Direct Connections / localStorage | 双轨入口 |
 | `Route Selector` | 决定请求走内置轨道还是 BYOK 轨道，并在发送前结合当前模型能力判断截图是否允许发送 | local UI state | 不得静默切轨；截图能力预检在此完成 |
 | `Rich UI Embed Host` | 承载 HTML/iframe 富展示 | Rich UI iframe sandbox | 必须支持降级 |
 | `Recognition Review Panel` | 展示识别候选、承接用户勾选/确认，并与会话中的已确认拥有列表状态提示联动 | local UI state + chat timeline components | 只能表达候选与确认动作，不是真理源 |
 | `Whitelist Policy` | 定义保留能力与禁止入口，并作为白名单回归唯一验证资产的逻辑来源 | product config + ADR-004 | 真理源是 `VisibleFeaturePolicy` |

 ### 4.3 Data Flow (数据流)

 ```mermaid
 sequenceDiagram
     participant User
     participant Shell as Product Shell Layout
     participant Route as Route Selector
     participant Backend as agent-backend-system
     participant Provider as BYOK Provider
     participant Review as Recognition Review Panel
     participant RichUI as Rich UI Host

     User->>Shell: 输入文本 / 上传截图
     Shell->>Route: 读取当前轨道状态与当前模型能力
     alt 图片发送前能力不满足
         Route-->>Shell: 返回 CAPABILITY_ 错误
         Shell-->>User: 提示切换支持视觉的模型或切回内置轨道
     else 内置轨道
         Route->>Backend: POST /v1/chat/completions
         Backend-->>Shell: 流式消息 / 工具结果 / Rich UI payload / 识别候选
         alt 返回识别候选
             Shell->>Review: 渲染候选清单与确认态
             User->>Review: 勾选 / 确认拥有列表
             Review->>Backend: submit confirmed owned list
             Backend-->>Shell: 会话确认成功 / 后续推荐受约束
         end
     else BYOK 轨道
         Route->>Provider: Browser direct request
         Provider-->>Shell: 模型响应
     end
     Shell->>RichUI: 渲染富结果或降级文本卡片
     RichUI-->>User: 展示结果
 ```

 **关键数据流说明**:
 1. 用户请求在离开前端前必须先完成轨道决策，避免“界面是 A、请求走 B”。
 2. 图片请求在真正发送前必须先完成视觉能力预检；不支持视觉时，前端直接返回 `CAPABILITY_` 产品错误，而不是等待 Provider 默认失败。
 3. 内置轨道与 BYOK 轨道的故障模式不同，错误提示必须区分；内置额度超限时应显式引导切换 BYOK 或等待窗口重置。
 4. **BYOK 轨道是受限直连模式**：不经过 Agent 后端，因此不具备工具调用、BWIKI 查询、精灵卡片、会话隔离等 Agent 增强能力。前端必须在 BYOK 轨道下显式降级相关 UI 暗示（参见 `01_PRD.md` §6.2 双轨能力矩阵）。
 5. 当后端返回截图识别候选时，前端必须先进入 `Recognition Review` 交互态；候选列表在用户确认前不得被表述为“已拥有事实”。
 6. 前端只负责展示候选、收集确认并提交；`ConfirmedOwnedSpiritList` 的权威存储与推荐约束都在 `agent-backend-system`。
 7. Rich UI 只是增强层，渲染失败时必须回退为可读文本结果。
 8. 完整决策逻辑见 [L1 §4](./web-ui-system.detail.md#4-决策树详细逻辑-decision-tree-details)。

 ### 4.4 建议目录结构

 ```text
 src/web-ui-shell/
 ├── shell/
 │   ├── layout/
 │   ├── navigation/
 │   └── branding/
 ├── chat/
 │   ├── composer/
 │   ├── attachments/
 │   ├── timeline/
 │   └── tool-result/
 ├── settings/
 │   ├── builtin-route/
 │   ├── byok/
 │   └── visibility/
 ├── guards/
 │   ├── feature-whitelist/
 │   ├── role-gating/
 │   └── route-isolation/
 ├── integrations/
 │   ├── agent-backend-connection/
 │   ├── direct-connections/
 │   └── rich-ui/
 └── regression/
     └── ui-entry-checklist/
 ```

 ---
 
 ## 5. 接口设计 (Interface Design)
 
 ### 5.1 操作契约表 (Operation Contracts)
 
 | 操作 | [REQ-XXX] | 前置条件 | 消耗/输入 | 产出/副作用 | 实现细节 |
 | ---- | :---: | ---- | ---- | ---- | :---: |
 | `filter_navigation(user_role, policy)` | [REQ-006] | 已加载用户角色; 已加载白名单 | 当前导航树 | 返回可见入口集合；屏蔽无关入口 | [L1 §3.1](./web-ui-system.detail.md#31-filter_navigationuser_role-policy) |
 | `select_route(route_state, builtin_ready, direct_ready)` | [REQ-001], [REQ-002], [REQ-006] | 用户已选择模型或轨道 | 当前路由状态 | 决定走内置轨道或 BYOK；必要时显式回退 | [L1 §3.2](./web-ui-system.detail.md#32-select_routeroute_state-builtin_ready-direct_ready) |
 | `preflight_image_capability(route_state, model_capability)` | [REQ-002], [REQ-006] | 当前轨道与当前模型已解析 | 当前路由状态、模型能力摘要 | 若支持视觉则允许继续发送；若不支持则返回 `CAPABILITY_` 错误并阻止发送 | [L1 §3.5](./web-ui-system.detail.md#35-submit_image_messagefile-route_state) |
 | `submit_text_message(text, route_state)` | [REQ-001], [REQ-003], [REQ-005] | 文本非空; 存在可用轨道 | 文本、模型状态 | 发起对话请求；消息进入时间线 | [L1 §3.4](./web-ui-system.detail.md#34-submit_text_messagetext-route_state) |
 | `submit_image_message(file, route_state)` | [REQ-002] | 文件类型合法; 存在可用轨道; 当前轨道对应模型支持视觉能力 | 图片文件、模型状态 | 生成多模态消息输入；进入对话链路；若能力不满足则前端直接阻断 | [L1 §3.5](./web-ui-system.detail.md#35-submit_image_messagefile-route_state) |
 | `render_recognition_review(candidates, route_state)` | [REQ-002], [REQ-005] | 当前请求走 builtin 轨道; 后端返回识别候选 | 候选精灵列表、当前路由状态 | 渲染候选 review 清单；进入“待确认”UI 状态；未确认前不改变会话拥有事实 | [L1 §3.9](./web-ui-system.detail.md#39-render_recognition_reviewcandidates-route_state) |
| `submit_owned_list_confirmation(confirmed_list, route_state)` | [REQ-002], [REQ-005] | 用户已确认候选; 当前聊天存在 `chat_id`; 当前轨道为 builtin | 已确认拥有列表、当前路由状态 | 向 `agent-backend-system` 提交确认结果；成功后刷新“当前推荐基于已确认拥有列表”状态提示 | [L1 §3.10](./web-ui-system.detail.md#310-submit_owned_list_confirmationconfirmed_list-route_state) |
| `persist_direct_connection(base_url, api_key, config)` | [REQ-006] | `ENABLE_DIRECT_CONNECTIONS=true`; 浏览器可写 `localStorage` | Provider URL、API Key、配置 | 本地保存 BYOK 配置；不触达服务端 | [L1 §3.6](./web-ui-system.detail.md#36-persist_direct_connectionbase_url-api_key-config) |
 | `render_message_artifacts(message, policy)` | [REQ-004], [REQ-006] | 消息已返回 | 工具事件、Rich UI payload | 渲染工具折叠卡片与富结果；必要时降级 | [L1 §3.3](./web-ui-system.detail.md#33-render_message_artifactsmessage-policy) |
 | `build_theme_override_css(theme_config, selector_map)` | [REQ-006] | 已确定产品视觉 token；已确认 DOM 锚点 | 主题配置、DOM 选择器映射 | 输出注入 Open WebUI 的 CSS Variables 与强制覆写样式 | [L1 §3.8](./web-ui-system.detail.md#38-build_theme_override_csstheme_config-selector_map) |
 | `register_builtin_connection(base_url, config)` | [REQ-006] | 管理员权限; 系统设置可用 | 系统级连接配置 | 内置轨道可用；终端用户不见后台入口 | [L1 §3.7](./web-ui-system.detail.md#37_register_builtin_connectionbase_url-config) |
 
 ### 5.2 跨系统接口协议 (Cross-System Interface)
 
 ```python
 class IWebUiRouteGateway(Protocol):
     def select_route(self, route_state: UiRouteState) -> str: ...
     def can_render_rich_ui(self, policy: VisibleFeaturePolicy) -> bool: ...
 
 class IAgentBackendConnection(Protocol):
     def list_models(self) -> list[str]: ...
     def send_chat_completion(self, payload: dict) -> object: ...
 ```

 **会话头传递契约 (Session Header Contract)**:

 `web-ui-system` 在内置轨道下向 `agent-backend-system` 发送请求时，**必须**同时转发以下两个头部：
 - `X-OpenWebUI-User-Id`: 当前用户标识
 - `X-OpenWebUI-Chat-Id`: 当前聊天标识
 
 若任一头部缺失，`agent-backend-system` 将返回 **400 Bad Request**，不做回退。
 
 **前置条件**: Open WebUI 必须开启 `ENABLE_FORWARD_USER_INFO_HEADERS=true`。
 
 ### 5.3 HTTP API / Connection Summary
 
 | Method | Path / Target | Auth | 用途 | [REQ-XXX] |
 | ---- | ---- | :---: | ---- | :---: |
 | `GET` | `/v1/models` | 系统连接 | 拉取内置轨道模型列表 | [REQ-006] |
 | `POST` | `/v1/chat/completions` | 系统连接 | 向 `agent-backend-system` 发送对话请求 | [REQ-001], [REQ-002], [REQ-003], [REQ-004], [REQ-005] |
 | Browser Direct | `OpenAI-compatible base_url` | 用户自带 Key | 走 BYOK 轨道直连 Provider | [REQ-006] |
 
 ---
 
 ## 6. 数据模型 (Data Model)
 
 ### 6.1 核心实体 (Core Entities)
 
 ```python
 @dataclass
 class VisibleFeaturePolicy:
     chat_enabled: bool
     image_upload_enabled: bool
     builtin_route_enabled: bool
     byok_enabled: bool
     tool_result_enabled: bool
     rich_ui_enabled: bool
     forbidden_entries: list[str]
     policy_version: str
     snapshot_scope: list[str]
     expected_visible_entries: list[str]
     expected_hidden_entries: list[str]
     validation_baseline_id: str | None
 
     def allows(self, feature_key: str) -> bool: ...
 
 
 @dataclass
 class BuiltinRouteConfig:
     connection_name: str
     base_url: str
     default_model_id: str
     enabled: bool
 
 
 @dataclass
 class DirectConnectionEntry:
     base_url: str
     api_key: str
     config: dict
     selected_model: str | None
     storage_scope: Literal["localStorage"]
 
 
 @dataclass
 class UiRouteState:
     active_route: Literal["builtin", "byok"]
     active_model_id: str | None
     chat_id: str | None
     is_uploading: bool
     rich_ui_available: bool
     active_model_supports_vision: bool | None
     builtin_quota_status: Literal["available", "exhausted", "unknown"]
 
     def can_send(self) -> bool: ...


 @dataclass
 class RecognitionReviewState:
     chat_id: str
     candidates: list[dict]
     status: Literal["idle", "pending_confirmation", "submitting", "confirmed"]
     source_message_id: str | None
 
     def can_submit(self) -> bool: ...


 @dataclass
 class ConfirmedOwnedListViewModel:
     chat_id: str
     confirmed_spirit_ids: list[str]
     confirmed_names: list[str]
     is_active: bool
     last_confirmed_at: datetime | None


 @dataclass
 class ThemeOverrideConfig:
     theme_name: Literal["roco_adventure_journal"]
     root_tokens: dict[str, str]
     selector_map: dict[str, list[str]]
     texture_strategy: str
     sidebar_edge_style: str
     bubble_style_mode: str
 ```
 
 > *(配置常量详见 [L1 §1](./web-ui-system.detail.md#1-配置常量-config-constants) · 完整方法实现详见 [L1 §2](./web-ui-system.detail.md#2-核心数据结构完整定义-full-data-structures))*
 
 ### 6.2 实体关系图 (Entity Relationship)
 
 ```mermaid
 classDiagram
     class VisibleFeaturePolicy {
         +bool chat_enabled
         +bool image_upload_enabled
         +bool builtin_route_enabled
         +bool byok_enabled
         +bool tool_result_enabled
         +bool rich_ui_enabled
         +list forbidden_entries
     }
     class BuiltinRouteConfig {
         +str connection_name
         +str base_url
         +str default_model_id
         +bool enabled
     }
     class DirectConnectionEntry {
         +str base_url
         +str api_key
         +dict config
         +str selected_model
         +str storage_scope
     }
     class UiRouteState {
         +str active_route
         +str active_model_id
         +str chat_id
         +bool is_uploading
         +bool rich_ui_available
     }
     class RecognitionReviewState {
         +str chat_id
         +list candidates
         +str status
         +str source_message_id
     }
     class ConfirmedOwnedListViewModel {
         +str chat_id
         +list confirmed_spirit_ids
         +list confirmed_names
         +bool is_active
         +datetime last_confirmed_at
     }

      class ThemeOverrideConfig {
         +str theme_name
         +dict root_tokens
         +dict selector_map
         +str texture_strategy
         +str sidebar_edge_style
         +str bubble_style_mode
     }
 
     VisibleFeaturePolicy --> UiRouteState : constrains
     BuiltinRouteConfig --> UiRouteState : provides default route
     DirectConnectionEntry --> UiRouteState : backs byok route
     RecognitionReviewState --> UiRouteState : depends on active builtin chat
     RecognitionReviewState --> ConfirmedOwnedListViewModel : becomes after confirmation
     ThemeOverrideConfig --> VisibleFeaturePolicy : styles visible shell
 ```
 
 ### 6.3 数据流向 (Data Flow Direction)
 
 - `VisibleFeaturePolicy` 决定终端用户可见能力与可达入口，也是白名单唯一验证资产的真理源
 - `BuiltinRouteConfig` 描述系统级内置轨道连接
 - `DirectConnectionEntry` 保存在浏览器本地，用于 BYOK 直连
 - `UiRouteState` 在发送消息前决定请求实际走向，并携带当前模型视觉能力与内置额度状态摘要
 - `RecognitionReviewState` 表示截图识别后的候选 review 交互态；其候选只用于展示与确认，不代表已确认拥有事实
 - `ConfirmedOwnedListViewModel` 只用于会话界面展示当前 chat 已确认拥有列表状态；权威存储仍在 `agent-backend-system`
 - `ThemeOverrideConfig` 定义 CSS Variables、DOM 锚点、纹理和聊天气泡等产品视觉基线

 ---
 
 ## 7. 技术选型 (Technology Stack)

| 层 | 技术 | 用途 |
|----|------|------|
| Base Platform | Open WebUI | 提供对话 UI、连接配置、Rich UI、用户会话外壳 |
| UI Runtime | Svelte/SvelteKit（随 Open WebUI） | 前端页面与组件运行时 |
| Styling Layer | CSS Variables + Tailwind utility overrides + scoped custom CSS | 将默认平台风格收敛为产品手账风 |
| Built-in Route | OpenAI-compatible connection | 连接 `agent-backend-system` |
| BYOK Route | Direct Connections | 用户本地直连 OpenAI 兼容 Provider |
| Rich UI | sandboxed iframe / HTML embed | 展示精灵卡片与工具富结果 |
| Storage | `localStorage` | 用户本地保存 BYOK Key 与连接配置 |
| Deployment | Docker | 与后端共同部署 |

### 7.1 关键配置约束

| 配置项 | 值/策略 | 原因 |
|-------|---------|------|
| `ENABLE_DIRECT_CONNECTIONS` | `true` | 支持 BYOK |
| 系统级 OpenAI 连接 | 指向 `agent-backend-system` | 提供内置模型轨道 |
| 用户 API Key 存储 | 仅 `localStorage` | 满足 PRD 安全约束 |
| 默认首页路径 | 直接落在产品对话主路径 | 避免用户进入平台化首页 |
| 禁止入口策略 | 配置关闭 + 导航裁剪 + 不可达兜底 | 三层防线防回流 |
| 主题注入方式 | `:root` CSS Variables + DOM 语义锚点 + Tailwind 强制覆写 | 尽量减少对 Open WebUI 内部结构的脆弱依赖 |

### 7.2 Visual Language & Theme Override Strategy

- **整体气质**: 页面必须呈现“复古冒险者手账风”，不是通用 AI 平台控制台
- **主色结构**: 炭黑侧栏、羊皮纸主聊天区、暖金强调色、奶白表面层
- **纹理策略**: 主区叠加 5%-10% 透明度的地图线稿 / 山脉 / 齿轮类 SVG 纹理，`background-blend-mode: multiply`
- **版式语汇**: 侧栏与主区交界使用撕纸 / 笔刷边缘，而不是 1px 直线分隔
- **聊天语汇**: 用户气泡是纸贴片；Agent 文本更接近直接书写在纸面上的记录；输入区采用胶囊形工具条
- **组件语汇**: History 项、快捷按钮、工具卡片必须具备手账标签感，Hover / Active 使用暖金色 + 虚线内框
- **实现原则**: 优先锚定语义容器（`aside`, `main`, `form`, `textarea`, `iframe`），再覆盖 Open WebUI 常见 Tailwind 类名，最后才使用高优先级兜底选择器
- **落地参考**: 完整 `:root` 变量、Custom CSS、DOM 覆写策略和 Tailwind 组件拆解见 [L1 §5.2](./web-ui-system.detail.md#52-ui-theme-override-reference)

 ---
 
 ## 8. Trade-offs & Alternatives

### 8.1 ADR 引用清单

> **决策来源**: [ADR-001: 技术栈选择（v2）](../03_ADR/ADR_001_TECH_STACK.md)
>
> 本系统实现 ADR-001 定义的“Open WebUI 作为受控产品壳层基座”决策，不在此重复为何不自建前端。

> **决策来源**: [ADR-004: Web UI 裁剪与收敛策略](../03_ADR/ADR_004_WEB_UI_PRUNING_STRATEGY.md)
>
> 本系统遵循“能力白名单优先、终端用户主路径收敛、管理员能力不可进入主路径”的约束，不在此重复跨系统裁剪策略理由。

### 8.2 本系统特有决策 1：为什么采用“能力白名单”，而不是“默认开放 + 局部隐藏”

- **选择 A**: 白名单驱动的可见能力设计
- **不选 B**: 默认开放后再按页面逐个隐藏

**原因**:
- 本产品的核心问题是产品边界，而不是主题皮肤。
- 默认开放会让上游新增入口在升级后悄悄进入用户视野。
- 白名单更容易转化为 UI 回归清单和发布验收标准。

### 8.3 本系统特有决策 2：为什么保留 Open WebUI，而不是立即自建前端

- **选择 A**: Open WebUI 受控壳层
- **不选 B**: 自建 Next.js / React 前端

**原因**:
- Open WebUI 已成熟提供对话、多模型连接、Direct Connections、Rich UI 等基础能力。
- 当前阶段产品验证重点是“配队体验与能力收敛”，而不是重新建设前端基础设施。
- 只有当上游裁剪成本持续高于自建成本时，才值得转向自建前端。

### 8.4 本系统特有决策 3：为什么区分“内置轨道”与“BYOK 轨道”，且 BYOK 是受限直连模式

- **选择 A**: 双轨明确分离，BYOK 定义为受限直连模式
- **不选 B**: 所有模型连接统一放在一个模糊入口
- **不选 C**: BYOK 也承诺完整产品能力（通过服务端转发 Agent）

**原因**:
- 两条链路的信任边界不同：内置轨道由部署者承担，BYOK 轨道由用户承担。
- **能力边界不同**: BYOK 请求由浏览器直连 Provider，不经过 Agent 后端，因此不具备工具调用、BWIKI 数据、精灵卡片、会话隔离等 Agent 增强能力。
- 故障模式不同：内置轨道主要是服务端可用性问题，BYOK 轨道还涉及 CORS、用户 Key、Provider 能力差异。
- 用户理解成本更低：开箱即用与自带 Key 是两种清晰产品承诺，前者完整，后者受限。
- 完整能力矩阵见 `01_PRD.md` §6.2。

### 8.5 本系统特有决策 4：为什么把“管理员能力保留”与“终端用户不可达”分开设计

- **选择 A**: 允许后台保留必要系统维护能力，但与终端主路径隔离
- **不选 B**: 要么全部保留，要么尝试全部物理删除

**原因**:
- Open WebUI 仍承担基座与维护责任，管理员需要保留连接配置和系统管理能力。
- 物理删除会提高升级成本与分叉维护成本。
- 对 v2 而言，“终端用户不可达”已经足以满足产品边界要求。

### 8.6 本系统特有决策 5：为什么要求 Rich UI 必须支持降级

- **选择 A**: Rich UI 增强 + 文本/结构化结果降级
- **不选 B**: 纯依赖 iframe 高级能力

**原因**:
- Rich UI 运行受 sandbox 与浏览器能力限制。
- 若某些脚本能力或 same-origin 条件不满足，纯降级文本仍能保证结果可读性。
- 这能避免“展示失败即功能失败”的脆弱链路。

 ---
 
 ## 9. 安全性考虑 (Security Considerations)

- **BYOK 密钥边界**
  - 用户 API Key 仅保存在浏览器 `localStorage`
  - 不通过 `agent-backend-system` 中转，不写入服务端日志
  - 对用户明确提示浏览器本地存储语义与 Provider 风险
- **管理员能力隔离**
  - 系统级连接与配置入口只对管理员开放
  - 终端用户主路径中不出现后台维护入口
- **上传与富展示安全**
  - 图片上传仅用于对话输入，不形成持久化媒体库
  - Rich UI 严格运行在 iframe sandbox 内
  - 富展示与父页面交互优先走受控 `postMessage`
- **错误暴露控制**
  - 对终端用户使用可理解的产品级错误文案
  - 不暴露系统连接细节、环境变量、内部 URL 结构
- **产品级错误展示契约**
  - 所有错误必须对齐 `02_ARCHITECTURE_OVERVIEW.md` §3.5 跨系统错误分类矩阵
  - 内置轨道错误（来自 `agent-backend-system`）应根据错误码前缀映射为用户友好文案
  - BYOK 轨道错误归因必须指向用户侧（Key / Provider / 网络 / CORS），不得暗示系统内部故障
  - 可重试错误应提供重试按钮或重试引导；不可重试错误应提供明确的下一步行动建议
  - BWIKI 相关失败必须展示 `wiki_url` 回退链接

 ---
 
 ## 10. 性能考虑 (Performance Considerations)

- **Chat-first 首屏**: 默认进入对话主路径，减少平台型首页跳转成本
- **入口精简**: 减少无关导航和页面切换，提升首次理解速度
- **上传链路轻量化**: 截图上传只走必要消息链路，不引入额外工作区存储流程
- **Rich UI 降级**: 富展示失败时快速退回文本展示，避免消息区空白
- **连接状态缓存**: 系统级连接与用户本地 Direct Connections 状态应就近读取，减少无意义重复初始化
- **移动兼容**: 小屏下保持单列对话主路径，不把复杂设置面作为默认入口
- **视觉覆写可控**: 通过集中 theme token 和 DOM selector map 管理样式，降低 Open WebUI 升级后大面积重写成本

 ---
 
 ## 11. 测试策略 (Testing Strategy)

### 11.1 单元/组件测试
- 导航过滤逻辑：终端用户角色下不应出现禁止入口
- 轨道路由逻辑：内置模型与 BYOK 模型切换正确
- 本地存储逻辑：BYOK 配置仅写入浏览器本地
- 上传组件：图片选择、预览、发送状态切换正确
- 图片发送前能力预检：非视觉模型上传截图时返回 `CAPABILITY_` 并阻止发送
- 内置额度状态提示：`builtin_quota_status=exhausted` 时不会继续发起 builtin 请求
- Rich UI Host：有 payload 时渲染，失败时降级
- Theme Override Layer：能输出 `:root` token、撕纸边缘、背景纹理、输入框覆写和标签化历史项样式

### 11.2 集成测试
- `agent-backend-system` 作为系统级 OpenAI 兼容连接可被正常选择与调用
- 开启 Direct Connections 后，用户可新增自定义 OpenAI 兼容 Provider
- 截图上传后消息能以多模态方式进入对话链路
- 内置轨道返回识别候选时，前端先渲染 `Recognition Review`，而不是直接把候选当作已确认拥有列表
- 用户确认拥有列表后，界面出现“当前推荐基于已确认拥有列表”提示，且后续同 chat 请求保持该提示
- BYOK 非视觉模型上传截图时，前端在发送前拦截并提示切换支持视觉的模型或切回 builtin
- BYOK 轨道不出现识别确认、精灵卡片与工具调用增强闭环的误导性 UI 暗示
- builtin route 额度超限时，界面显示 `QUOTA_` 语义与切换 BYOK 引导，而不是静默切轨
- 工具调用结果以折叠卡片出现在时间线中
- 精灵卡片可在消息区渲染，异常时回退为文本
- 注入产品主题后，主区、侧栏、消息列表、输入区与 Rich UI 宿主在桌面端与移动端都保持同源视觉语言

### 11.3 UI 回归测试
- 终端用户首页不出现 Notes、Channels、Open Terminal、Knowledge、Admin 等入口
- 侧边栏、顶部栏、空状态页、设置面板、移动导航都满足白名单约束
- 管理员登录时必要后台能力仍可访问
- 升级 Open WebUI 后，禁止入口不会重新暴露
- `VisibleFeaturePolicy` 导出快照与基线一致；若不一致则视为白名单回归未通过
- 炭黑侧栏、撕纸边缘、羊皮纸纹理、暖金高亮、标签式 History 项与胶囊输入框不会在升级后退回默认平台样式
- Agent 文本、用户气泡、工具卡片与 Rich UI 宿主保持“手账记录”一致气质，而不是混入明显平台风组件

### 11.4 验收测试
- 对照 [REQ-006] 检查首页只暴露聊天、截图上传、模型/Key 配置、结果展示相关入口
- 对照 [REQ-002] 检查截图上传路径从选择文件到发送消息完整可用
- 对照 [REQ-002] 检查“识别候选 → 用户确认 → 已确认拥有列表状态提示”完整可走通，且候选不会被误呈现为已确认事实
- 对照 [REQ-004] 检查 Rich UI 精灵卡片可渲染，并带有数据来源跳转
- 对照 [REQ-005] 检查用户在同一聊天中多轮追问体验稳定
- 对照产品视觉规范检查 UI 已收敛为“复古冒险者手账风”，且沉浸式样式未破坏聊天主路径可读性

 ---
 
 ## 12. 部署与运维 (Deployment & Operations)

### 12.1 部署约束
- 作为独立 Docker 服务运行
- 与 `agent-backend-system` 处于同一 Docker Compose 网络
- 通过管理员配置注册 `agent-backend-system` 为系统级 OpenAI 兼容连接
- `ENABLE_DIRECT_CONNECTIONS=true`

### 12.2 上线前检查
- 内置轨道已注册且可拉取模型列表
- BYOK 入口已启用且用户文案清晰
- 终端用户首页默认进入产品对话主路径
- 禁止入口在 user 角色下均不可见、不可达
- 富展示失败时有可读降级结果
- `VisibleFeaturePolicy` 导出快照已生成，并与快照基线比对通过
- 截图发送前能力校验文案与 `CAPABILITY_` 错误语义已对齐总览矩阵
- `Recognition Review` → 用户确认 → 已确认拥有列表状态提示链路在 Compose 基线上可验
- 主题注入 CSS 已生效，主区纹理、侧栏撕纸边缘、History 标签态与输入框胶囊样式通过人工验收

### 12.3 运行时监控
- 首页进入对话主路径成功率
- 截图上传失败率
- `image_capability_block_count`
- `builtin_quota_exhausted_prompt_count`
- `recognition_review_render_count`
- `owned_list_confirmation_submit_count`
- Rich UI 渲染失败率
- 内置轨道调用成功率
- BYOK 配置保存成功率
- `visible_feature_policy_regression_fail_count`
- UI 回归缺陷数（每次上游升级后统计）

 ---
 
 ## 13. 未来考虑 (Future Considerations)

- 若 Open WebUI 裁剪成本持续升高，可在 v3+ 评估迁移到自建前端
- 为终端用户增加更明确的“当前走的是内置模型还是 BYOK”状态提示
- 为移动端进一步优化上传与消息时间线布局
- 将 UI 回归清单自动化为快照测试或 Playwright 路径测试
- 为不同用户层级设计更细的可见能力矩阵，但前提是不破坏单用途产品边界

 ---
 
 ## 14. 附录 (Appendix)

### 14.1 外部来源
- Open WebUI Features: https://docs.openwebui.com/features/ （访问于 2026-04-07）
- Open WebUI Rich UI: https://docs.openwebui.com/features/extensibility/plugin/development/rich-ui/ （访问于 2026-04-07）
- Open WebUI Brand Guidelines: https://docs.openwebui.com/brand/ （访问于 2026-04-07）
- UI 风格参考图: `d:\PROJECTALL\ROCO\asserts\ui-style.png`

### 14.2 本地源码参考
- `d:\PROJECTALL\ROCO\references\open-webui\src\lib\stores\index.ts`
- `d:\PROJECTALL\ROCO\references\open-webui\src\lib\components\admin\Settings\Connections.svelte`
- `d:\PROJECTALL\ROCO\references\open-webui\src\lib\components\chat\Settings\Connections.svelte`
- `d:\PROJECTALL\ROCO\references\open-webui\src\lib\utils\connections.ts`

### 14.3 设计拆分检测

| 规则 | 结果 |
|------|------|
| R1 单个函数/算法伪代码 > 30 行 | ❌ |
| R2 所有代码块合计 > 200 行 | ❌ |
| R3 配置常量字典条目 > 5 个 | ❌ |
| R4 版本历史注释 > 5 处 | ❌ |
| R5 文档总行数 > 500 行 | ✅ |

**结论**: 触发 R5，已创建 [web-ui-system.detail.md](./web-ui-system.detail.md) 作为实现层补充文档。
