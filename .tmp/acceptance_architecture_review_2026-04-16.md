# RoCo Team Builder 静态交付验收 / 架构审查报告

- **审查日期**: 2026-04-16
- **审查方式**: 纯静态审查
- **工作目录**: `d:\PROJECTALL\ROCO`
- **执行约束**: 未启动项目、未运行 Docker、未运行测试、未修改代码

---

## 1. 总结结论

- **Overall conclusion**: **Fail**

- **核心结论**
  - **[Blocker]** `REQ-002` 截图识别仍是明确标注的骨架实现，未达到 PRD 要求的多模态识别能力。证据：`.anws/v2/01_PRD.md:81-90`, `src/agent_backend/runtime/recognition_tool.py:42-74`
  - **[High]** 后端公开暴露在宿主机 `8000` 端口，并直接信任来路未验证的 `X-OpenWebUI-User-Id` / `X-OpenWebUI-Chat-Id` 作为会话与额度身份，导致会话隔离与额度归属可被伪造。证据：`docker-compose.yml:11-12`, `src/agent_backend/app/session_service.py:65-92`, `src/agent_backend/api/routes_openai.py:80-113`
  - **[High]** BYOK 轨道的本地持久化契约未闭合：需求要求 Key 保存在 `localStorage`，但实现保存前将 `api_key` 替换为 `***`，读取时再清空，等于并未持久化可用 Key。证据：`.anws/v2/01_PRD.md:58-59`, `.anws/v2/01_PRD.md:198-215`, `.anws/v2/05_TASKS.md:393-405`, `src/web-ui-shell/settings/byok/config.ts:102-129`
  - **[High]** `web-ui-shell` 的交付在静态上缺少“已装配到 Open WebUI 主路径”的闭环证据；README、前端 README 与 E2E 契约彼此不一致，导致评审者无法在不补核心接线代码的前提下验证 `REQ-006`。证据：`README.md:90-112`, `src/web-ui-shell/README.md:95-98`, `tests/e2e/product-shell.spec.ts:21-41`, `tests/e2e/product-shell.spec.ts:60-111`, `tests/e2e/visible-feature-policy.spec.ts:76-100`

---

## 2. 审查范围与静态验证边界

- **审查了什么**
  - 根文档与配置：`README.md:9-155`, `.env.example:1-58`, `docker-compose.yml:1-55`, `pyproject.toml:1-34`
  - 需求与架构：`.anws/v2/01_PRD.md:12-255`, `.anws/v2/02_ARCHITECTURE_OVERVIEW.md:10-264`, `.anws/v2/05_TASKS.md:49-500`
  - 后端实现：`src/agent_backend/main.py:1-104`, `src/agent_backend/api/routes_openai.py:1-240`, `src/agent_backend/app/*.py`, `src/agent_backend/runtime/*.py`
  - 前端壳层实现：`src/web-ui-shell/**/*.ts`, `src/web-ui-shell/README.md:1-111`
  - 测试：`tests/unit/*.py`, `tests/integration/*.py`, `tests/e2e/*.ts`, `tests/conftest.py:1-10`

- **没有审查什么**
  - `references/` 下的参考仓库运行状态与集成细节
  - 外部服务真实行为：BWIKI、OpenRouter、Open WebUI 容器内部运行时装配
  - 浏览器实际渲染结果与视觉一致性运行态

- **有意未执行什么**
  - 未运行 `pytest`
  - 未运行 Playwright
  - 未启动 Docker / Compose
  - 未发起任何网络请求

- **哪些结论需要人工验证**
  - `web-ui-shell` 资产是否在真实 Open WebUI 容器内另有额外挂载/注入步骤；当前仓库内**无法通过静态审查确认**。相关边界：`docker-compose.yml:30-45`, `src/web-ui-shell/README.md:59-98`
  - 视觉主题、Rich UI 卡片与白名单裁剪在真实浏览器中的表现；当前只能确认样式与宿主代码存在，不能确认运行效果。证据：`src/web-ui-shell/shell/layout/theme-config.ts:148-439`, `src/web-ui-shell/integrations/rich-ui/host.ts:29-158`

---

## 3. 仓库 / 需求映射摘要

- **Prompt 边界**
  - 用户提供的 `{prompt}` 实际为空占位符；因此本次“Prompt 映射”只能以仓库内可追溯需求代理为准：`README.md:1-6`, `.anws/v2/01_PRD.md:12-49`, `.anws/v2/01_PRD.md:64-153`

