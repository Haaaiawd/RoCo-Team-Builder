# Workbench Host - Manual Verification Guide

## Implementation Status
✅ T4.1.1: 实现双入口 Team Workbench Host 与 handoff fallback 进入路径

## Components Implemented
- `types.ts` - Type definitions for TeamDraft, WorkbenchHandOffPayload, etc.
- `hydration.ts` - Core hydration logic with dual entry points
- `WorkbenchHost.svelte` - Svelte component for workbench UI
- `index.ts` - Module exports

## Acceptance Criteria Verification

### AC1: 侧边栏入口创建或加载当前单草稿
**Given**: 用户点击侧边栏工作台入口
**When**: 页面进入工作台
**Then**: 创建或加载当前单草稿

**Verification Steps**:
1. 在 Open WebUI 中导航到侧边栏
2. 点击"配队工作台"入口
3. 验证：
   - 如果本地有缓存草稿，应加载该草稿
   - 如果无缓存草稿，应创建空白草稿
   - `entry_point` 应为 "sidebar"
   - `source` 应为 "empty" 或 "agent_handoff"（如果有缓存）

### AC2: 聊天结果承接入口加载草稿
**Given**: 聊天结果包含合法 handoff payload
**When**: 用户点击承接入口
**Then**: 工作台加载该草稿

**Verification Steps**:
1. 在聊天中让 Agent 生成一支完整队伍
2. Agent 响应应包含 `WorkbenchHandOffPayload` artifact
3. 点击"在配队工作台中查看"按钮
4. 验证：
   - 工作台应加载 Agent 生成的队伍草稿
   - `entry_point` 应为 "agent_handoff"
   - `source` 应为 "agent_handoff"
   - 所有槽位应正确填充

### AC3: Handoff 失败时空白草稿兜底
**Given**: payload 缺失或损坏
**When**: 承接失败
**Then**: 提示错误并允许以空白草稿进入

**Verification Steps**:
1. 模拟损坏的 handoff payload（缺失 team_draft 或 schema_version 不匹配）
2. 尝试从聊天结果进入工作台
3. 验证：
   - 应显示错误横幅："无法加载队伍草稿：承接载荷缺失或损坏" 或 "数据版本不匹配"
   - 应允许用户继续编辑空白草稿
   - `entry_point` 应为 "agent_handoff"
   - `source` 应为 "empty"
   - `last_error_code` 应设置相应错误码

## Error Codes
- `HANDOFF_PAYLOAD_INVALID` - 承接载荷缺失或损坏
- `HANDOFF_SCHEMA_VERSION_MISMATCH` - 数据版本不匹配
- `UNKNOWN_ENTRY_POINT` - 未知的入口类型
- `HANDOFF_HYDRATION_ERROR` - Hydration 过程中的其他错误

## Integration Notes
- This module is designed to integrate with Open WebUI's route system
- The hydration logic uses localStorage with key `team_draft:v1`
- Schema version is currently "v1"
- The component follows the "复古冒险者手账风" visual language (to be applied via theme overrides)

## Next Steps
- Integrate WorkbenchHost.svelte into Open WebUI's routing system
- Add sidebar navigation entry for workbench
- Add handoff button in chat timeline for agent results
- Apply theme overrides for visual consistency
