/**
 * UiRouteState - UI 轨道状态管理
 * 
 * 管理当前活跃轨道（builtin 或 byok）、模型能力、配额状态等。
 * 确保不可静默切轨，明确提示用户下一步操作。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §6.1 UiRouteState
 */

/**
 * UI 轨道状态
 */
export interface UiRouteState {
	/** 当前活跃轨道：builtin 或 byok */
	active_route: 'builtin' | 'byok';
	/** 当前模型 ID */
	active_model_id: string | null;
	/** 当前聊天 ID */
	chat_id: string | null;
	/** 是否正在上传 */
	is_uploading: boolean;
	/** Rich UI 是否可用 */
	rich_ui_available: boolean;
	/** 当前模型是否支持视觉能力 */
	active_model_supports_vision: boolean | null;
	/** 内置轨道配额状态 */
	builtin_quota_status: 'available' | 'exhausted' | 'unknown';
}

/**
 * 轨道类型
 */
export type RouteType = 'builtin' | 'byok';

/**
 * 轨道状态管理器
 */
export class RouteStateManager {
	private state: UiRouteState;
	private listeners: Set<(state: UiRouteState) => void> = new Set();

	constructor(initialState?: Partial<UiRouteState>) {
		this.state = {
			active_route: 'builtin',
			active_model_id: null,
			chat_id: null,
			is_uploading: false,
			rich_ui_available: false,
			active_model_supports_vision: null,
			builtin_quota_status: 'unknown',
			...initialState,
		};
	}

	/**
	 * 获取当前状态
	 */
	getState(): UiRouteState {
		return { ...this.state };
	}

	/**
	 * 设置活跃轨道
	 * 验收标准：不可静默切轨，明确提示用户
	 */
	setActiveRoute(route: RouteType): void {
		const oldRoute = this.state.active_route;
		if (oldRoute === route) return;

		this.state.active_route = route;
		this.notifyListeners();
	}

	/**
	 * 设置活跃模型
	 */
	setActiveModel(modelId: string | null): void {
		this.state.active_model_id = modelId;
		this.notifyListeners();
	}

	/**
	 * 设置聊天 ID
	 */
	setChatId(chatId: string | null): void {
		this.state.chat_id = chatId;
		this.notifyListeners();
	}

	/**
	 * 设置上传状态
	 */
	setUploading(isUploading: boolean): void {
		this.state.is_uploading = isUploading;
		this.notifyListeners();
	}

	/**
	 * 设置 Rich UI 可用性
	 */
	setRichUiAvailable(available: boolean): void {
		this.state.rich_ui_available = available;
		this.notifyListeners();
	}

	/**
	 * 设置模型视觉能力
	 */
	setModelVisionCapability(supportsVision: boolean | null): void {
		this.state.active_model_supports_vision = supportsVision;
		this.notifyListeners();
	}

	/**
	 * 设置内置轨道配额状态
	 */
	setBuiltinQuotaStatus(status: 'available' | 'exhausted' | 'unknown'): void {
		this.state.builtin_quota_status = status;
		this.notifyListeners();
	}

	/**
	 * 检查是否可以发送消息
	 * 验收标准：当前轨道不可用时，不发生静默切轨，而是显示明确的下一步提示
	 */
	canSend(): { canSend: boolean; reason?: string; nextStep?: string } {
		const { active_route, builtin_quota_status, active_model_id, active_model_supports_vision } = this.state;

		// 检查是否有活跃模型
		if (!active_model_id) {
			return {
				canSend: false,
				reason: '未选择模型',
				nextStep: '请先选择一个模型',
			};
		}

		// 检查内置轨道配额
		if (active_route === 'builtin' && builtin_quota_status === 'exhausted') {
			return {
				canSend: false,
				reason: '内置轨道额度已耗尽',
				nextStep: '请切换到 BYOK 轨道或等待额度重置',
			};
		}

		// 检查视觉能力（如果需要上传图片）
		if (this.state.is_uploading && active_model_supports_vision === false) {
			return {
				canSend: false,
				reason: '当前模型不支持视觉能力',
				nextStep: '请切换到支持视觉的模型或移除图片',
			};
		}

		return { canSend: true };
	}

	/**
	 * 注册状态监听器
	 */
	subscribe(listener: (state: UiRouteState) => void): () => void {
		this.listeners.add(listener);
		return () => {
			this.listeners.delete(listener);
		};
	}

	private notifyListeners(): void {
		this.listeners.forEach(listener => listener(this.getState()));
	}
}

/**
 * 创建轨道状态管理器
 */
export function createRouteStateManager(initialState?: Partial<UiRouteState>): RouteStateManager {
	return new RouteStateManager(initialState);
}
