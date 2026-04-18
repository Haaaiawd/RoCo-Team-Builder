# 变更日志 - .anws v2

> 此文件记录本版本迭代过程中的微调变更（由 /change 处理）。新增功能/任务需创建新版本（由 /genesis 处理）。

## 格式说明
- **[ADD]** 新增内容
- **[CHANGE]** 微调已有任务（由 /change 处理）
- **[FIX]** 修复问题
- **[REMOVE]** 移除内容

---

## 2026-04-07 - 初始化
- [ADD] 创建 `.anws` v2 版本
- [CHANGE] 将前端系统提升为正式架构系统，要求后续单独设计
- [ADD] 新增 Open WebUI 裁剪与收敛的架构约束

## 2026-04-07 - UI 风格与系统设计细化
- [CHANGE] `web-ui-system`: 收敛为"复古冒险者手账风"产品壳层
  - 修改内容: 新增视觉约束、Theme Override Layer、CSS Variables / DOM selector map / Tailwind 组件拆解、UI 回归与验收标准
  - 影响范围: `.anws/v2/04_SYSTEM_DESIGN/web-ui-system.md`, `.anws/v2/04_SYSTEM_DESIGN/web-ui-system.detail.md`
  - PRD 追溯: [REQ-006], [REQ-004]
- [CHANGE] `spirit-card-system`: 与主 UI 统一卡片视觉语言
  - 修改内容: 新增卡片视觉约束、主题 token、`theme_name`、手账式卡片参考与测试要求
  - 影响范围: `.anws/v2/04_SYSTEM_DESIGN/spirit-card-system.md`, `.anws/v2/04_SYSTEM_DESIGN/spirit-card-system.detail.md`
  - PRD 追溯: [REQ-004]

## 2026-04-07 - Challenge Report 修复（第 2 轮）
- [FIX] **CH-06 [High]**: 为内置轨道额度限制补齐最小运行模型、产品错误语义与观测口径
  - 修改内容: PRD §6.2 / §7 / §8 明确 builtin quota 只作用于内置轨道，超限后返回 `QUOTA_` 并引导切 BYOK；Architecture Overview §1.3 / §2 / §3.5 / §3.6 补共享术语、`QUOTA_` 错误与 Builtin Quota 定义；agent-backend-system L0/L1 新增 BuiltinQuotaPolicy / State / Decision、额度检查契约、监控口径与决策顺序；web-ui-system §4.2 / §4.3 / §11 / §12 补前端额度提示与回归检查
  - 影响范围: `01_PRD.md`, `02_ARCHITECTURE_OVERVIEW.md`, `agent-backend-system.md`, `agent-backend-system.detail.md`, `web-ui-system.md`
- [FIX] **CH-07 [High]**: 把截图上传的视觉能力判断前移到发送前，并统一失败语义为 `CAPABILITY_`
  - 修改内容: PRD US-002 / §6.2 补发送前视觉能力校验；Architecture Overview §3.5 新增 `CAPABILITY_` 分类；web-ui-system L0/L1 新增 `preflight_image_capability`、截图发送前能力决策、BYOK 非视觉模型阻断逻辑；agent-backend-system L0/L1 将图片命中非视觉模型的后端兜底错误统一为 `CAPABILITY_`
  - 影响范围: `01_PRD.md`, `02_ARCHITECTURE_OVERVIEW.md`, `web-ui-system.md`, `web-ui-system.detail.md`, `agent-backend-system.md`, `agent-backend-system.detail.md`
- [FIX] **CH-08 [Medium]**: 指定白名单唯一验证资产，减少对白名单人工清单的依赖
  - 修改内容: Architecture Overview §2 / §3.6 将 `VisibleFeaturePolicy` 明确为白名单真理源；web-ui-system L0/L1 为 `VisibleFeaturePolicy` 增加导出快照/基线语义、发布前检查与监控指标；ADR-004 正式定义“真理源 → 唯一验证资产 → 发布比较物”三层关系
  - 影响范围: `02_ARCHITECTURE_OVERVIEW.md`, `web-ui-system.md`, `web-ui-system.detail.md`, `03_ADR/ADR_004_WEB_UI_PRUNING_STRATEGY.md`
- [FIX] 一致性修复: `agent-backend-system.detail.md` 移除 session key 回退逻辑，重新对齐 ADR-003 的严格拒绝模式
  - 修改内容: `resolve_session_key(...)` 改为缺少 `user_id` 或 `chat_id` 直接拒绝；更新相关测试、边缘情况与决策顺序文档
  - 影响范围: `agent-backend-system.detail.md`, `agent-backend-system.md`