- **核心业务目标 / 流程 / 约束（按 PRD 代理）**
  - 文字配队与技能调优：`.anws/v2/01_PRD.md:66-109`
  - 截图识别并基于已拥有精灵约束推荐：`.anws/v2/01_PRD.md:81-94`
  - 单精灵资料查询与 Rich UI 卡片：`.anws/v2/01_PRD.md:112-123`
  - 多轮会话隔离：`.anws/v2/01_PRD.md:126-137`
  - 受控 Open WebUI 产品壳层 + BYOK 双轨：`.anws/v2/01_PRD.md:140-153`, `.anws/v2/01_PRD.md:196-215`

- **主要实现区域**
  - `agent-backend-system`: `src/agent_backend/main.py:96-103`, `src/agent_backend/api/routes_openai.py:64-239`
  - `data-layer-system`: `src/data_layer/app/facade.py`（经测试与客户端间接验证），`tests/integration/test_t322_tool_integration.py:87-124`
  - `spirit-card-system`: `tests/integration/test_t322_tool_integration.py:140-166`
  - `web-ui-system`: `src/web-ui-shell/guards/feature-whitelist/policy.ts:73-284`, `src/web-ui-shell/settings/byok/config.ts:13-155`, `src/web-ui-shell/chat/composer/message-composer.ts:42-152`

---

## 4. 分章节审查结果

### 1.1 文档与静态可验证性

- **结论**: **Fail**
- **理由**: 根 README 提供了启动、测试与部署说明，但核心前端交付链条在静态上不自洽：根 README 让评审者在 `src/web-ui-shell` 下执行前端安装与测试，而前端 README 又明确说明“当前项目尚未配置前端测试环境”；与此同时，E2E 用例依赖具体 DOM、`window.rocoPolicy` 与截图夹具，但这些契约在当前仓库里缺少完整装配证据。
- **证据**:
  - `README.md:90-112`
  - `src/web-ui-shell/README.md:95-98`
  - `tests/e2e/product-shell.spec.ts:21-41`
  - `tests/e2e/product-shell.spec.ts:60-111`
  - `tests/e2e/visible-feature-policy.spec.ts:76-100`
- **人工验证建议**: 需要人工确认真实 Open WebUI 容器内是否存在未纳入当前仓库的接线步骤；若没有，则当前交付不满足“无需先改核心代码即可尝试验证”的硬门槛。

### 1.2 是否与 Prompt 发生实质偏离

- **结论**: **无法通过静态审查确认**
- **理由**: 用户输入的 `{prompt}` 为空，无法与“唯一依据的业务 Prompt”逐条对照；仅能确认仓库实现总体围绕 PRD 中的配队、截图识别、卡片查询、BYOK 与产品壳层展开。
- **证据**:
  - `README.md:1-6`
  - `.anws/v2/01_PRD.md:40-49`
  - `.anws/v2/01_PRD.md:64-153`
- **人工验证建议**: 若存在外部原始任务 Prompt，应补充后再做一次严格映射。

### 2.1 是否完整覆盖 Prompt 中明确提出的核心需求

- **结论**: **Fail**
- **理由**: `REQ-002` 是 P0 需求，但当前截图识别工具明确自述为“骨架实现”，且依旧使用硬编码 `if` 链；此外，BYOK 本地存储契约未闭合，会影响双轨核心路径可用性。
- **证据**:
  - `.anws/v2/01_PRD.md:81-90`
  - `.anws/v2/01_PRD.md:243-255`
  - `src/agent_backend/runtime/recognition_tool.py:42-74`
  - `src/web-ui-shell/settings/byok/config.ts:102-129`
- **人工验证建议**: 先补齐截图识别真实实现与 BYOK 持久化，再做运行验收。

### 2.2 是否构成一个从 0 到 1 的基础可交付项目

- **结论**: **Partial Pass**
- **理由**: 仓库具备完整后端、数据层、卡片系统、Compose、架构文档与测试目录；但前端壳层在静态上更像“工具/策略模块集合”，而非已接入 Open WebUI 主路径的可直接验证产品壳层，因此整体交付闭环不完整。
- **证据**:
  - `pyproject.toml:1-34`
  - `docker-compose.yml:4-55`
  - `src/agent_backend/main.py:96-103`
  - `src/web-ui-shell/chat/composer/message-composer.ts:42-152`
  - `src/web-ui-shell/integrations/agent-backend-connection/client.ts:51-166`
  - `src/web-ui-shell/integrations/rich-ui/host.ts:29-158`
