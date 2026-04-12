/**
 * BuiltinRouteConfig - 内置轨道配置
 * 
 * 定义系统级内置连接的配置，由管理员注册。
 * 内置轨道提供完整的 Agent 增强能力（工具调用、BWIKI 数据、精灵卡片、会话隔离）。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §6.1 BuiltinRouteConfig
 */

/**
 * 内置轨道配置
 */
export interface BuiltinRouteConfig {
	/** 连接名称 */
	connection_name: string;
	/** 后端服务地址 */
	base_url: string;
	/** 默认模型 ID */
	default_model_id: string;
	/** 是否启用 */
	enabled: boolean;
	/** 连接描述（用于用户提示） */
	description?: string;
	/** 能力标签（用于与 BYOK 对比） */
	capabilities: string[];
}

/**
 * 默认内置轨道配置
 */
export const DEFAULT_BUILTIN_CONFIG: BuiltinRouteConfig = {
	connection_name: 'RoCo Agent Backend',
	base_url: 'http://localhost:8000', // 默认本地地址
	default_model_id: 'roco-agent',
	enabled: true,
	description: '内置轨道：完整的配队推理、资料查询、精灵卡片与工具调用能力',
	capabilities: [
		'配队推理',
		'资料查询',
		'精灵卡片',
		'工具调用',
		'会话隔离',
		'截图识别',
	],
};

/**
 * 创建内置轨道配置
 */
export function createBuiltinRouteConfig(config: Partial<BuiltinRouteConfig> = {}): BuiltinRouteConfig {
	return {
		...DEFAULT_BUILTIN_CONFIG,
		...config,
	};
}

/**
 * 验证内置轨道配置
 */
export function validateBuiltinRouteConfig(config: BuiltinRouteConfig): { valid: boolean; errors: string[] } {
	const errors: string[] = [];

	if (!config.connection_name || config.connection_name.trim() === '') {
		errors.push('connection_name 不能为空');
	}

	if (!config.base_url || config.base_url.trim() === '') {
		errors.push('base_url 不能为空');
	} else {
		try {
			new URL(config.base_url);
		} catch {
			errors.push('base_url 必须是有效的 URL');
		}
	}

	if (!config.default_model_id || config.default_model_id.trim() === '') {
		errors.push('default_model_id 不能为空');
	}

	if (!Array.isArray(config.capabilities)) {
		errors.push('capabilities 必须是数组');
	}

	return {
		valid: errors.length === 0,
		errors,
	};
}
