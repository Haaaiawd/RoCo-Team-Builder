# Summary Card Host - Manual Verification Guide

## Implementation Status
✅ T4.2.1: 实现 Summary Card Host、AI Action Bar 与 Wiki 深读交互

## Components Implemented
- `types.ts` - Type definitions for SummaryPayload, SummaryCardRenderResult, WikiLinkInfo, AIActionState
- `summaryCardHost.ts` - Summary card rendering with fallback support (render_summary_cards from web-ui-system.detail.md §3.17)
- `aiActionBar.ts` - AI review request handler with draft preservation
- `SummaryCardView.svelte` - Svelte component for displaying summary cards with Wiki links
- `AIActionBar.svelte` - Svelte component for AI review action bar
- `index.ts` - Module exports

## Acceptance Criteria Verification

### AC1: 渲染 summary card 或 fallback 文本
**Given**: 当前精灵存在摘要信息
**When**: 查看摘要区域
**Then**: 渲染 summary card 或 fallback 文本

**Verification Steps**:
1. 在工作台中为某个槽位添加精灵
2. 模拟返回 summary_payload（含 html 或 fallback_text）
3. 验证：
   - 如果 rich_ui_enabled 且 summary_payload.html 存在，渲染 HTML 卡片
   - 如果 rich_ui_enabled 为 false 或 html 缺失，渲染 fallback_text
   - SummaryCardView 正确显示精灵名称和摘要内容
   - Wiki 深读链接正确显示（如果 wiki_slug 存在）

### AC2: AI 分析请求成功或失败时草稿保持不丢失
**Given**: 用户点击 AI 分析评价与建议
**When**: 请求返回成功或失败
**Then**: 草稿保持不丢失并显示清晰状态

**Verification Steps**:
1. 在工作台中配置完整队伍
2. 点击"发起 AI 分析"按钮
3. 验证：
   - 请求成功时：显示 AI 分析结果，草稿状态保持不变
   - 请求失败时：显示错误提示"草稿已保存，您可以稍后重试"，草稿不丢失
   - 草稿为空时：提示"请先完成基础配队后再发起 AI 分析"，不允许发起请求
   - 按钮在请求期间显示"分析中..."并禁用

### AC3: Wiki 链接缺失或失败时保留站内摘要并给出受控提示
**Given**: Wiki 链接缺失或失败
**When**: 用户尝试深读
**Then**: 保留站内摘要并给出受控提示

**Verification Steps**:
1. 为精灵设置 summary_payload（含或不含 wiki_slug）
2. 验证：
   - wiki_slug 存在：显示"Wiki 深读 →"链接，点击在新标签页打开
   - wiki_slug 缺失：显示"Wiki 暂不可用"灰色提示
   - 无论 Wiki 链接是否可用，站内摘要始终显示
   - 不因 Wiki 链接问题影响摘要内容展示

## Integration Notes
- Summary card rendering follows spirit-card-system §6.2 RenderedSpiritCard contract
- renderSummaryCards implements web-ui-system.detail.md §3.17 with fallback support
- AI review requests use MockWorkbenchGateway for testing; replace with actual HTTP client in production
- Draft preservation is guaranteed: errors never clear or modify the current draft
- Wiki links are constructed as `https://wiki.biligame.com/roco/{wiki_slug}`

## Error Handling
- Summary rendering failures fall back to fallback_text
- AI review failures preserve draft state and show retry hint
- Empty draft prevents AI review with clear guidance
- Wiki link failures don't affect summary display

## Next Steps
- Replace MockWorkbenchGateway with actual HTTP client to call `/v1/workbench/ai-review`
- Integrate with actual backend summary_payload from spirit-card-system
- Add unit tests for renderSummaryCards
- Add integration tests for AI review scenarios
- Add Wiki link validation tests
