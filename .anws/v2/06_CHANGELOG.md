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
- [CHANGE] `web-ui-system`: 收敛为“复古冒险者手账风”产品壳层
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

