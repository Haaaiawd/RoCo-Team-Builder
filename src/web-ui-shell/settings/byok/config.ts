/**
 * DirectConnectionEntry - BYOK 直连配置
 * 
 * 定义用户自带 Key 的直连配置，仅保存在浏览器本地。
 * BYOK 轨道是受限直连模式，不具备 Agent 增强能力。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §6.1 DirectConnectionEntry
 */

/**
 * 直连配置条目
 */
export interface DirectConnectionEntry {
	/** Provider 基础 URL */
	base_url: string;
	/** API Key（仅保存在 localStorage） */
	api_key: string;
	/** 额外配置 */
	config: Record<string, any>;
	/** 选中的模型 */
	selected_model: string | null;
	/** 存储范围（固定为 localStorage） */
	storage_scope: 'localStorage';
	/** 连接名称（用户自定义） */
	name?: string;
	/** 能力标签（用于与内置轨道对比） */
	capabilities: string[];
}

/**
 * 默认 BYOK 能力标签
 */
export const DEFAULT_BYOK_CAPABILITIES: string[] = [
	'基础对话',
	'多模型直连',
];

/**
 * BYOK 配置的 localStorage 键
 */
export const BYOK_STORAGE_KEY = 'roco_byok_connections';

/**
 * 创建 BYOK 配置
 */
export function createDirectConnectionEntry(
	base_url: string,
	api_key: string,
	name?: string
): DirectConnectionEntry {
	return {
		base_url,
		api_key,
		config: {},
		selected_model: null,
		storage_scope: 'localStorage',
		name: name || 'Custom Connection',
		capabilities: [...DEFAULT_BYOK_CAPABILITIES],
	};
}

/**
 * 验证 BYOK 配置
 */
export function validateDirectConnectionEntry(entry: DirectConnectionEntry): { valid: boolean; errors: string[] } {
	const errors: string[] = [];

	if (!entry.base_url || entry.base_url.trim() === '') {
		errors.push('base_url 不能为空');
	} else {
		try {
			new URL(entry.base_url);
		} catch {
			errors.push('base_url 必须是有效的 URL');
		}
	}

	if (!entry.api_key || entry.api_key.trim() === '') {
		errors.push('api_key 不能为空');
	}

	if (entry.storage_scope !== 'localStorage') {
		errors.push('storage_scope 必须是 localStorage');
	}

	return {
		valid: errors.length === 0,
		errors,
	};
}

/**
 * BYOK 配置管理器
 */
export class ByokConnectionManager {
	private storageKey: string;

	constructor(storageKey: string = BYOK_STORAGE_KEY) {
		this.storageKey = storageKey;
	}

	/**
	 * 保存 BYOK 配置到 localStorage
	 * 验收标准：API Key 真实保存在 localStorage，不替换为 ***
	 */
	save(entry: DirectConnectionEntry): void {
		const validation = validateDirectConnectionEntry(entry);
		if (!validation.valid) {
			throw new Error(`Invalid BYOK config: ${validation.errors.join(', ')}`);
		}

		// 真实保存 api_key 到 localStorage（不替换为 ***）
		localStorage.setItem(this.storageKey, JSON.stringify(entry));
	}

	/**
	 * 从 localStorage 加载 BYOK 配置
	 * 验收标准：API Key 可正常读取使用，不为空字符串
	 */
	load(): DirectConnectionEntry | null {
		const data = localStorage.getItem(this.storageKey);
		if (!data) return null;

		try {
			const entry = JSON.parse(data) as DirectConnectionEntry;
			return entry;
		} catch {
			return null;
		}
	}

	/**
	 * 删除 BYOK 配置
	 */
	remove(): void {
		localStorage.removeItem(this.storageKey);
	}

	/**
	 * 检查是否存在 BYOK 配置
	 */
	hasConfig(): boolean {
		return localStorage.getItem(this.storageKey) !== null;
	}
}

/**
 * 创建 BYOK 配置管理器
 */
export function createByokConnectionManager(): ByokConnectionManager {
	return new ByokConnectionManager();
}