- **人工验证建议**: 补充壳层装配入口、前端运行说明与最小验证路径。

### 3.1 项目结构与模块划分是否与问题规模相匹配

- **结论**: **Pass**
- **理由**: 四系统边界清晰，模块职责基本合理，后端/数据层/卡片系统各自分层明确；没有明显把大量核心逻辑塞进单文件。
- **证据**:
  - `AGENTS.md:125-187`
  - `.anws/v2/02_ARCHITECTURE_OVERVIEW.md:43-164`
  - `src/agent_backend/main.py:1-104`
- **人工验证建议**: 无。

### 3.2 是否具备基本可维护性和可扩展性

- **结论**: **Partial Pass**
- **理由**: 后端与数据层具备较好的契约化和分层；但 `web-ui-shell` 存在“需求契约强、装配闭环弱”的问题，导致可维护性更多停留在模块设计层，而非已验证的产品集成层。
- **证据**:
  - `src/agent_backend/app/request_normalizer.py:22-63`
  - `src/agent_backend/app/quota_guard.py:22-191`
  - `src/web-ui-shell/guards/feature-whitelist/policy.ts:73-284`
  - `src/web-ui-shell/navigation/filter.ts:58-158`
- **人工验证建议**: 补全实际装配入口后再评估前端维护性。

### 4.1 工程细节与专业度

- **结论**: **Partial Pass**
- **理由**: 结构化错误映射、会话清理、配额/能力兜底、测试组织都体现出专业实践；但关键边界上仍有明显缺口：截图识别为骨架、会话身份信任边界缺失、前端测试环境未闭合。
- **证据**:
  - `src/agent_backend/api/routes_openai.py:86-127`
  - `src/agent_backend/app/request_normalizer.py:27-45`
  - `src/agent_backend/app/quota_guard.py:131-191`
  - `src/agent_backend/runtime/recognition_tool.py:42-74`
  - `src/web-ui-shell/README.md:95-98`
- **人工验证建议**: 先修复高风险边界问题，再补最小验收脚本。

### 4.2 项目是否更像真实产品 / 服务，而不是示例或演示级实现

- **结论**: **Fail**
- **理由**: 数据层、卡片层、OpenAI 兼容路由确实接近真实服务；但 P0 的截图识别仍是示例级骨架，前端壳层缺少静态可验证的装配闭环，整体尚未达到“可直接验收的真实产品”标准。
- **证据**:
  - `src/agent_backend/runtime/recognition_tool.py:44-74`
  - `tests/integration/test_t324_session_constraints.py:23-35`
  - `README.md:9-68`
  - `src/web-ui-shell/README.md:95-98`
- **人工验证建议**: 以 P0 路径优先补齐产品闭环，而非继续扩展辅助模块。

### 5.1 Prompt 理解与需求贴合度

- **结论**: **无法通过静态审查确认**
- **理由**: 原始 `{prompt}` 缺失，无法按“唯一依据”为其业务语义背书；如果以仓库内 PRD 代理，则实现方向大体贴合。
- **证据**:
  - `.anws/v2/01_PRD.md:40-49`
  - `.anws/v2/01_PRD.md:64-153`
  - `.anws/v2/02_ARCHITECTURE_OVERVIEW.md:16-39`
- **人工验证建议**: 补充原始 Prompt 再做最终贴合度评分。

### 6.1 美观度（前端 / 全栈适用）

- **结论**: **无法通过静态审查确认**
- **理由**: 主题变量、样式注入器与 Rich UI 宿主代码存在，但纯静态审查无法证明浏览器实际渲染质量、交互反馈与视觉统一性。
- **证据**:
  - `src/web-ui-shell/shell/layout/theme-config.ts:148-439`
  - `src/web-ui-shell/branding/theme-injector.ts:81-221`
  - `src/web-ui-shell/integrations/rich-ui/host.ts:29-158`
- **人工验证建议**: 需要浏览器端人工验证或可运行的前端验收环境。

---

## 5. Issues / Suggestions（按严重级别）

### Blocker

