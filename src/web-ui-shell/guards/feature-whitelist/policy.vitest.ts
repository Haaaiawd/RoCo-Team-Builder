/**
 * VisibleFeaturePolicy vitest 冒烟用例
 *
 * 目的：证明 web-ui-shell 的 TypeScript + vitest 脚手架确实能跑。
 * 这里仅做最低限度的白名单/黑名单验证，完整用例覆盖仍在 `policy.test.ts`
 * 的 `runPolicyTests()` 里，后续迁移工作由独立 PR 承接。
 */

import { describe, expect, it } from 'vitest';

import { FeatureKey, createRocoDefaultPolicy } from './policy';

describe('VisibleFeaturePolicy', () => {
	it('默认策略放行核心功能并拦截禁止功能', () => {
		const policy = createRocoDefaultPolicy();

		expect(policy.allows(FeatureKey.CHAT_INTERFACE)).toBe(true);
		expect(policy.allows(FeatureKey.BUILTIN_ROUTE)).toBe(true);
		expect(policy.allows(FeatureKey.BYOK_ROUTE)).toBe(true);
		expect(policy.allows(FeatureKey.TOOL_RESULTS)).toBe(true);
		expect(policy.allows(FeatureKey.RICH_UI_HOST)).toBe(true);

		expect(policy.allows(FeatureKey.NOTES)).toBe(false);
		expect(policy.allows(FeatureKey.CHANNELS)).toBe(false);
		expect(policy.allows(FeatureKey.OPEN_TERMINAL)).toBe(false);
		expect(policy.allows(FeatureKey.KNOWLEDGE)).toBe(false);
		expect(policy.allows(FeatureKey.ADMIN_PANEL)).toBe(false);
	});

	it('快照导出 / baseline 校验可用', () => {
		const policy = createRocoDefaultPolicy();

		const snapshot = policy.exportSnapshot();
		expect(snapshot.policy_version).toBeTruthy();
		expect(snapshot.visible_entries.length).toBeGreaterThan(0);
		expect(snapshot.hidden_entries.length).toBeGreaterThan(0);

		const validation = policy.validateAgainstBaseline();
		expect(validation.valid).toBe(true);
	});
});
