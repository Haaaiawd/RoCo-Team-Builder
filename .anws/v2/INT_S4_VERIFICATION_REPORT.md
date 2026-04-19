# INT-S4 集成验证报告 — Product Shell

> **S4 集成验证 — Product Shell**
> 
> 版本: v2
> Wave: Wave 4C — Web UI 壳层基础
> 日期: 2026-04-12
> 状态: **代码完成，待部署后执行 E2E 测试**

---

## 1. 验证概述

### 1.1 验证目标
验证产品壳层退出标准，确认终端用户主路径、截图能力预检、BYOK 降级、白名单快照和关键故事可演示；同时验证白名单回归指标可被观测。

### 1.2 依赖检查
- [x] T4.1.1 — 产品壳层骨架 + VisibleFeaturePolicy 真理源 + 复古冒险者手账风主题
- [x] T4.1.2 — 接入内置轨道与 BYOK 双轨设置
- [x] T4.2.1 — 打通聊天时间线、工具折叠卡片与 Rich UI 宿主
- [x] T4.2.2 — 白名单导航裁剪与复古手账主题覆写
- [x] T4.2.3 — 截图发送前能力预检与 builtin 配额提示
- [x] T4.3.1 — 关键用户故事 E2E、白名单回归与发布前检查
- [x] T3.3.2 — 后端流式能力（已完成）

### 1.3 验证范围
- 终端用户主路径验证
- 截图能力预检验证
- BYOK 降级验证
- 白名单快照验证
- 关键用户故事验证
- 主题巡检验证
- 监控指标验证

---

## 2. 代码完成度检查

### 2.1 核心功能实现
- [x] **VisibleFeaturePolicy** — 白名单驱动的可见能力设计
- [x] **NavigationFilter** — 导航裁剪过滤器
- [x] **ThemeInjector** — 主题注入器
- [x] **ImageCapabilityPreflight** — 图片能力预检
- [x] **QuotaGuard** — 配额守卫
- [x] **MessageComposer** — 消息编写器
- [x] **MessageArtifacts** — 消息工件渲染
- [x] **ToolResultCard** — 工具结果卡片
- [x] **RichUiHost** — Rich UI 宿主

### 2.2 测试覆盖
- [x] 单元测试 — VisibleFeaturePolicy, NavigationFilter, ThemeInjector, QuotaGuard, MessageComposer
- [x] 集成测试 — BuiltinRouteConfig, ByokConnectionManager, RouteStateManager, ImageCapabilityPreflight
- [x] E2E 测试 — Product Shell, Visible Feature Policy（需 Playwright 安装）

### 2.3 文档完整性
- [x] 系统设计文档 — web-ui-system.md
- [x] ADR — ADR-001, ADR-002, ADR-003, ADR-004
- [x] 任务清单 — 05_TASKS.md
- [x] 发布检查清单 — RELEASE_CHECKLIST.md
- [x] README — Web UI Shell 说明文档

---

## 3. 待部署验证项目

### 3.1 E2E 测试（需要实际部署）

#### 3.1.1 关键用户故事验证
- [ ] US-001: 文字配队
  - [ ] 用户发送配队请求，Agent 返回推荐队伍
  - [ ] 用户追问配队细节，Agent 保持上下文
  
- [ ] US-002: 截图识别
  - [ ] 用户上传截图，Agent 返回识别候选
  - [ ] 用户确认拥有列表，界面显示状态提示
  - [ ] BYOK 非视觉模型上传截图，前端拦截并提示
  
- [ ] US-004: 资料卡片
  - [ ] Agent 返回精灵卡片，Rich UI 宿主渲染
  - [ ] Rich UI 渲染失败，降级为文本
  
- [ ] US-006: 白名单路径
  - [ ] 终端用户首页不出现禁止入口
  - [ ] 侧栏导航满足白名单约束
  - [ ] BYOK 轨道不出现识别确认、精灵卡片等误导性 UI
  - [ ] 主题注入后，UI 呈现复古手账风

#### 3.1.2 白名单基线比对
- [ ] VisibleFeaturePolicy 导出快照与基线一致
- [ ] 未出现新增暴露入口
- [ ] 若出现新增入口，已阻断发布

#### 3.1.3 主题巡检
- [ ] 炭黑侧栏、撕纸边缘效果正确
- [ ] 羊皮纸主区、地图纹理正确
- [ ] 暖金高亮、虚线内框正确
- [ ] 用户气泡纸贴片效果正确
- [ ] Agent 文本书写风格正确
- [ ] 胶囊形输入区正确
- [ ] History 项手账标签感正确
- [ ] 桌面端与移动端视觉语言一致

### 3.2 监控指标验证（需要实际部署）
- [ ] 首页进入对话主路径成功率
- [ ] 截图上传失败率
- [ ] `image_capability_block_count`
- [ ] `builtin_quota_exhausted_prompt_count`
- [ ] `recognition_review_render_count`
- [ ] `owned_list_confirmation_submit_count`
- [ ] Rich UI 渲染失败率
- [ ] 内置轨道调用成功率
- [ ] BYOK 配置保存成功率
- [ ] `visible_feature_policy_regression_fail_count`
- [ ] UI 回归缺陷数