#### 1. 截图识别核心需求仍是硬编码骨架
- **Severity**: Blocker
- **Title**: `REQ-002` 未实现真实多模态识别
- **Conclusion**: Fail
- **Evidence**:
  - `.anws/v2/01_PRD.md:81-90`
  - `.anws/v2/01_PRD.md:243-245`
  - `src/agent_backend/runtime/recognition_tool.py:42-74`
  - `tests/integration/test_t324_session_constraints.py:23-35`
- **Impact**: P0 用户故事要求“上传截图 -> 调用多模态 LLM -> 展示识别清单 -> 用户确认”，但当前实现只是对 `image_description` 做硬编码关键词匹配；即使测试通过，也只能证明骨架逻辑，不代表真实截图识别可用。
- **Minimum actionable fix**:
  - 用真实多模态调用替换 `recognize_spirit_list` 的硬编码分支
  - 输出结构化候选 + 不确定项，并保留失败语义
  - 为真实识别流补最小契约测试（含正常、模糊、失败三条路径）
- **Minimum verification path**:
  - 人工上传一张包含多只精灵的样本截图，确认识别列表、`uncertain_items` 与后续 `owned_spirits` 约束链路闭合

### High

#### 2. 后端公开暴露且直接信任客户端提供的会话身份头
- **Severity**: High
- **Title**: 会话隔离与额度归属建立在可伪造头部之上
- **Conclusion**: Fail
- **Evidence**:
  - `docker-compose.yml:11-12`
  - `src/agent_backend/api/routes_openai.py:80-113`
  - `src/agent_backend/app/request_normalizer.py:41-63`
  - `src/agent_backend/app/session_service.py:65-92`
  - `src/agent_backend/app/quota_guard.py:41-45`
- **Impact**: 只要能直连公开的 `8000` 端口，就可以自定义 `X-OpenWebUI-User-Id` / `X-OpenWebUI-Chat-Id`，从而伪造 session key、污染他人会话、绕过按 session 计量的额度归属；这直接削弱 PRD 中多用户隔离与公网部署目标。`.anws/v2/01_PRD.md:43-45`, `.anws/v2/01_PRD.md:197-201`
- **Minimum actionable fix**:
  - 让后端只接受可信代理注入的身份，或在后端校验来自 Web UI 的可信令牌/签名
  - 若架构允许，取消对宿主机公开暴露 `8000`，改为仅容器内访问
  - 为“伪造头部访问 чужая session / 额度归属”补 401/403 级安全测试
- **Minimum verification path**:
  - 人工以非 Web UI 客户端直接请求 `POST /v1/chat/completions`，验证无法通过伪造头部访问或占用他人会话/额度

#### 3. BYOK Key 持久化契约未闭合
- **Severity**: High
- **Title**: 需求要求 Key 存于 `localStorage`，实现却主动抹除 Key
- **Conclusion**: Fail
- **Evidence**:
  - `.anws/v2/01_PRD.md:58-59`
  - `.anws/v2/01_PRD.md:198-215`
  - `.anws/v2/05_TASKS.md:393-405`
  - `src/web-ui-shell/settings/byok/config.ts:102-129`
- **Impact**: 产品契约要求用户 BYOK 配置保存在浏览器本地，不上传服务端；当前实现保存时把 `api_key` 改成 `***`，读取时再清空，意味着重开页面后并没有可用 Key，双轨体验与需求承诺不一致。
- **Minimum actionable fix**:
  - 明确设计：如果要真正支持“本地持久化可直接使用”，就必须在本地安全存储可用 Key
  - 如果出于安全考虑不做持久化，则必须同步修正文档、PRD、任务契约与 UI 文案，避免虚假承诺
  - 为保存/加载/重开页面后的 BYOK 可用性补前端集成测试
- **Minimum verification path**:
  - 人工保存 BYOK 配置，刷新页面后检查模型与 Key 是否仍能直接发起 BYOK 对话

#### 4. Web UI 壳层缺少静态可验证的装配闭环
- **Severity**: High
- **Title**: `REQ-006` 的交付更像工具模块集合，而非已接线产品壳层
- **Conclusion**: Fail on static verifiability
- **Evidence**:
  - `README.md:90-112`
  - `src/web-ui-shell/README.md:59-98`
  - `tests/e2e/product-shell.spec.ts:21-41`
  - `tests/e2e/product-shell.spec.ts:60-111`
  - `tests/e2e/visible-feature-policy.spec.ts:76-100`
  - `src/web-ui-shell/chat/composer/message-composer.ts:42-152`
  - `src/web-ui-shell/integrations/agent-backend-connection/client.ts:51-166`
  - `src/web-ui-shell/integrations/rich-ui/host.ts:29-158`
