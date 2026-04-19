/**
 * NavigationFilter - 导航裁剪过滤器
 * 
 * 根据白名单策略过滤导航树，隐藏终端用户无关入口。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §5.1 filter_navigation
 * 参考：ADR-004 Web UI 裁剪与收敛策略
 */

import { VisibleFeaturePolicy, FeatureKey } from '../guards/feature-whitelist/policy';

/**
 * 导航节点
 */
export interface NavigationNode {
	id: string;
	label: string;
	path?: string;
	children?: NavigationNode[];
	visible: boolean;
	role_required?: 'user' | 'admin';
}

/**
 * 导航树
 */
export interface NavigationTree {
	nodes: NavigationNode[];
}

/**
 * 禁止的入口（终端用户不可见）
 */
export const FORBIDDEN_ENTRIES: string[] = [
	'notes',
	'channels',
	'knowledge',
	'admin',
	'open-terminal',
	'workspaces',
	'prompts',
	'documents',
];

/**
 * 允许的入口（终端用户可见）
 */
export const ALLOWED_ENTRIES: string[] = [
	'chat',
	'settings',
	'models',
	'connections',
];

/**
 * 导航过滤器
 */
export class NavigationFilter {
	private policy: VisibleFeaturePolicy;

	constructor(policy: VisibleFeaturePolicy) {
		this.policy = policy;
	}

	/**
	 * 过滤导航树
	 * 验收标准：Notes、Channels、Knowledge、Admin、Open Terminal 等无关入口不可见且不可达
	 */
	filterNavigation(tree: NavigationTree, userRole: 'user' | 'admin'): NavigationTree {
		const filteredNodes = tree.nodes
			.map(node => this.filterNode(node, userRole))
			.filter(node => node.visible);

		return {
			nodes: filteredNodes,
		};
	}

	/**
	 * 过滤单个节点
	 */
	private filterNode(node: NavigationNode, userRole: 'user' | 'admin'): NavigationNode {
		const filteredNode: NavigationNode = { ...node };

		// 检查是否是禁止入口
		if (this.isForbiddenEntry(node.id)) {
			filteredNode.visible = false;
			return filteredNode;
		}

		// 检查是否需要管理员权限
		if (node.role_required === 'admin' && userRole !== 'admin') {
			filteredNode.visible = false;
			return filteredNode;
		}

		// 检查是否在白名单中
		if (!this.isAllowedEntry(node.id)) {
			filteredNode.visible = false;
			return filteredNode;
		}

		// 递归过滤子节点
		if (node.children && node.children.length > 0) {
			filteredNode.children = node.children
				.map(child => this.filterNode(child, userRole))
				.filter(child => child.visible);
		}

		return filteredNode;
	}

	/**
	 * 检查是否是禁止入口
	 */
	private isForbiddenEntry(entryId: string): boolean {
		return FORBIDDEN_ENTRIES.some(forbidden => entryId.toLowerCase().includes(forbidden));
	}

	/**
	 * 检查是否是允许入口
	 */
	private isAllowedEntry(entryId: string): boolean {
		return ALLOWED_ENTRIES.some(allowed => entryId.toLowerCase().includes(allowed));
	}

	/**
	 * 验证导航树是否符合白名单
	 * 用于回归测试
	 */
	validateNavigation(tree: NavigationTree): { valid: boolean; violations: string[] } {
		const violations: string[] = [];

		const checkNode = (node: NavigationNode) => {
			if (node.visible && this.isForbiddenEntry(node.id)) {
				violations.push(`Forbidden entry is visible: ${node.id}`);
			}
			if (node.children) {
				node.children.forEach(checkNode);
			}
		};

		tree.nodes.forEach(checkNode);

		return {
			valid: violations.length === 0,
			violations,
		};
	}
}

/**
 * 创建导航过滤器
 */
export function createNavigationFilter(policy: VisibleFeaturePolicy): NavigationFilter {
	return new NavigationFilter(policy);
}