## 2026-04-13 - 设计对齐修复（质疑报告 P0/P1 问题）
- [CHANGE] 添加 System 5: Design Alignment 修复任务
  - 用户原话: "批准，请先写入，change"（指代质疑报告中发现的 P0/P1 实现偏离问题）
  - 修改内容: 新增 6 个修复任务到 05_TASKS.md，包括 FIX-QUOTA-1/2（QuotaDecision/BuiltinQuotaPolicy 重构）、FIX-RUNTIME-1（run_agent_turn 签名对齐）、FIX-ROUTE-1（session.lock 保护）、FIX-SESSION-1（SessionRecordExtended 集成）、FIX-DOC-1（evict_idle_sessions 伪代码补齐）
  - 影响范围: `.anws/v2/05_TASKS.md`, `src/agent_backend/app/quota_guard.py`, `src/agent_backend/runtime/runtime_service.py`, `src/agent_backend/api/routes_openai.py`, `src/agent_backend/app/session_service.py`, `04_SYSTEM_DESIGN/agent-backend-system.detail.md`
  - PRD 追溯: [REQ-001], [REQ-002], [REQ-005]

## 2026-04-15 - Design Alignment 文档收口
- [CHANGE] 补齐 `FIX-DOC-1`：为 `agent-backend-system.detail.md` 添加 `evict_idle_sessions(registry, now)` 伪代码
  - 用户原话: "很好，那就补齐和收口吧" / "@[/change] 请继续吧"
  - 修改内容: 在 `§3 核心算法伪代码` 中新增 `§3.6 evict_idle_sessions(registry, now)`，明确 TTL 截止时间计算、待清理 key 收集、统一删除顺序与返回值，消除 janitor 行为的实现猜测空间
  - 影响范围: `.anws/v2/04_SYSTEM_DESIGN/agent-backend-system.detail.md`, `.anws/v2/06_CHANGELOG.md`
  - PRD 追溯: [REQ-005]

## 2026-04-16 - 架构审查报告修复
- [CHANGE] T3.2.4: 标记为未完成，添加骨架实现说明
  - 用户原话: "按照标准流程调用change等等吧" (基于架构审查报告)
  - 修改内容: 将 T3.2.4 从 [x] 改为 [ ]，添加 ⚠️ 注意说明当前 recognize_spirit_list 为硬编码骨架实现，需替换为真实多模态 LLM 调用
  - 影响范围: `.anws/v2/05_TASKS.md`
  - PRD 追溯: [REQ-002]
- [CHANGE] T4.1.2: 修正 BYOK 持久化验收标准
  - 修改内容: 修改验收标准，明确 API Key 真实保存在 localStorage（不替换为 ***），刷新页面后可读取使用
  - 影响范围: `.anws/v2/05_TASKS.md`
  - PRD 追溯: [REQ-006]