- **Impact**: 当前仓库能证明存在策略、过滤器、客户端与 HTML 生成器，但不足以证明这些模块已接入真实 Open WebUI 主路径；因此评审者即使不改核心代码，也难以按文档验证 `REQ-006`、截图前置拦截、白名单快照等前端主路径。
- **Minimum actionable fix**:
  - 补充明确的壳层装配入口、运行方式与注入点文档
  - 让 E2E 依赖的 `window.rocoPolicy`、DOM 选择器、截图夹具等在仓库内可追溯
  - 保证前端运行/测试环境自洽，不再出现“README 要求 npm test，但前端 README 又说测试环境未配置”的冲突
- **Minimum verification path**:
  - 评审者按仓库文档即可完成一次前端最小启动或静态构建，并能定位到白名单快照、BYOK 设置、消息输入与截图预检的真实装配入口

### Medium

#### 5. 前端文档与测试契约互相矛盾
- **Severity**: Medium
- **Title**: 前端开发/测试说明不一致，降低人工验证效率
- **Conclusion**: Partial Pass
- **Evidence**:
  - `README.md:92-111`
  - `src/web-ui-shell/README.md:95-98`
- **Impact**: 评审者无法判断应以根 README 还是前端 README 为准，直接削弱“从 clone 到验证”的交付可信度。
- **Minimum actionable fix**:
  - 统一前端开发/测试入口文档
  - 若前端测试环境未配置，应从根 README 删除或降级相关承诺

#### 6. 日志中直接输出原始 session key
- **Severity**: Medium
- **Title**: Session janitor 日志暴露 `user_id:chat_id`
- **Conclusion**: Partial Pass
- **Evidence**:
  - `src/agent_backend/main.py:33-39`
- **Impact**: 虽非密钥泄露，但会把用户/聊天标识直接写入日志，增加标识符暴露面，也不利于后续合规收敛。
- **Minimum actionable fix**:
  - 记录哈希化/截断后的会话标识，或仅记录数量与内部追踪 ID

---

## 6. 安全审查摘要

### 认证入口
- **结论**: **Fail**
- **理由**: 后端没有看到认证中间件、令牌校验或可信代理校验；请求只要带上头部即可进入会话解析与业务处理。
- **证据**: `src/agent_backend/main.py:96-103`, `src/agent_backend/api/routes_openai.py:80-113`, `src/agent_backend/app/request_normalizer.py:41-63`

### 路由级鉴权
- **结论**: **Fail**
- **理由**: `/v1/models` 与 `/v1/chat/completions` 无鉴权依赖；同时 Compose 将 `8000` 暴露给宿主机。
- **证据**: `src/agent_backend/api/routes_openai.py:64-80`, `src/agent_backend/api/routes_openai.py:217-239`, `docker-compose.yml:11-12`

### 对象级鉴权
- **结论**: **Fail**
- **理由**: 虽然 session key 使用 `user_id:chat_id` 分隔对象，但并未校验调用者是否有权声明该 `user_id/chat_id`。
- **证据**: `src/agent_backend/app/session_service.py:65-92`, `src/agent_backend/api/routes_openai.py:93-113`

### 函数级权限控制
- **结论**: **Partial Pass**
- **理由**: 有能力兜底与配额守卫，但这些控制建立在不可信身份之上，因此只能算部分有效。
- **证据**: `src/agent_backend/app/request_normalizer.py:36-45`, `src/agent_backend/app/quota_guard.py:131-191`, `src/agent_backend/app/capability_guard.py:26-58`

### 租户 / 用户数据隔离
- **结论**: **Partial Pass**
- **理由**: 代码实现了不同 `chat_id` 的会话隔离与锁，但信任边界缺失使这种隔离可被伪造请求绕过。
- **证据**: `src/agent_backend/app/session_service.py:95-146`, `tests/unit/test_session_service.py:158-199`

