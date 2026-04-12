/**
 * VisibleFeaturePolicy 单元测试
 * 
 * 验证白名单策略的正确性
 * 
 * 注意：这是一个测试文件，需要配置 vitest 或类似测试框架才能运行。
 * 当前项目尚未配置前端测试环境，此文件作为测试用例参考。
 */

import { VisibleFeaturePolicy, FeatureKey, createRocoDefaultPolicy } from './policy';

// 测试函数（需要配置测试框架后才能运行）
export function runPolicyTests() {
	const policy = createRocoDefaultPolicy();

	// 测试核心功能可见性
	const coreFeatures = [
		FeatureKey.CHAT_INTERFACE,
		FeatureKey.IMAGE_UPLOAD,
		FeatureKey.BUILTIN_ROUTE,
		FeatureKey.BYOK_ROUTE,
		FeatureKey.TOOL_RESULTS,
		FeatureKey.RICH_UI_HOST,
		FeatureKey.SPIRIT_CARDS,
	];

	console.log('Testing core features visibility...');
	coreFeatures.forEach(feature => {
		const result = policy.allows(feature);
		console.log(`${feature}: ${result ? '✓' : '✗'}`);
		if (!result) {
			throw new Error(`Core feature ${feature} should be visible`);
		}
	});

	// 测试禁止功能不可见
	const forbiddenFeatures = [
		FeatureKey.NOTES,
		FeatureKey.CHANNELS,
		FeatureKey.OPEN_TERMINAL,
		FeatureKey.KNOWLEDGE,
		FeatureKey.ADMIN_PANEL,
	];

	console.log('Testing forbidden features visibility...');
	forbiddenFeatures.forEach(feature => {
		const result = policy.allows(feature);
		console.log(`${feature}: ${result ? '✗' : '✓'}`);
		if (result) {
			throw new Error(`Forbidden feature ${feature} should not be visible`);
		}
	});

	// 测试快照导出
	console.log('Testing snapshot export...');
	const snapshot = policy.exportSnapshot();
	console.log(`Snapshot version: ${snapshot.policy_version}`);
	console.log(`Visible entries: ${snapshot.visible_entries.length}`);
	console.log(`Hidden entries: ${snapshot.hidden_entries.length}`);

	// 测试基线验证
	console.log('Testing baseline validation...');
	const validation = policy.validateAgainstBaseline();
	console.log(`Valid: ${validation.valid}`);
	if (!validation.valid) {
		throw new Error('Baseline validation failed');
	}

	console.log('All tests passed!');
}
