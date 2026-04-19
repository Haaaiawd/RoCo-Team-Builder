# 探索报告: data-layer-system

**日期**: 2026-04-07
**探索者**: Cascade / Explorer
**系统**: `data-layer-system`

---

## 1. 问题与范围

**核心问题**: 如何为 `data-layer-system` 设计一个面向 `agent-backend-system` 的稳定数据访问层，使其既能从 BWIKI / MediaWiki API 获取精灵实时数据，又能在 v2 的单机单进程约束下通过简单缓存、名称规范化和模糊匹配提供低延迟、低脆弱性的结构化数据能力。

**探索范围**:
- 包含: BWIKI 访问模式、MediaWiki API 客户端礼仪、TTL 缓存策略、名称规范化与模糊匹配、数据瘦身与错误映射
- 不包含: `agent-backend-system` 的会话管理、`spirit-card-system` 的 HTML 渲染、`web-ui-system` 的前端交互与壳层裁剪

---

## 2. 核心洞察 (Key Insights)

1. **`data-layer-system` 应被设计为“受控数据适配层”，而不是 BWIKI 原始代理**: 上游 MediaWiki 数据结构天然偏通用、字段噪声高，后端真正需要的是稳定的领域对象，如 `SpiritProfile`、`SearchCandidate`、`TypeMatchupResult`，而不是把 wiki 原始 JSON 直接灌给 Agent。
2. **缓存不是性能优化附属品，而是外部依赖防抖层**: ADR-002 已经明确 v2 使用 `cachetools` TTL Cache；对 `data-layer-system` 而言，缓存的价值不只是缩短延迟，更是减少重复访问 BWIKI、降低外部站点抖动对整条推理链的放大效应。
3. **名称规范化 + 模糊匹配必须前置到数据层，而不是散落到 Agent Prompt**: `REQ-001` 与 `REQ-004` 都要求支持查不到时给出相似名称建议；这属于可测试的数据访问契约，应该由 `data-layer-system` 输出候选，而不是把“猜名字”交给 LLM 临场发挥。
4. **应区分“可缓存的读取结果”与“不可缓存的失败类型”**: 成功返回的精灵详情、搜索结果、属性克制表适合 TTL 缓存；但超时、解析异常、上游 5xx 不能盲目长时间缓存，否则会把短暂故障固化成系统错误。
5. **v2 的正确复杂度上限是“同步领域模型 + 异步 I/O + 内存缓存”，而不是 Redis / 搜索引擎 / 离线镜像**: 当前项目规模与 ADR 明确要求简单优先，因此应把复杂度集中在“结构化解析与错误边界”上，而不是引入额外基础设施。

---

## 3. 详细发现

### 3.1 BWIKI / MediaWiki 访问模式

**探索方式**: 🔍 PRD + MediaWiki 官方文档摘要

**发现**:
- PRD 已把 BWIKI 定义为精灵实时数据来源，并明确要求 `REQ-001` ~ `REQ-004` 依赖该数据层。
- MediaWiki API 天然是通用内容接口，不直接等价于产品领域模型；若不做适配，调用方会被模板、页面结构、字段差异污染。
- MediaWiki 官方 `API:Etiquette` 与 `API:Caching_data` 页面都强调客户端应避免不必要的高频请求、合理利用缓存、对上游负载保持克制。

**结论**:
- `data-layer-system` 不能暴露“任意 wiki 查询”给上游系统，而应只暴露有限、稳定、领域化的操作契约。
- 读取路径应优先通过“规范化名称 → 结构化查询 → 结果瘦身”的三段式完成。

### 3.2 缓存策略的系统意义

**探索方式**: 🔍 ADR + 搜索结果摘要

**发现**:
- ADR-002 已确定：v2 使用 `cachetools` 内存 TTL Cache；精灵详情 TTL 1 小时、搜索结果 TTL 10 分钟、最大 500 条。
- `cachetools` 的 `TTLCache` 适合当前单机单进程、零额外依赖的部署方式。
- 对外部 wiki 场景，缓存的意义不仅是快，更是“消峰”和“抗抖动”。

**结论**:
- 设计上应把缓存放在 `WikiGateway` 之后、领域解析之前或之后做明确分层，而不是零散地在函数装饰器里到处缓存。
- v2 应至少区分三类缓存键：`spirit_profile`、`search_candidates`、`wiki_page_extract` / `type_matchup`。

### 3.3 名称规范化与模糊匹配

**探索方式**: 🔍 PRD + 内部推理

**发现**:
- `REQ-001` 明确要求“未找到该精灵时给出相似名称建议”。
- `REQ-004` 明确要求简称、别名时尝试模糊匹配，多个候选时列出确认。
- 如果把这件事交给 `agent-backend-system` 或 Prompt，行为会变得不可预测，也难做契约测试。

**结论**:
- `data-layer-system` 需要明确提供 `resolve_spirit_name()` / `search_spirits()` 这类领域操作。
- 名称流程应拆成：输入清洗、规范化、精确命中、别名表命中、模糊候选排序、置信度分层返回。

### 3.4 错误分类与降级

**探索方式**: 🔍 PRD + 内部推理

**发现**:
- `REQ-004` 要求 BWIKI 超时（>5s）时，Agent 能说明暂时无法获取并提供 BWIKI 链接。
- 这说明 `data-layer-system` 不应只抛出裸异常，而要返回可映射的结构化错误语义。
- 对 Agent 来说，最重要的不是 HTTP 细节，而是“查无此精灵”“候选不唯一”“上游暂时不可用”三类业务级差异。

