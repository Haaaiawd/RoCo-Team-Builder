/**
 * VisibleFeaturePolicy - 产品能力白名单策略
 * 
 * 这是 web-ui-system 的真理源，定义终端用户可见的能力范围。
 * 任何不在白名单中的功能都必须对终端用户不可见、不可达。
 * 
 * 参考：ADR-004 Web UI 裁剪与收敛策略
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §6.1 VisibleFeaturePolicy
 */

/**
 * 功能键枚举
 * 定义所有可能的功能入口键
 */
export enum FeatureKey {
	// 核心对话功能
	CHAT_INTERFACE = 'chat_interface',
	IMAGE_UPLOAD = 'image_upload',
	
	// 模型配置
	MODEL_SELECTION = 'model_selection',
	BUILTIN_ROUTE = 'builtin_route',
	BYOK_ROUTE = 'byok_route',
	
	// 工具与富展示
	TOOL_RESULTS = 'tool_results',
	RICH_UI_HOST = 'rich_ui_host',
	SPIRIT_CARDS = 'spirit_cards',
	
	// 禁止的 Open WebUI 原生功能（必须隐藏）
	NOTES = 'notes',
	CHANNELS = 'channels',
	OPEN_TERMINAL = 'open_terminal',
	KNOWLEDGE = 'knowledge',
	ADMIN_PANEL = 'admin_panel',
	DOCUMENTS = 'documents',
	GALLERY = 'gallery',
	WORKSPACE = 'workspace',
	PROMPTS = 'prompts',
	SETTINGS_ADVANCED = 'settings_advanced',
}

/**
 * 可见功能策略配置
 */
export interface VisibleFeaturePolicyConfig {
	// 核心能力开关
	chat_enabled: boolean;
	image_upload_enabled: boolean;
	builtin_route_enabled: boolean;
	byok_enabled: boolean;
	tool_result_enabled: boolean;
	rich_ui_enabled: boolean;
	
	// 禁止入口列表
	forbidden_entries: string[];
	
	// 元数据
	policy_version: string;
	
	// 快照导出配置
	snapshot_scope: string[];
	expected_visible_entries: string[];
	expected_hidden_entries: string[];
	validation_baseline_id: string | null;
}

/**
 * 可见功能策略
 * 
 * 这是白名单的唯一真理源，所有前端组件必须通过此策略判断功能可见性。
 */
export class VisibleFeaturePolicy {
	private config: VisibleFeaturePolicyConfig;

	constructor(config: VisibleFeaturePolicyConfig) {
		this.config = config;
	}

	/**
	 * 检查功能是否可见
	 * @param featureKey 功能键
	 * @returns 是否可见
	 */
	allows(featureKey: FeatureKey): boolean {
		// 首先检查是否在禁止列表中
		if (this.config.forbidden_entries.includes(featureKey)) {
			return false;
		}

		// 然后检查对应的能力开关
		switch (featureKey) {
			case FeatureKey.CHAT_INTERFACE:
				return this.config.chat_enabled;
			case FeatureKey.IMAGE_UPLOAD:
				return this.config.image_upload_enabled;
			case FeatureKey.MODEL_SELECTION:
				return this.config.builtin_route_enabled || this.config.byok_enabled;
			case FeatureKey.BUILTIN_ROUTE:
				return this.config.builtin_route_enabled;
			case FeatureKey.BYOK_ROUTE:
				return this.config.byok_enabled;
			case FeatureKey.TOOL_RESULTS:
				return this.config.tool_result_enabled;
			case FeatureKey.RICH_UI_HOST:
				return this.config.rich_ui_enabled;
			case FeatureKey.SPIRIT_CARDS:
				return this.config.rich_ui_enabled;
			default:
				// 默认拒绝未定义的功能
				return false;
		}
	}

	/**
	 * 检查多个功能是否全部可见
	 * @param featureKeys 功能键数组
	 * @returns 是否全部可见
	 */
	allowsAll(featureKeys: FeatureKey[]): boolean {
		return featureKeys.every(key => this.allows(key));
	}

	/**
	 * 检查任意功能是否可见
	 * @param featureKeys 功能键数组
	 * @returns 是否任意可见
	 */
	allowsAny(featureKeys: FeatureKey[]): boolean {
		return featureKeys.some(key => this.allows(key));
	}

	/**
	 * 导出快照
	 * 用于发布前比对和 UI 回归测试
	 */
	exportSnapshot(): FeaturePolicySnapshot {
		return {
			policy_version: this.config.policy_version,
			visible_entries: this.getVisibleEntries(),
			hidden_entries: this.getHiddenEntries(),
			forbidden_entries: [...this.config.forbidden_entries],
			timestamp: new Date().toISOString(),
			validation_baseline_id: this.config.validation_baseline_id,
		};
	}