- [ADD] FIX-SECURITY-1: 修复后端信任边界
  - 用户原话: "按照标准流程调用change等等吧" (基于架构审查报告 High Issue #2)
  - 修改内容: 新增任务修复 docker-compose.yml 端口暴露与 session 头部信任问题
  - 影响范围: `.anws/v2/05_TASKS.md`, `docker-compose.yml`, `src/agent_backend/api/routes_openai.py`
  - PRD 追溯: [PRD §6.2]
- [ADD] FIX-DOC-2: 统一前端文档与测试契约
  - 修改内容: 新增任务修改根 README.md，与 src/web-ui-shell/README.md 保持一致
  - 影响范围: `.anws/v2/05_TASKS.md`, `README.md`
  - PRD 追溯: N/A
- [ADD] FIX-LOG-1: Session janitor 日志脱敏
  - 修改内容: 新增任务修改 main.py 日志输出，将原始 session_key 替换为哈希或截断形式
  - 影响范围: `.anws/v2/05_TASKS.md`, `src/agent_backend/main.py`
  - PRD 追溯: N/A
- [ADD] FIX-DOC-3: Web UI 壳层装配闭环文档自洽
  - 修改内容: 新增任务统一 README.md、src/web-ui-shell/README.md 与 E2E 测试契约的装配描述
  - 影响范围: `.anws/v2/05_TASKS.md`, `README.md`, `src/web-ui-shell/README.md`
  - PRD 追溯: N/A

## 2026-04-16 - T3.2.4 实现路径调整
- [CHANGE] T3.2.4: 移除 recognize_spirit_list 工具，改为多模态 LLM 直接处理图像
  - 用户原话: "移除工具，多模态模型可以自行处理，可能需要change"
  - 修改内容: 移除 recognition_tool.py 输出依赖，修改验收标准为 Agent 直接接收图片并识别，调整估时从 6h 至 4h
  - 影响范围: `.anws/v2/05_TASKS.md`
  - PRD 追溯: [REQ-002]

## 2026-04-16 - 静态复核补充修复
- [CHANGE] T4.1.2: 强化 BYOK 本地持久化验收标准
  - 用户原话: "我先做一次'回归式静态复核'... BYOK 持久化看起来仍然没修好"
  - 修改内容: 修改验收标准，明确 API Key 保存时代码中不得替换为 ***，确保真实保存到 localStorage
  - 影响范围: `.anws/v2/05_TASKS.md`
  - PRD 追溯: [REQ-006]
- [CHANGE] T3.2.4: 补充截图识别闭环验收标准
  - 用户原话: "我怀疑截图修复只完成了一半"
  - 修改内容: 补充验收标准，明确要求前端确认 UI 和后端 owned_spirits 写回链路
  - 影响范围: `.anws/v2/05_TASKS.md`
  - PRD 追溯: [REQ-002]
- [ADD] FIX-BYOK-PERSISTENCE: 修复 BYOK 本地持久化实现
  - 用户原话: "BYOK 持久化看起来仍然没修好"
  - 修改内容: 新增任务修复 config.ts 中将 api_key 替换为 *** 的逻辑，确保真实保存到 localStorage
  - 影响范围: `.anws/v2/05_TASKS.md`, `src/web-ui-shell/settings/byok/config.ts`, `src/web-ui-shell/settings/byok/config.test.ts`
  - PRD 追溯: [PRD §6.2]
- [ADD] FIX-RECOGNITION-CLOSURE: 补充截图识别闭环实现
  - 用户原话: "我怀疑截图修复只完成了一半"
  - 修改内容: 新增任务实现前端识别结果确认 UI 和后端 owned_spirits 写回链路
  - 影响范围: `.anws/v2/05_TASKS.md`, 前端确认 UI 组件、后端确认信号处理
  - PRD 追溯: [REQ-002]
- [ADD] FIX-SECURITY-NEGATIVE-TEST: 补充安全修复负向测试
  - 用户原话: "安全修复是否有对应测试闭环"
  - 修改内容: 新增任务添加测试验证缺失/错误 secret 必须 403
  - 影响范围: `.anws/v2/05_TASKS.md`, `tests/integration/test_agent_backend_routes.py`
  - PRD 追溯: [PRD §6.2]
- [ADD] FIX-FRONTEND-CLOSURE: 补充前端装配闭环
  - 用户原话: "前端装配闭环与 E2E 契约一致性"
  - 修改内容: 新增任务修复 E2E 测试契约一致性，补充装配证据
  - 影响范围: `.anws/v2/05_TASKS.md`, E2E 测试更新、装配文档补充
  - PRD 追溯: [REQ-006]

## 2026-04-18 - FIX-RECOGNITION-CLOSURE 设计细节补充
- [CHANGE] FIX-RECOGNITION-CLOSURE: 补充前端 UI 组件位置和后端 API 端点
  - 用户原话: 确认变更计划
  - 修改内容: 补充任务描述，明确前端组件位置 `src/web-ui-shell/chat/timeline/recognition-confirm.tsx`，后端端点 POST `/v1/recognition/confirm`，确认信号格式和 data-testid 标识符
  - 影响范围: `.anws/v2/05_TASKS.md`
  - PRD 追溯: [REQ-002]

## 2026-04-18 - 复核反馈补充修复
- [ADD] RESTORE-RECOGNITION-TOOL: 恢复识别工具实现
  - 用户原话: "截图识别仍是骨架实现... recognition_tool.py 源文件已删除，只剩缓存文件"
  - 修改内容: 新增任务恢复或重新实现 recognition_tool.py 及其在 Agent Factory 中的注册
  - 影响范围: `.anws/v2/05_TASKS.md`, `src/agent_backend/runtime/recognition_tool.py`, `src/agent_backend/runtime/agent_factory.py`
  - PRD 追溯: [REQ-002]
- [ADD] IMPLEMENT-FRONTEND-CORE: 实现前端核心组件
  - 用户原话: "Web UI 装配闭环部分解决... 很多主路径组件仍是待实现"
  - 修改内容: 新增任务实现主聊天界面、精灵卡片、工具结果展示等核心组件以满足 E2E 测试契约
  - 影响范围: `.anws/v2/05_TASKS.md`, `src/web-ui-shell/chat/composer/*`, `src/web-ui-shell/chat/timeline/*`
  - PRD 追溯: [REQ-006]
- [ADD] EXPAND-SECURITY-TESTS: 扩展安全负向测试
  - 用户原话: "负向测试只覆盖 /v1/models，未覆盖其他端点"
  - 修改内容: 新增任务扩展负向测试覆盖所有受保护端点（/v1/chat/completions, /v1/recognition/confirm）
  - 影响范围: `.anws/v2/05_TASKS.md`, `tests/integration/test_agent_backend_routes.py`
  - PRD 追溯: [PRD §6.2]