**结论**:
- 需要统一错误模型，如 `SpiritNotFoundError`、`AmbiguousSpiritNameError`、`WikiUpstreamTimeoutError`、`WikiParseError`。
- 应为“超时”保留 BWIKI 页面链接或候选页面标题，支持上游生成更友好的回退文案。

### 3.5 静态知识与动态 wiki 的边界

**探索方式**: 🔍 ADR + PRD + 内部推理

**发现**:
- Architecture Overview 已把 `data-layer-system` 职责写明为“BWIKI 客户端 + 本地缓存 + 静态知识”。
- PRD 也指出属性克制矩阵、核心机制知识由开发者手动维护更新，而不是实时抓取。
- 这意味着数据层不是单一 API 客户端，而是“动态源 + 静态源”的统一访问面。

**结论**:
- 属性克制、血脉/机制等低频变化知识，应由本地静态知识库承担权威读取；BWIKI 只负责高波动实体数据。
- `agent-backend-system` 不应该感知数据来自 BWIKI 还是本地静态表；它只依赖数据层契约。

### 3.6 推荐架构模式

**探索方式**: 🔍🧠 混合

**发现**:
- 若直接把 `httpx` + `cachetools` 散落在多个函数里，解析逻辑、缓存键、异常边界会迅速失控。
- 更稳的模式是：`Gateway` 负责 HTTP；`Parser` 负责页面/模板抽取；`Repository/Service` 负责领域契约；`StaticKnowledgeStore` 负责本地表。

**结论**:
- v2 推荐采用“分层数据适配架构”：
  - `WikiGateway`: 与 MediaWiki API 通信
  - `WikiParser`: 解析原始结构
  - `SpiritRepository`: 对外提供精灵查询契约
  - `TypeChartStore`: 提供静态属性克制与机制知识
  - `NameResolver`: 负责规范化与模糊匹配
  - `DataCacheRegistry`: 统一缓存策略与 key 规范

---

## 4. 方案清单

| 方案 | 描述 | 可行性 | 风险 | 推荐度 |
|------|------|:------:|:----:|:------:|
| A | `httpx` + `cachetools` + 分层领域适配（Gateway / Parser / Repository / Static Store） | 高 | 低中 | ⭐⭐⭐⭐⭐ |
| B | 直接函数式调用 MediaWiki API + 局部缓存装饰器 | 高 | 中 | ⭐⭐ |
| C | 引入 Redis 做跨请求缓存与共享 | 中 | 中高 | ⭐⭐ |
| D | 预抓取全量 wiki 到本地数据库后离线查询 | 低 | 高 | ⭐ |

**推荐**: 方案 A

---

## 5. 行动建议

| 优先级 | 建议 | 理由 |
|:------:|------|------|
| P0 | 定义面向后端的稳定契约：精灵详情、搜索候选、属性克制、静态机制知识 | 避免 `agent-backend-system` 直接绑定 wiki 原始结构 |
| P0 | 严格落实 ADR-002 的 TTL 缓存与缓存键规范 | 减少外部依赖抖动，控制重复请求 |
| P0 | 在数据层集中实现名称规范化、别名表与模糊候选输出 | 满足 `REQ-001` / `REQ-004` 的可测试需求 |
| P0 | 为 BWIKI 超时、查无结果、解析失败定义结构化错误模型 | 让上层能稳定生成用户可理解的回退文案 |
| P1 | 为静态属性克制表与动态 wiki 实体查询做清晰边界分层 | 防止职责污染 |
| P1 | 加入有限并发保护与请求超时预算 | 防止单次抖动拖垮整轮推理 |
| P2 | 为 v3+ 预留缓存后端替换接口（Redis） | 不改变上层契约即可升级 |

---

## 6. 局限性与待探索

- MediaWiki 官方页面本次抓取时出现 TLS 超时，相关结论依赖搜索摘要与该类官方页面标题/描述交叉判断，后续可在网络稳定时补充正文核验。
- 尚未实际验证 BWIKI 每个精灵页面模板字段的稳定性，解析器实现时仍需结合样本页再细化。
- 尚未建立正式别名词表，v2 需要先定义人工维护入口或最小静态字典。
- 尚未对 BWIKI 的异常状态码与返回体做实测采样，错误映射仍需 `/forge` 阶段补契约测试。

---

## 7. 参考来源

1. BWIKI 精灵图鉴: https://wiki.biligame.com/rocom/%E7%B2%BE%E7%81%B5%E5%9B%BE%E9%89%B4 （访问于 2026-04-07）
2. BWIKI 首页: https://wiki.biligame.com/rocom/%E9%A6%96%E9%A1%B5 （访问于 2026-04-07）
3. MediaWiki API Etiquette: https://www.mediawiki.org/wiki/API:Etiquette （访问于 2026-04-07，本次正文抓取超时）
4. MediaWiki API Caching Data: https://www.mediawiki.org/wiki/API:Caching_data/en （访问于 2026-04-07，本次正文抓取超时）
5. ADR-002: `d:\PROJECTALL\ROCO\.anws\v2\03_ADR\ADR_002_DATA_LAYER_CACHE.md`
6. cachetools GitHub: https://github.com/tkem/cachetools （搜索结果访问于 2026-04-07）
7. PRD: `d:\PROJECTALL\ROCO\.anws\v2\01_PRD.md`
8. Architecture Overview: `d:\PROJECTALL\ROCO\.anws\v2\02_ARCHITECTURE_OVERVIEW.md`
