/**
 * NavigationFilter 集成测试
 * 
 * 验证导航裁剪和白名单过滤逻辑
 */

import {
	NavigationFilter,
	createNavigationFilter,
	FORBIDDEN_ENTRIES,
	ALLOWED_ENTRIES,
	NavigationTree,
	NavigationNode,
} from './filter';
import { createRocoDefaultPolicy } from '../guards/feature-whitelist/policy';

// 测试函数（需要配置测试框架后才能运行）
export function runNavigationFilterTests() {
	console.log('Testing navigation filter...');

	// 测试禁止入口列表
	console.log('Forbidden entries:', FORBIDDEN_ENTRIES);
	if (!FORBIDDEN_ENTRIES.includes('notes')) {
		throw new Error('Forbidden entries should include notes');
	}
	if (!FORBIDDEN_ENTRIES.includes('admin')) {
		throw new Error('Forbidden entries should include admin');
	}

	// 测试允许入口列表
	console.log('Allowed entries:', ALLOWED_ENTRIES);
	if (!ALLOWED_ENTRIES.includes('chat')) {
		throw new Error('Allowed entries should include chat');
	}
	if (!ALLOWED_ENTRIES.includes('settings')) {
		throw new Error('Allowed entries should include settings');
	}

	// 创建过滤器
	const policy = createRocoDefaultPolicy();
	const filter = createNavigationFilter(policy);

	// 测试导航树过滤
	const testTree: NavigationTree = {
		nodes: [
			{
				id: 'chat',
				label: 'Chat',
				visible: true,
				children: [],
			},
			{
				id: 'notes',
				label: 'Notes',
				visible: true,
				children: [],
			},
			{
				id: 'admin',
				label: 'Admin',
				visible: true,
				role_required: 'admin',
				children: [],
			},
			{
				id: 'settings',
				label: 'Settings',
				visible: true,
				children: [],
			},
		],
	};

	// 测试终端用户过滤
	const filteredForUser = filter.filterNavigation(testTree, 'user');
	console.log('Filtered for user:', filteredForUser);
	
	const userNodeIds = filteredForUser.nodes.map(n => n.id);
	if (userNodeIds.includes('notes')) {
		throw new Error('Notes should be filtered for user');
	}
	if (userNodeIds.includes('admin')) {
		throw new Error('Admin should be filtered for user');
	}
	if (!userNodeIds.includes('chat')) {
		throw new Error('Chat should be visible for user');
	}
	if (!userNodeIds.includes('settings')) {
		throw new Error('Settings should be visible for user');
	}

	// 测试管理员过滤
	const filteredForAdmin = filter.filterNavigation(testTree, 'admin');
	console.log('Filtered for admin:', filteredForAdmin);
	
	const adminNodeIds = filteredForAdmin.nodes.map(n => n.id);
	if (adminNodeIds.includes('notes')) {
		throw new Error('Notes should be filtered even for admin');
	}
	if (!adminNodeIds.includes('admin')) {
		throw new Error('Admin should be visible for admin');
	}

	// 测试导航验证
	const validation = filter.validateNavigation(filteredForUser);
	console.log('Validation result:', validation);
	if (!validation.valid) {
		throw new Error(`Navigation validation failed: ${validation.violations.join(', ')}`);
	}

	// 测试禁止入口可见时的验证失败
	const invalidTree: NavigationTree = {
		nodes: [
			{
				id: 'notes',
				label: 'Notes',
				visible: true,
				children: [],
			},
		],
	};
	const invalidValidation = filter.validateNavigation(invalidTree);
	console.log('Invalid validation:', invalidValidation);
	if (invalidValidation.valid) {
		throw new Error('Validation should fail when forbidden entry is visible');
	}

	console.log('All navigation filter tests passed!');
}