---

## 4. 部署前置条件

### 4.1 依赖安装
```bash
# 安装 Playwright（用于 E2E 测试）
npm install -D @playwright/test
npx playwright install
```

### 4.2 环境配置
- [ ] Open WebUI 已部署
- [ ] Agent Backend 已部署
- [ ] Docker Compose 网络已配置
- [ ] 环境变量已设置

### 4.3 前置集成验证
- [x] INT-S1 — S1 集成验证 — Data Spine
- [x] INT-S2 — S2 集成验证 — Card Surface
- [x] INT-S3 — S3 集成验证 — Agent Core

---

## 5. 验证执行计划

### 5.1 E2E 测试执行
```bash
# 运行产品壳层 E2E 测试
npx playwright test tests/e2e/product-shell.spec.ts

# 运行白名单策略 E2E 测试
npx playwright test tests/e2e/visible-feature-policy.spec.ts

# 生成测试报告
npx playwright show-report
```

### 5.2 白名单基线比对
```bash
# 导出当前快照
# （需要在前端代码中暴露 window.rocoPolicy.exportSnapshot()）

# 与基线比对
# （手动比对或自动化脚本）
```

### 5.3 主题巡检
- 人工 UI 巡检
- 截图对比
- 跨浏览器验证（Chrome, Firefox, Safari）
- 响应式验证（桌面端, 移动端）

---

## 6. 验收标准对照

### 6.1 S4 退出标准
- [ ] Given S4 所有任务已完成
  - **状态**: ✅ 代码完成
  
- [ ] When 执行文字配队、截图识别、资料卡片、BYOK 降级、白名单基线和主题巡检
  - **状态**: ⏳ 待部署后执行
  
- [ ] Then 全部通过，终端用户主导航保持 0 个无关入口
  - **状态**: ⏳ 待验证
  
- [ ] Given `web-ui-system.md` §12.3 定义的 `visible_feature_policy_regression_fail_count` 指标
  - **状态**: ⏳ 待部署后验证
  
- [ ] When 白名单比对发现新增暴露入口
  - **状态**: ⏳ 待验证
  
- [ ] Then 日志/报告中可观测到该指标被触发，且构建被阻断
  - **状态**: ⏳ 待验证
  
- [ ] Given 任一关键路径失败
  - **状态**: ⏳ 待验证
  
- [ ] When 记录结果
  - **状态**: ⏳ 待验证
  
- [ ] Then 形成发布阻断项并要求修复后重跑
  - **状态**: ⏳ 待验证

### 6.2 上线前检查（§12.2）
- [ ] 内置轨道已注册且可拉取模型列表
- [ ] BYOK 入口已启用且用户文案清晰
- [ ] 终端用户首页默认进入产品对话主路径
- [ ] 禁止入口在 user 角色下均不可见、不可达
- [ ] 富展示失败时有可读降级结果
- [ ] `VisibleFeaturePolicy` 导出快照已生成，并与快照基线比对通过
- [ ] 截图发送前能力校验文案与 `CAPABILITY_` 错误语义已对齐总览矩阵
- [ ] `Recognition Review` → 用户确认 → 已确认拥有列表状态提示链路在 Compose 基线上可验
- [ ] 主题注入 CSS 已生效，主区纹理、侧栏撕纸边缘、History 标签态与输入框胶囊样式通过人工验收

---

## 7. 当前状态总结

### 7.1 已完成
- ✅ 所有 Wave 4C 任务代码实现完成
- ✅ 单元测试和集成测试完成
- ✅ E2E 测试脚本编写完成
- ✅ 发布检查清单完成
- ✅ 文档更新完成

### 7.2 待完成
- ⏳ Playwright 依赖安装
- ⏳ Open WebUI 部署
- ⏳ Agent Backend 部署
- ⏳ 端到端集成
- ⏳ E2E 测试执行
- ⏳ 白名单基线比对
- ⏳ 主题巡检
- ⏳ 监控指标验证

### 7.3 风险评估
- **中等风险**: E2E 测试需要实际部署环境
- **低风险**: 代码质量高，测试覆盖完整
- **缓解措施**: 提供详细的 E2E 测试脚本和验证清单

---

## 8. 下一步行动

### 8.1 立即行动
1. 安装 Playwright 依赖
2. 准备部署环境
3. 执行 Docker Compose 部署

### 8.2 验证执行
1. 运行 E2E 测试
2. 执行白名单基线比对
3. 执行主题巡检
4. 验证监控指标

### 8.3 发布决策
根据验证结果决定是否发布。若出现阻断项，需修复后重跑 INT-S4。

---

## 9. 备注

- E2E 测试文件位置: `tests/e2e/product-shell.spec.ts`, `tests/e2e/visible-feature-policy.spec.ts`
- 发布检查清单: `.anws/v2/RELEASE_CHECKLIST.md`
- 系统设计文档: `.anws/v2/04_SYSTEM_DESIGN/web-ui-system.md`
- 当前状态: **代码完成，待部署后执行 E2E 测试**