### 管理 / 内部 / 调试端点保护
- **结论**: **Pass**
- **理由**: 当前后端只暴露模型、聊天、健康与就绪检查，未发现额外管理/调试端点。
- **证据**: `src/agent_backend/api/routes_openai.py:64-80`, `src/agent_backend/api/routes_openai.py:217-239`

---

## 7. 测试与日志审查

### 单元测试
- **结论**: **Pass**
- **理由**: 存在成体系的单元测试，覆盖会话、请求归一化、工厂/工具注册等基础模块。
- **证据**: `pyproject.toml:27-33`, `tests/unit/test_request_normalizer.py:10-169`, `tests/unit/test_session_service.py:34-228`, `tests/unit/test_agent_factory.py:35-118`

### API / 集成测试
- **结论**: **Partial Pass**
- **理由**: 后端 API、卡片链路、配额/能力、流式与会话约束均有静态测试证据；但安全边界、真实截图识别、前端主路径与 E2E 环境仍明显不足。
- **证据**: `tests/integration/test_agent_backend_routes.py:126-219`, `tests/integration/test_t322_tool_integration.py:87-238`, `tests/integration/test_t324_session_constraints.py:22-128`, `tests/integration/test_t331_quota_capability_guards.py:26-200`, `tests/integration/test_t332_streaming.py:26-170`, `tests/e2e/product-shell.spec.ts:21-263`

### 日志分类 / 可观测性
- **结论**: **Partial Pass**
- **理由**: 有会话清理日志，但缺少可追踪的请求级审计/安全日志；日志体系更像局部埋点，而非完整观测方案。
- **证据**: `src/agent_backend/main.py:26-39`, `.anws/v2/02_ARCHITECTURE_OVERVIEW.md:259-264`

### 日志 / 响应中的敏感信息泄漏风险
- **结论**: **Partial Pass**
- **理由**: Provider API Key 通过环境变量读取，没有硬编码；但日志会输出原始 `session_key`，同时身份头完全由客户端声明，也放大了标识符与归属混淆风险。
- **证据**: `src/agent_backend/runtime/provider_factory.py:48-56`, `src/agent_backend/main.py:33-39`, `src/agent_backend/app/request_normalizer.py:46-63`

---

## 8. Test Coverage Assessment（静态审计）

### 8.1 测试概览

- **是否存在单元测试与 API / 集成测试**
  - 存在 Python 单元/集成测试与 TypeScript E2E 测试文件。证据：`pyproject.toml:27-33`, `tests/conftest.py:1-10`, `tests/e2e/product-shell.spec.ts:1-264`, `tests/e2e/visible-feature-policy.spec.ts:1-208`

- **测试框架**
  - Python: `pytest`。证据：`pyproject.toml:27-29`
  - 前端 E2E: `@playwright/test`。证据：`tests/e2e/product-shell.spec.ts:16`, `tests/e2e/visible-feature-policy.spec.ts:14`

- **测试入口**
  - Python 入口依赖 `tests/conftest.py` 将 `src/` 加入 `sys.path`。证据：`tests/conftest.py:5-10`
  - 文档中提供了测试命令，但前端 README 同时声明前端测试环境未配置。证据：`README.md:103-112`, `src/web-ui-shell/README.md:95-98`

### 8.2 覆盖映射表