	/**
	 * 获取所有可见入口
	 */
	private getVisibleEntries(): string[] {
		const allFeatures = Object.values(FeatureKey);
		return allFeatures.filter(key => this.allows(key));
	}

	/**
	 * 获取所有隐藏入口
	 */
	private getHiddenEntries(): string[] {
		const allFeatures = Object.values(FeatureKey);
		return allFeatures.filter(key => !this.allows(key));
	}

	/**
	 * 验证快照是否与预期一致
	 * 用于 UI 回归测试
	 */
	validateAgainstBaseline(): ValidationResult {
		const snapshot = this.exportSnapshot();
		const visibleMatches = this.arraysEqual(
			snapshot.visible_entries.sort(),
			this.config.expected_visible_entries.sort()
		);
		const hiddenMatches = this.arraysEqual(
			snapshot.hidden_entries.sort(),
			this.config.expected_hidden_entries.sort()
		);

		return {
			valid: visibleMatches && hiddenMatches,
			visible_matches: visibleMatches,
			hidden_matches: hiddenMatches,
			missing_visible: this.config.expected_visible_entries.filter(
				e => !snapshot.visible_entries.includes(e)
			),
			unexpected_visible: snapshot.visible_entries.filter(
				e => !this.config.expected_visible_entries.includes(e)
			),
		};
	}

	private arraysEqual(a: string[], b: string[]): boolean {
		if (a.length !== b.length) return false;
		return a.every((val, index) => val === b[index]);
	}
}

/**
 * 功能策略快照
 */
export interface FeaturePolicySnapshot {
	policy_version: string;
	visible_entries: string[];
	hidden_entries: string[];
	forbidden_entries: string[];
	timestamp: string;
	validation_baseline_id: string | null;
}

/**
 * 验证结果
 */
export interface ValidationResult {
	valid: boolean;
	visible_matches: boolean;
	hidden_matches: boolean;
	missing_visible: string[];
	unexpected_visible: string[];
}

/**
 * 创建默认的 RoCo 产品策略
 * 
 * 根据 PRD US-006 和 ADR-004，RoCo 产品只暴露：
 * - 聊天界面
 * - 图片上传
 * - 模型/Key 配置（内置轨道 + BYOK）
 * - 工具结果展示
 * - 富卡片宿主
 */
export function createRocoDefaultPolicy(): VisibleFeaturePolicy {
	const config: VisibleFeaturePolicyConfig = {
		// 核心能力：全部开启
		chat_enabled: true,
		image_upload_enabled: true,
		builtin_route_enabled: true,
		byok_enabled: true,
		tool_result_enabled: true,
		rich_ui_enabled: true,

		// 禁止的 Open WebUI 原生功能
		forbidden_entries: [
			FeatureKey.NOTES,
			FeatureKey.CHANNELS,
			FeatureKey.OPEN_TERMINAL,
			FeatureKey.KNOWLEDGE,
			FeatureKey.ADMIN_PANEL,
			FeatureKey.DOCUMENTS,
			FeatureKey.GALLERY,
			FeatureKey.WORKSPACE,
			FeatureKey.PROMPTS,
			FeatureKey.SETTINGS_ADVANCED,
		],

		// 元数据
		policy_version: '1.0.0',
		snapshot_scope: ['navigation', 'settings', 'chat', 'tools'],
		expected_visible_entries: [
			FeatureKey.CHAT_INTERFACE,
			FeatureKey.IMAGE_UPLOAD,
			FeatureKey.MODEL_SELECTION,
			FeatureKey.BUILTIN_ROUTE,
			FeatureKey.BYOK_ROUTE,
			FeatureKey.TOOL_RESULTS,
			FeatureKey.RICH_UI_HOST,
			FeatureKey.SPIRIT_CARDS,
		],
		expected_hidden_entries: [
			FeatureKey.NOTES,
			FeatureKey.CHANNELS,
			FeatureKey.OPEN_TERMINAL,
			FeatureKey.KNOWLEDGE,
			FeatureKey.ADMIN_PANEL,
			FeatureKey.DOCUMENTS,
			FeatureKey.GALLERY,
			FeatureKey.WORKSPACE,
			FeatureKey.PROMPTS,
			FeatureKey.SETTINGS_ADVANCED,
		],
		validation_baseline_id: null,
	};

	return new VisibleFeaturePolicy(config);
}
