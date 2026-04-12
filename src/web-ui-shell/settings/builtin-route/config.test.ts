/**
 * 内置轨道配置集成测试
 * 
 * 验证配置创建、验证和默认值
 */

import {
	createBuiltinRouteConfig,
	validateBuiltinRouteConfig,
	DEFAULT_BUILTIN_CONFIG,
} from './config';

// 测试函数（需要配置测试框架后才能运行）
export function runBuiltinConfigTests() {
	console.log('Testing builtin route config...');

	// 测试默认配置
	const defaultConfig = DEFAULT_BUILTIN_CONFIG;
	console.log('Default config:', defaultConfig);

	// 测试创建配置
	const customConfig = createBuiltinRouteConfig({
		connection_name: 'Custom Backend',
		base_url: 'https://custom-backend.com',
	});
	console.log('Custom config:', customConfig);

	// 测试验证
	const validation = validateBuiltinRouteConfig(customConfig);
	console.log('Validation:', validation);
	if (!validation.valid) {
		throw new Error(`Validation failed: ${validation.errors.join(', ')}`);
	}

	// 测试无效配置
	const invalidConfig = createBuiltinRouteConfig({
		connection_name: '', // 无效
		base_url: 'not-a-url', // 无效
	});
	const invalidValidation = validateBuiltinRouteConfig(invalidConfig);
	console.log('Invalid validation:', invalidValidation);
	if (invalidValidation.valid) {
		throw new Error('Invalid config should fail validation');
	}

	console.log('All builtin config tests passed!');
}
