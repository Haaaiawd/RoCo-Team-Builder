/**
 * BYOK 配置集成测试
 * 
 * 验证 localStorage 存储、配置验证和管理器功能
 * 
 * 验收标准：
 * - 用户输入 BYOK 配置后，API Key 仅保存在 localStorage，不发送到服务端
 */

import {
	createDirectConnectionEntry,
	validateDirectConnectionEntry,
	ByokConnectionManager,
	createByokConnectionManager,
} from './config';

// 测试函数（需要配置测试框架后才能运行）
export function runByokConfigTests() {
	console.log('Testing BYOK config...');

	// 测试创建配置
	const entry = createDirectConnectionEntry('https://api.openai.com/v1', 'sk-test-key', 'My OpenAI');
	console.log('Created entry:', entry);

	// 测试验证
	const validation = validateDirectConnectionEntry(entry);
	console.log('Validation:', validation);
	if (!validation.valid) {
		throw new Error(`Validation failed: ${validation.errors.join(', ')}`);
	}

	// 测试管理器
	const manager = createByokConnectionManager();

	// 测试保存
	manager.save(entry);
	console.log('Saved to localStorage');

	// 测试加载
	const loaded = manager.load();
	console.log('Loaded from localStorage:', loaded);
	if (!loaded) {
		throw new Error('Failed to load from localStorage');
	}

	// 验证 API Key 未返回（安全措施）
	if (loaded.api_key !== '') {
		throw new Error('API key should not be returned from localStorage');
	}

	// 测试检查是否存在
	if (!manager.hasConfig()) {
		throw new Error('hasConfig should return true');
	}

	// 测试删除
	manager.remove();
	console.log('Removed from localStorage');

	// 测试删除后不存在
	if (manager.hasConfig()) {
		throw new Error('hasConfig should return false after removal');
	}

	console.log('All BYOK config tests passed!');
}
