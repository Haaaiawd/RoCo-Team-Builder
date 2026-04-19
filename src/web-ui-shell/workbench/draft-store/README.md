# Draft Store - Manual Verification Guide

## Implementation Status
✅ T4.1.2: 实现 TeamDraft Store、分析刷新编排与旧结果保护

## Components Implemented
- `types.ts` - Type definitions for DraftMutation, AnalysisRefreshRequest, TeamAnalysisSnapshot, etc.
- `draftStore.ts` - Draft store with mutateTeamDraft, local state guards, and localStorage persistence
- `analysisRefresh.ts` - Analysis refresh with stale protection using request IDs
- `AnalysisView.svelte` - Svelte component for displaying TeamAnalysisSnapshot with controlled empty states
- `index.ts` - Module exports

## Acceptance Criteria Verification

### AC1: 编辑精灵或技能时 UI 与草稿状态同步更新
**Given**: 用户已进入工作台
**When**: 用户替换任一槽位中的精灵
**Then**: 工作台必须更新该槽位展示并触发对应的结构化分析刷新

**Verification Steps**:
1. 在工作台中编辑某个槽位的精灵
2. 调用 `mutateTeamDraft(draft, mutation)` 更新草稿
3. 验证：
   - UI 立即反映新的精灵名称
   - 草稿状态保存到 localStorage (key: "team_draft:v1")
   - Local state guard 的 `is_mutating` 标志正确管理
   - `last_mutation_timestamp` 更新

### AC2: 频繁编辑时旧结果不覆盖新草稿状态
**Given**: 用户频繁连续编辑
**When**: 多次刷新分析返回
**Then**: 旧结果不会覆盖新草稿状态

**Verification Steps**:
1. 快速连续编辑多个槽位
2. 在编辑过程中触发多次分析刷新
3. 验证：
   - 每次刷新生成新的 `request_id`
   - 草稿的 `last_analysis_request_id` 始终为最新
   - 旧响应的 `request_id` 不匹配时被忽略（status: "stale_ignored"）
   - UI 显示的草稿状态始终为最后一次有效编辑结果

### AC3: 空草稿或数据不足时返回受控空状态
**Given**: 空草稿或数据不足
**When**: 展示分析面板
**Then**: 返回受控空状态而非误导性结论

**Verification Steps**:
1. 创建空白草稿（无精灵）
2. 点击"刷新分析"按钮
3. 验证：
   - AnalysisView 显示"数据不足"空状态
   - 不显示误导性的分析结果
   - 空状态文案明确："请添加精灵到队伍后查看分析结果"
4. 添加少量精灵后再次分析
5. 验证：
   - 显示可计算部分的分析结果
   - 缺失的数据项显示"暂无数据"
   - 不输出误导性结论

## Integration Notes
- Draft store uses localStorage with keys:
  - `team_draft:v1` - draft data
  - `team_draft_guard:v1` - local state guard
- Analysis refresh uses request ID tracking for stale protection
- Local state guard prevents concurrent mutations and analysis requests
- MockWorkbenchGateway is provided for testing; replace with actual HTTP client in production

## Stale Protection Mechanism
1. Each analysis refresh generates a unique `request_id`
2. Draft stores `last_analysis_request_id` before sending request
3. Response is accepted only if `response.request_id === draft.last_analysis_request_id`
4. Old responses are ignored with status "stale_ignored"

## Error Handling
- Analysis failures preserve current draft state
- Guard is released even on error
- Error messages displayed in AnalysisView component
- Empty states are explicitly controlled, not accidental

## Next Steps
- Replace MockWorkbenchGateway with actual HTTP client to call `/v1/workbench/team-analysis`
- Integrate with actual backend TeamAnalysisSnapshot schema
- Add unit tests for draft store mutations
- Add integration tests for stale protection scenarios
