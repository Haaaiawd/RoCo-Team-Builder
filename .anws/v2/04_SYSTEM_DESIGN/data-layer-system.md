# 系统设计: data-layer-system
 
 | 字段 | 值 |
 | ---- | --- |
 | **System ID** | `data-layer-system` |
 | **Project** | RoCo Team Builder |
 | **Version** | v2 |
 | **Status** | `Draft` |
 | **Author** | Cascade |
 | **Date** | 2026-04-07 |
 | **L1 Detail** | [data-layer-system.detail.md](./data-layer-system.detail.md) |
 | **Research** | [`_research/data-layer-system-research.md`](./_research/data-layer-system-research.md) |
 
 > [!IMPORTANT]
 > **文档分层说明**
 > - **本文件 (L0 导航层)**: 架构图、操作契约、设计决策。面向快速理解与任务规划。
 > - **[data-layer-system.detail.md](./data-layer-system.detail.md) (L1 实现层)**: 配置常量、完整数据结构、伪代码、边缘情况。仅 `/forge` 明确引用时加载。
 
 ---
 
 ## 📋 目录 (Table of Contents)
 
 | § | 章节 | 关键内容 |
 | :---: | ---- | ---- |
 | 1 | [概览](#1-概览-overview) | 系统目的、边界、职责 |
 | 2 | [目标与非目标](#2-目标与非目标-goals--non-goals) | Goals / Non-Goals |
 | 3 | [背景与上下文](#3-背景与上下文-background--context) | 为什么需要这个系统、约束 |
 | 4 | [系统架构](#4-系统架构-architecture) | Mermaid 架构图、组件职责、数据流 |
 | 5 | [接口设计](#5-接口设计-interface-design) | 操作契约表、跨系统协议 |
 | 6 | [数据模型](#6-数据模型-data-model) | 属性字段声明、关系图 |
 | 7 | [技术选型](#7-技术选型-technology-stack) | 核心技术、关键依赖 |
 | 8 | [Trade-offs](#8-trade-offs--alternatives) | 决策理由、备选方案对比 |
 | 9 | [安全性考虑](#9-安全性考虑-security-considerations) | 风险与缓解 |
 | 10 | [性能考虑](#10-性能考虑-performance-considerations) | 性能目标、优化策略 |
 | 11 | [测试策略](#11-测试策略-testing-strategy) | 单测、集成、契约测试 |
 | 12 | [部署与运维](#12-部署与运维-deployment--operations) | 部署、监控、运维边界 |
 | 13 | [未来考虑](#13-未来考虑-future-considerations) | 扩展性、演进路径 |
 | 14 | [附录](#14-附录-appendix) | 参考资料、拆分检测 |
 
 **L1 实现层** → [data-layer-system.detail.md](./data-layer-system.detail.md)
 > [§1 配置常量](./data-layer-system.detail.md#1-配置常量-config-constants) · [§2 数据结构](./data-layer-system.detail.md#2-核心数据结构完整定义-full-data-structures) · [§3 算法](./data-layer-system.detail.md#3-核心算法伪代码-non-trivial-algorithm-pseudocode) · [§4 决策树](./data-layer-system.detail.md#4-决策树详细逻辑-decision-tree-details) · [§5 边缘情况](./data-layer-system.detail.md#5-边缘情况与注意事项-edge-cases--gotchas)

 ---
 
 ## 1. 概览 (Overview)
 
 ### 1.1 System Purpose (系统目的)
 
 `data-layer-system` 是 RoCo Team Builder 的受控数据适配层。它的职责不是把 BWIKI / MediaWiki API 原样暴露给上游，而是将外部 wiki 数据、本地静态知识和名称解析逻辑收敛成一组稳定、可测试、面向领域的读取契约，供 `agent-backend-system` 在配队推理、技能分析和精灵资料查询中直接消费。
 
 ### 1.2 System Boundary (系统边界)
 
 - **输入 (Input)**: 精灵名称、搜索关键词、属性组合、知识查询键
 - **输出 (Output)**: 结构化精灵资料、候选名称列表、属性克制结果、结构化错误对象、BWIKI 回退链接
 - **依赖系统 (Dependencies)**: 外部 BWIKI / MediaWiki API、本地静态知识文件
 - **被依赖系统 (Dependents)**: `agent-backend-system`
 
 ### 1.3 System Responsibilities (系统职责)
 
 **负责**:
 - 封装 BWIKI MediaWiki API 调用与超时控制
 - 提供精灵名称规范化、别名解析和模糊匹配候选
 - 将 wiki 原始数据转换为稳定的领域对象
 - 提供属性克制矩阵和核心机制等本地静态知识读取能力
 - 通过内存 TTL 缓存减少重复请求和上游抖动
 
 **不负责**:
 - Agent 推理、会话管理和多轮上下文维护
 - 对话级错误文案生成与最终用户交互
 - 精灵卡片 HTML 渲染
 - Open WebUI 前端展示、BYOK 或 Rich UI 宿主逻辑
 
 ---
 
 ## 2. 目标与非目标 (Goals & Non-Goals)

 ### 2.1 目标
 - 支撑 [REQ-001], [REQ-002], [REQ-003], [REQ-004]
 - 向 `agent-backend-system` 提供稳定的领域读取契约，而不是泄漏 wiki 原始结构
 - 对精灵详情、搜索候选和属性克制查询提供低延迟、可缓存、可测试的访问路径
 - 在精灵名缺失、别名、简称和拼写偏差场景下输出稳定候选
 - 对上游 BWIKI 的超时、空结果和解析异常进行结构化分类
 - 保持 v2 单机单进程、零额外基础设施的简单实现路径

 ### 2.2 非目标
 - 不在 v2 中引入 Redis、数据库或离线全量镜像
 - 不将 BWIKI 作为通用搜索引擎向外开放任意查询能力
 - 不在本系统内承担最终用户文案与多轮澄清策略
 - 不负责持久化用户输入、截图或会话状态
 - 不在 v2 中自动维护完整别名百科或自动爬取全站 schema
 
 ---
 
 ## 3. 背景与上下文 (Background & Context)

 ### 3.1 Why This System? (为什么需要这个系统？)
 
 `agent-backend-system` 需要频繁查询精灵资料、搜索相似名称、读取属性克制关系，并将这些数据喂给 Agent 进行推理。但上游 BWIKI / MediaWiki API 输出的是通用内容结构，不是产品领域模型；如果直接在后端工具函数中零散拼接 HTTP 请求、缓存和解析逻辑，系统会迅速被偶然复杂度淹没。
 
 因此，`data-layer-system` 的意义在于把“外部数据源的不稳定与噪声”隔离在一处，让上游只依赖稳定的领域契约。
 
 **关联 PRD 需求**: [REQ-001], [REQ-002], [REQ-003], [REQ-004]
 
 ### 3.2 Current State (现状分析)
 
 当前 v2 架构已明确数据层的职责范围与缓存方向，但尚缺一份正式系统设计把以下问题写死：
 
 - 名称规范化、别名解析、模糊匹配由谁负责
 - BWIKI 动态数据与静态知识的边界在哪里
 - 缓存键、TTL、错误类型如何形成系统契约
 - 上游异常如何转换为可被 `agent-backend-system` 消费的结构化错误
 
 ### 3.3 Constraints (约束条件)
 
 - **技术约束**: 语言固定为 Python 3.11+；网络层使用 `httpx`；缓存策略受 ADR-002 约束为 `cachetools` 内存 TTL Cache
 - **性能约束**: BWIKI 查询成功率目标 ≥ 99%；对上游超时需要快速失败并允许上游降级；缓存必须减少重复请求
 - **资源约束**: v2 仍为单机 Docker 部署，不引入 Redis、数据库或专用搜索索引
 - **产品约束**: 数据时效以 BWIKI 为准，但静态机制知识由本地手动维护；数据层必须服务于受控产品边界，而非扩张为通用知识平台
 
 ---
 
 ## 4. 系统架构 (Architecture)

 ### 4.1 Architecture Diagram (架构图)
 
 ```mermaid
 flowchart TD
     A[agent-backend-system] --> B[Data Layer Facade]
     B --> C[Name Resolver]
     B --> D[Spirit Repository]
     B --> E[Type Matchup Store]
     B --> F[Static Knowledge Store]
 
     D --> G[Wiki Gateway]
     G --> H[BWIKI MediaWiki API]
     D --> I[Wiki Parser]
     C --> J[Alias Index]
     C --> K[Fuzzy Matcher]
 
     L[Cache Registry] --> C
     L --> D
     L --> E
     L --> F
 
     M[Error Mapper] --> B
     G --> M
     I --> M
 ```
 
 ### 4.2 Core Components (核心组件)
 
 | Component Name | Responsibility | Tech Stack | Notes |
 | ------ | ------ | ------ | ------ |
 | `Data Layer Facade` | 对外暴露统一领域契约 | Python service layer | 上游唯一入口 |
 | `Name Resolver` | 输入清洗、规范化、别名解析、模糊候选排序 | Python + `rapidfuzz` | 满足查无结果时的候选推荐 |
 | `Spirit Repository` | 获取并组装精灵结构化资料 | Python repository | 隔离 wiki 原始结构 |
 | `Wiki Gateway` | 负责 MediaWiki API 请求、超时与重试边界 | `httpx.AsyncClient` | 不承载领域逻辑 |
 | `Wiki Parser` | 将 wiki 原始响应转为领域字段 | Python parser | 避免上游绑定页面结构 |
 | `Type Matchup Store` | 提供属性克制与组合计算 | 本地静态 JSON / Python module | 不依赖外部 API |
 | `Static Knowledge Store` | 提供机制/血脉等低频知识读取 | 本地文件 | 作为静态权威源 |
 | `Cache Registry` | 统一缓存键、TTL 和最大条目控制 | `cachetools.TTLCache` | 实现 ADR-002 |
 | `Error Mapper` | 把网络/解析错误映射为结构化领域错误 | Python exceptions | 供上游稳定消费 |
 
 ### 4.3 Data Flow (数据流)
 
 ```mermaid
 sequenceDiagram
     participant BE as agent-backend-system
     participant Facade as Data Layer Facade
     participant Resolver as Name Resolver
     participant Repo as Spirit Repository
     participant Cache as Cache Registry
     participant Wiki as Wiki Gateway
     participant Parser as Wiki Parser
     participant Static as Static Knowledge Store
 
     BE->>Facade: get_spirit_profile("火神")
     Facade->>Resolver: normalize + resolve candidate
     Resolver-->>Facade: canonical name / candidates
     Facade->>Cache: lookup spirit_profile key
     alt cache hit
         Cache-->>Facade: cached profile
     else cache miss
         Facade->>Repo: fetch profile(canonical name)
         Repo->>Wiki: request MediaWiki API
         Wiki-->>Repo: raw payload
         Repo->>Parser: parse spirit fields
         Parser-->>Repo: SpiritProfile
         Repo-->>Facade: structured profile
         Facade->>Cache: store profile
     end
     Facade-->>BE: SpiritProfile / structured error
 
     BE->>Facade: get_type_matchup(["火", "翼"])
     Facade->>Cache: lookup type_matchup key
     Facade->>Static: read matchup matrix
     Static-->>Facade: matchup result
     Facade-->>BE: TypeMatchupResult
 ```
 
 **关键数据流说明**:
 1. 名称解析必须先于 wiki 请求完成，否则上游会在拼写偏差场景下频繁打空请求。
 2. 缓存命中应发生在外部请求之前，避免重复访问 BWIKI。
 3. 静态知识读取不应依赖 wiki，可独立完成并作为低风险兜底路径。
 4. 上游异常必须在离开数据层前转为领域错误，而不是把裸 HTTP / HTML 细节泄漏给后端。
 
 ### 4.4 建议目录结构
 
 ```text
 src/data-layer/
 ├── app/
 │   ├── facade.py
 │   ├── errors.py
 │   └── contracts.py
 ├── wiki/
 │   ├── gateway.py
 │   ├── parser.py
 │   ├── schemas.py
 │   └── endpoint_builder.py
 ├── spirits/
 │   ├── repository.py
 │   ├── name_resolver.py
 │   ├── alias_index.py
 │   └── fuzzy_matcher.py
 ├── static/
 │   ├── type_chart.py
 │   ├── mechanism_knowledge.py
 │   └── data/
 ├── cache/
 │   ├── registry.py
 │   └── key_builder.py
 └── main.py
 ```
 
 ---
 
 ## 5. 接口设计 (Interface Design)
 
 ### 5.1 操作契约表 (Operation Contracts)
 
 | 操作 | [REQ-XXX] | 前置条件 | 消耗/输入 | 产出/副作用 | 失败语义 |
 | ---- | :---: | ---- | ---- | ---- | :---: |
 | `resolve_spirit_name(query)` | [REQ-001], [REQ-004] | query 非空 | 用户输入名称 | 返回规范名、候选列表或歧义结果 | `SpiritNotFoundError` / `AmbiguousSpiritNameError` |
 | `get_spirit_profile(spirit_name)` | [REQ-001], [REQ-003], [REQ-004] | 名称可解析 | 精灵名称 | 返回结构化精灵资料；可能写入缓存 | `WikiUpstreamTimeoutError` / `WikiParseError`；**失败时必须携带 `wiki_url` 回退链接** |
 | `search_spirits(query, limit)` | [REQ-001], [REQ-004] | query 非空 | 搜索词、limit | 返回候选名称与置信度排序 | `SearchUnavailableError` |
 | `get_type_matchup(type_combo)` | [REQ-001], [REQ-003] | type_combo 合法 | 1-2 个属性类型 | 返回克制/被克制结果 | `InvalidTypeComboError` |
 | `get_static_knowledge(topic_key)` | [REQ-003], [REQ-004] | topic_key 在允许集合中 | 知识主题 key | 返回静态机制知识 | `KnowledgeTopicNotFoundError` |
 | `build_wiki_link(spirit_name)` | [REQ-004] | 名称已解析 | 规范精灵名 | 返回 BWIKI 页面链接 | `SpiritNotFoundError` |
 
 ### 5.2 跨系统接口协议 (Cross-System Interface)
 
 ```python
 class IDataLayerFacade(Protocol):
     async def resolve_spirit_name(self, query: str) -> dict: ...
     async def get_spirit_profile(self, spirit_name: str) -> dict: ...
     async def search_spirits(self, query: str, limit: int = 5) -> list[dict]: ...
     async def get_type_matchup(self, type_combo: list[str]) -> dict: ...
     async def get_static_knowledge(self, topic_key: str) -> dict: ...
     async def build_wiki_link(self, spirit_name: str) -> str: ...
 ```
 
 ### 5.3 对 `agent-backend-system` 的契约要求
 
 | 契约点 | 要求 |
 | ---- | ---- |
 | 数据形状 | 返回稳定字段，不暴露 wiki 原始模板噪声 |
 | 错误边界 | 用结构化错误类型表示“未找到 / 歧义 / 超时 / 解析失败” |
 | 名称候选 | 必须返回候选名称和可选置信度，便于后端追问用户 |
 | 回退链接 | 超时或解析失败场景**必须**提供 BWIKI 链接（`wiki_url`），这是强制契约而非可选建议 |
 | 静态知识 | 与 wiki 动态实体查询使用同一 facade，不让调用方感知来源差异 |
 
 ---
 
 ## 6. 数据模型 (Data Model)
 
 ### 6.1 核心实体 (Core Entities)
 
 ```python
 @dataclass
 class SpiritProfile:
     canonical_name: str
     display_name: str
     types: list[str]
     base_stats: dict[str, int]
     skills: list[dict]
     bloodline_type: str | None
     evolution_chain: list[dict]
     wiki_url: str
 
 
 @dataclass
 class SearchCandidate:
     canonical_name: str
     display_name: str
     score: float
     match_reason: str
 
 
 @dataclass
 class TypeMatchupResult:
     input_types: list[str]
     attack_advantages: list[dict]
     defense_weaknesses: list[dict]
     defense_resistances: list[dict]
 
 
 @dataclass
 class StaticKnowledgeEntry:
     topic_key: str
     title: str
     content: str
     source: str
 
 
 @dataclass
 class DataLayerErrorEnvelope:
     error_code: str
     message: str
     retryable: bool
     wiki_url: str  # 强制必填：失败时仅当名称完全无法解析时才允许为空字符串
     candidates: list[SearchCandidate] | None
 ```

 > *(配置常量详见 [L1 §1](./data-layer-system.detail.md#1-配置常量-config-constants) · 完整方法实现详见 [L1 §2-3](./data-layer-system.detail.md#2-核心数据结构完整定义-full-data-structures))*
 
 ### 6.2 实体关系图 (Entity Relationship)
 
 ```mermaid
 classDiagram
     class SpiritProfile {
         +str canonical_name
         +str display_name
         +list types
         +dict base_stats
         +list skills
         +str bloodline_type
         +list evolution_chain
         +str wiki_url
     }
     class SearchCandidate {
         +str canonical_name
         +str display_name
         +float score
         +str match_reason
     }
     class TypeMatchupResult {
         +list input_types
         +list attack_advantages
         +list defense_weaknesses
         +list defense_resistances
     }
     class StaticKnowledgeEntry {
         +str topic_key
         +str title
         +str content
         +str source
     }
     class DataLayerErrorEnvelope {
         +str error_code
         +str message
         +bool retryable
         +str wiki_url
         +list candidates
     }
 
     SearchCandidate --> SpiritProfile : resolves to
     SpiritProfile --> DataLayerErrorEnvelope : fallback link source
     StaticKnowledgeEntry --> TypeMatchupResult : supplements reasoning
 ```
 
 ### 6.3 数据模型说明 (Model Notes)
 
 - `SpiritProfile` 是上游最重要的领域对象，必须足够瘦身，避免把整页 wiki 内容灌入 Agent 上下文。
 - `SearchCandidate` 服务于查无结果与歧义澄清场景。
 - `TypeMatchupResult` 来自本地静态知识，不依赖网络读取。
 - `DataLayerErrorEnvelope` 是跨系统错误语义载体，而不是面向终端用户的最终文案。
 
 ---
 
 ## 7. 技术选型 (Technology Stack)

 | 层 | 技术 | 用途 |
 |----|------|------|
 | HTTP Client | `httpx.AsyncClient` | 访问 BWIKI / MediaWiki API |
 | Cache | `cachetools.TTLCache` | 内存 TTL 缓存，落实 ADR-002 |
 | Fuzzy Match | `rapidfuzz` | 名称相似度计算 |
 | Parsing | Python parser / schema adapters | wiki 原始结构解析 |
 | Static Knowledge | JSON / Python module | 属性克制与机制知识 |
 | Config | 环境变量 + 本地配置文件 | API 超时、缓存大小、知识源路径 |
 
 ### 7.1 关键配置约束
 
 | 配置项 | 值/策略 | 原因 |
 |-------|---------|------|
 | `wiki_request_timeout_seconds` | `5` | 对齐 PRD 中 BWIKI 超时边界 |
 | `spirit_profile_ttl_seconds` | `3600` | 遵循 ADR-002 |
 | `search_result_ttl_seconds` | `600` | 遵循 ADR-002 |
 | `cache_max_entries` | `500` | 遵循 ADR-002 |
 | `http_retry_policy` | v2 默认不做复杂自动重试，仅快速失败 | 避免放大上游负载 |
| `rate_limit_min_interval` | `1.0` (秒) | 遵守 MediaWiki API Etiquette，防止封禁 |
| `backoff_base` / `backoff_max` | `2.0` / `30.0` (秒) | 连续失败时指数退避，自动降压 |
 | `fuzzy_match_limit` | `5` | 控制候选数量，便于上游追问 |
 
 ---
 
 ## 8. Trade-offs & Alternatives
 
 ### 8.1 ADR 引用清单
 
 > **决策来源**: [ADR-001: 技术栈选择（v2）](../03_ADR/ADR_001_TECH_STACK.md)
 >
 > 本系统实现 ADR-001 中“低运维复杂度、个人开发者可维护”的总体技术路线，因此维持 Python 单体内的轻量数据适配层，不在此重复整体技术栈选型理由。
 
 > **决策来源**: [ADR-002: 数据层缓存策略（v2）](../03_ADR/ADR_002_DATA_LAYER_CACHE.md)
 >
 > 本系统严格遵循 `cachetools` 内存 TTL Cache、精灵详情 1 小时、搜索结果 10 分钟、最大 500 条的缓存约束，不在此重复缓存后端选型理由。
 
 ### 8.2 本系统特有决策 1：为什么采用“领域适配层”，而不是直接暴露 MediaWiki 原始响应
 
 - **选择 A**: 解析后输出稳定领域对象
 - **不选 B**: 直接把 wiki 原始 JSON 交给 `agent-backend-system`
 
 **原因**:
 - 上游系统需要的是配队推理可消费的数据，不是页面结构细节。
 - 直接暴露原始响应会让解析逻辑渗透到多个系统，形成耦合污染。
 - 领域适配层更适合做缓存、错误分类与契约测试。
 
 ### 8.3 本系统特有决策 2：为什么名称解析放在数据层，而不是 Agent Prompt
 
 - **选择 A**: 数据层集中实现名称规范化、别名和模糊候选
 - **不选 B**: 让 LLM 在 Prompt 中猜测相似名称
 
 **原因**:
 - 名称解析属于确定性、可测试逻辑，不应交给概率模型临场发挥。
 - 这直接决定 `REQ-001` / `REQ-004` 的异常处理是否稳定。
 - 放在数据层后，上游只消费“已解析 / 有候选 / 需确认”三种清晰状态。
 
 ### 8.4 本系统特有决策 3：为什么 v2 不引入 Redis
 
 - **选择 A**: 单进程内存 TTL Cache
 - **不选 B**: Redis 共享缓存
 
 **原因**:
 - v2 的部署规模与 ADR-002 已明确支持简单优先。
 - Redis 会引入额外服务、连接管理和运维负担，而当前收益不足。
 - 缓存重启丢失只影响首批请求延迟，不影响数据正确性。
 
 ### 8.5 本系统特有决策 4：为什么静态知识与动态 wiki 查询要走统一 facade
 
 - **选择 A**: 统一数据层入口
 - **不选 B**: 让后端分别调用 wiki 客户端和本地知识文件
 
 **原因**:
 - 调用方不应感知数据来源差异，否则职责边界会被打穿。
 - 统一 facade 更容易做错误边界、缓存策略和未来替换。
 - 这让 `agent-backend-system` 维持“只依赖数据契约，不依赖数据来源”的简单心智模型。
 
 ---
 
 ## 9. 安全性考虑 (Security Considerations)
 
 - **外部访问约束**
   - 仅访问受控 BWIKI / MediaWiki API 端点
   - 不允许构造任意外部 URL 请求，避免演化为通用代理
 - **输入安全**
   - 对精灵名、查询词和属性组合做白名单化校验与长度限制
   - 避免把用户原始输入直接拼接进复杂查询参数
 - **错误暴露控制**
   - 对上游仅返回结构化错误与必要回退链接
   - 不把底层 HTML、完整堆栈和内部解析细节外泄给调用方
 - **静态知识可信边界**
   - 本地静态数据文件应纳入版本控制，不允许运行时远程覆盖
 
 ---
 
 ## 10. 性能考虑 (Performance Considerations)
 
 - **缓存优先**: 对高频精灵查询和搜索候选优先命中 TTL 缓存
 - **名称前置解析**: 先做规范化和候选缩小，减少空打 BWIKI 的概率
 - **响应瘦身**: 只返回 Agent 真正需要的字段，控制上下文膨胀
 - **静态知识本地化**: 属性克制与机制知识走本地读取，避免无意义外部 I/O
 - **快速失败**: 超时应在 5 秒边界内尽早返回，给上游留下降级空间
 - **有限并发**: WikiGateway 已实现 in-flight 去重（同一精灵并发查询复用同一 Future）+ Semaphore(1) 速率限制 + 指数退避
 
 ---
 
 ## 11. 测试策略 (Testing Strategy)
 
 ### 11.1 单元测试
 - `Name Resolver`: 规范化、别名、模糊候选排序、候选上限
 - `Cache Registry`: 不同 query type 的 key 生成与 TTL 失效
 - `Type Matchup Store`: 属性组合计算正确性
 - `Wiki Parser`: 样本页面解析到 `SpiritProfile` 的字段映射
 - `Error Mapper`: 超时、查无结果、歧义、解析失败的错误分类
 
 ### 11.2 集成测试
 - `get_spirit_profile()` 在缓存 miss / hit 两种路径都返回稳定结构
 - BWIKI 请求超时时返回结构化错误并附可用 wiki 链接
 - 查询简称或别名时能输出候选或规范名
 - 静态属性克制查询不依赖网络仍可完成
 - `agent-backend-system` 能稳定消费 `data-layer-system` 返回结构
 
 ### 11.3 契约测试
 - 校验 `SpiritProfile` 字段集合对上游保持稳定
 - 校验 `SearchCandidate` 至少包含名称、分数和匹配原因
 - 校验错误对象包含 `error_code`, `message`, `retryable`
 - 校验 `REQ-001` / `REQ-004` 所需候选推荐语义可从返回结构中构造
 
 ### 11.4 验收测试
 - 对照 [REQ-001]：查不到精灵时能给出相似名称建议
 - 对照 [REQ-003]：6 只精灵技能调优所需资料可稳定获取
 - 对照 [REQ-004]：单只精灵资料查询返回种族值、系别、技能、血脉、进化链与 BWIKI 链接
 - 对照 PRD 完成标准：重复查询不重复请求外部接口
 
 ---
 
 ## 12. 部署与运维 (Deployment & Operations)
 
 ### 12.1 部署约束
 - 作为 Python 进程内模块被 `agent-backend-system` 调用，或与其同仓部署
 - 不单独引入缓存中间件
 - 通过环境变量注入 BWIKI API 基础地址、超时和缓存配置
 
 ### 12.2 启动前检查
 - 本地静态知识文件存在且可读取
 - BWIKI API 基础地址配置正确
 - 缓存配置与超时配置可解析
 - 必要别名表或最小候选词表存在初始版本
 
 ### 12.3 运行时监控
 - `wiki_request_count`, `wiki_timeout_count`, `wiki_parse_error_count`
 - `cache_hit_count`, `cache_miss_count`, `cache_eviction_count`
 - `name_resolution_ambiguity_count`, `spirit_not_found_count`
 - `type_matchup_query_count`, `static_knowledge_hit_count`
 
 ---
 
 ## 13. 未来考虑 (Future Considerations)
 
 - v3+ 若出现多 worker / 多副本需求，可将 `Cache Registry` 替换为 Redis 实现，但保持 facade 契约不变
 - 为 BWIKI 页面模板变化建立样本回归测试集
 - 增加人工维护的精灵别名表与简称词典
 - 评估是否需要独立 `spirit-index` 离线构建步骤（一次性抓取全部精灵数据缓存到本地），以进一步降低对 BWIKI 的运行时依赖
 
 ---
 
 ## 14. 附录 (Appendix)
 
 ### 14.1 外部来源
 - BWIKI 精灵图鉴: https://wiki.biligame.com/rocokingdomworld/%E7%B2%BE%E7%81%B5%E5%9B%BE%E9%89%B4 （访问于 2026-04-07；URL 前缀于 2026-04-10 修正: rocom → rocokingdomworld）
- BWIKI 首页: https://wiki.biligame.com/rocokingdomworld/%E9%A6%96%E9%A1%B5 （访问于 2026-04-07）
 - MediaWiki API Etiquette: https://www.mediawiki.org/wiki/API:Etiquette （访问于 2026-04-07，本次正文抓取超时）
 - MediaWiki API Caching Data: https://www.mediawiki.org/wiki/API:Caching_data/en （访问于 2026-04-07，本次正文抓取超时）
 - cachetools GitHub: https://github.com/tkem/cachetools （搜索结果访问于 2026-04-07）
 
 ### 14.2 本地文档参考
 - `d:\PROJECTALL\ROCO\.anws\v2\01_PRD.md`
 - `d:\PROJECTALL\ROCO\.anws\v2\02_ARCHITECTURE_OVERVIEW.md`
 - `d:\PROJECTALL\ROCO\.anws\v2\03_ADR\ADR_001_TECH_STACK.md`
 - `d:\PROJECTALL\ROCO\.anws\v2\03_ADR\ADR_002_DATA_LAYER_CACHE.md`
 - `d:\PROJECTALL\ROCO\.anws\v2\04_SYSTEM_DESIGN\agent-backend-system.md`
 
 ### 14.3 设计拆分检测
 
 | 规则 | 结果 |
 |------|------|
 | R1 单个函数/算法伪代码 > 30 行 | ❌ |
 | R2 所有代码块合计 > 200 行 | ❌ |
 | R3 配置常量字典条目 > 5 个 | ❌ |
 | R4 版本历史注释 > 5 处 | ❌ |
 | R5 文档总行数 > 500 行 | ✅ |
 
 **结论**: 触发 R5，已创建 [data-layer-system.detail.md](./data-layer-system.detail.md) 作为实现层补充文档。