| Requirement / Risk Point | 对应测试用例 | 关键断言 / Fixture | 覆盖结论 | Gap | Minimum Test Addition |
|---|---|---|---|---|---|
| `REQ-001` 文字配队 | `tests/unit/test_agent_factory.py:73-90` | 仅断言 Agent 名称与工具注册，未断言 6 只配队/补位说明 | insufficient | 没有验证 PRD 要求的 6 精灵方案、定位说明、未拥有追问 | 增加固定数据集下的端到端配队集成测试 |
| `REQ-002` 截图识别 | `tests/integration/test_t324_session_constraints.py:23-35` | 断言 `火神/水灵` 文本命中骨架逻辑 | insufficient | 仅覆盖硬编码文本分支，不覆盖真实图片/多模态调用 | 为真实识别器补图片样本与失败路径测试 |
| `REQ-003` 技能调优 | `tests/unit/test_agent_factory.py:92-109` | 仅断言技能调优 Agent 工具注册 | insufficient | 未验证“4 技能组合”“锁定部分技能不变” | 增加技能调优业务集成测试 |
| `REQ-004` 资料查询 + 卡片 | `tests/integration/test_t322_tool_integration.py:89-124`, `:142-166`, `:175-217` | 覆盖资料成功、BWIKI 超时降级、卡片成功/失败降级 | basically covered | 未验证浏览器宿主渲染效果 | 增加最小前端宿主契约测试 |
| `REQ-005` 多轮会话隔离 | `tests/unit/test_session_service.py:135-199`, `tests/integration/test_t332_streaming.py:119-170` | 覆盖 `owned_spirits` 持久、不同 chat 隔离、session lock 串行化 | basically covered | 未覆盖伪造头部越权场景 | 增加跨用户/伪造头部安全测试 |
| `REQ-006` 产品壳层 / 白名单 | `tests/e2e/product-shell.spec.ts:155-238`, `tests/e2e/visible-feature-policy.spec.ts:20-123` | 依赖 DOM selector、`window.rocoPolicy`、视觉断言 | cannot confirm | 仓库内前端测试环境与装配闭环不自洽 | 提供可运行前端 harness 或明确装配入口 |
| `QUOTA_ / CAPABILITY_` 语义 | `tests/integration/test_agent_backend_routes.py:168-218`, `tests/integration/test_t331_quota_capability_guards.py:98-118`, `:158-200` | 覆盖非视觉模型拒绝、额度耗尽、能力判断 | basically covered | 未覆盖真实 Provider `RATE_LIMIT_` 映射 | 增加 Provider 限流映射测试 |
| 鉴权 / 对象授权 / 401/403 | 未见对应测试 | 现有测试只验证缺头返回 `400 SESSION_MISSING_IDENTITY`：`tests/integration/test_agent_backend_routes.py:144-152` | missing | 即使现有测试全过，也不能说明存在有效鉴权 | 增加 401/403、伪造会话、跨用户访问测试 |

### 8.3 安全覆盖审计

- **认证**
  - **结论**: **missing**
  - **说明**: 当前测试只校验“缺少身份头 -> 400”，并未覆盖任何认证成功/失败语义。证据：`tests/integration/test_agent_backend_routes.py:144-152`

- **路由鉴权**
  - **结论**: **missing**
  - **说明**: 未见 401/403 级测试；现有路由测试默认任何客户端都可调用。证据：`tests/integration/test_agent_backend_routes.py:128-166`

- **对象级鉴权**
  - **结论**: **insufficient**
  - **说明**: 测试覆盖的是“不同 `chat_id` 不串线”，不是“调用者不能伪造他人 `user_id/chat_id`”。证据：`tests/unit/test_session_service.py:158-166`

- **租户 / 数据隔离**
  - **结论**: **insufficient**
  - **说明**: 覆盖了同用户不同 chat 的隔离与锁，但没有跨用户越权/伪造头部测试。证据：`tests/unit/test_session_service.py:158-199`, `tests/integration/test_t332_streaming.py:121-169`

- **管理 / 内部端点保护**
  - **结论**: **not applicable**
  - **说明**: 当前实现未发现额外管理/调试端点；仅有 `/healthz` 与 `/readyz`。证据：`src/agent_backend/api/routes_openai.py:217-239`

### 8.4 最终覆盖结论

- **Conclusion**: **Fail**

- **边界说明**
  - **已覆盖的主要风险**
    - 请求归一化、图片 part 保留、`CAPABILITY_` / `QUOTA_` 部分错误语义
    - Session registry、不同 chat 隔离、SSE chunk 编码与 mid-stream error 形状
    - 资料查询与卡片降级链路
  - **未覆盖且会导致“测试即使通过，严重缺陷仍可能存在”的风险**
    - 截图识别真实多模态能力未测试，因为实现本身仍是骨架
    - 401/403、对象级鉴权、伪造头部越权完全缺失
    - `REQ-006` 前端主路径与白名单/主题/BYOK UI 的真实接线无法由当前测试环境闭环证明

---

## 9. 最后说明

- 本报告遵循纯静态审查边界，只对**有直接证据的静态事实**给出强结论。
- 我没有把“未运行”本身当成缺陷；所有 Fail / High / Blocker 结论均建立在代码、文档或测试契约的直接证据上。
- 本次判断主要受以下已证实根因驱动：
  - `REQ-002` 骨架未完成
  - 后端信任边界缺失
  - BYOK 本地持久化契约失真
  - 前端壳层交付在静态上不可自证
