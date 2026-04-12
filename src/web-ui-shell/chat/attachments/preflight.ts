/**
 * ImageCapabilityPreflight - 图片能力预检
 * 
 * 在发送前依据当前轨道与 supports_vision 做图片能力预检。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §5.1 preflight_image_capability
 * 参考：02_ARCHITECTURE_OVERVIEW.md §3.5 CAPABILITY_
 */

import { UiRouteState } from '../../integrations/agent-backend-connection/route-state';

/**
 * 能力预检结果
 */
export interface PreflightResult {
	/** 是否允许发送 */
	allowed: boolean;
	/** 错误类型 */
	error_type?: 'CAPABILITY_UNSUPPORTED' | 'QUOTA_EXHAUSTED' | 'ROUTE_UNAVAILABLE' | 'MODEL_NOT_SELECTED';
	/** 错误消息 */
	error_message?: string;
	/** 下一步提示 */
	next_step?: string;
}

/**
 * 能力预检器
 */
export class ImageCapabilityPreflight {
	/**
	 * 执行能力预检
	 * 验收标准：前端在发送前阻止请求并提示切换支持视觉的模型或切回内置轨道
	 */
	preflight(routeState: UiRouteState, hasImage: boolean): PreflightResult {
		// 如果没有图片，直接允许
		if (!hasImage) {
			return { allowed: true };
		}

		// 检查是否有活跃模型
		if (!routeState.active_model_id) {
			return {
				allowed: false,
				error_type: 'MODEL_NOT_SELECTED',
				error_message: '请先选择一个模型',
				next_step: '在模型设置中选择一个模型',
			};
		}

		// 检查模型是否支持视觉能力
		if (routeState.active_model_supports_vision === false) {
			// BYOK 轨道且模型不支持视觉
			if (routeState.active_route === 'byok') {
				return {
					allowed: false,
					error_type: 'CAPABILITY_UNSUPPORTED',
					error_message: '当前模型不支持视觉能力',
					next_step: '请切换到支持视觉的模型，或切回内置轨道',
				};
			}
			// 内置轨道且模型不支持视觉（理论上不应该发生）
			return {
				allowed: false,
				error_type: 'CAPABILITY_UNSUPPORTED',
				error_message: '当前模型不支持视觉能力',
				next_step: '请选择支持视觉的模型',
			};
		}

		// 检查内置轨道配额
		if (routeState.active_route === 'builtin' && routeState.builtin_quota_status === 'exhausted') {
			return {
				allowed: false,
				error_type: 'QUOTA_EXHAUSTED',
				error_message: '内置轨道额度已耗尽',
				next_step: '请切换到 BYOK 轨道或等待额度重置',
			};
		}

		// 检查轨道是否可用
		if (routeState.active_route === 'builtin' && routeState.builtin_quota_status === 'unknown') {
			return {
				allowed: false,
				error_type: 'ROUTE_UNAVAILABLE',
				error_message: '内置轨道状态未知',
				next_step: '请检查后端连接状态',
			};
		}

		// 验收标准：当前模型支持视觉且额度可用，请求进入正常的图文消息链路
		return { allowed: true };
	}

	/**
	 * 生成 CAPABILITY_ 错误提示
	 */
	generateCapabilityError(route: 'builtin' | 'byok'): string {
		if (route === 'byok') {
			return 'CAPABILITY_UNSUPPORTED: 当前 BYOK 模型不支持视觉能力，请切换支持视觉的模型或切回内置轨道';
		}
		return 'CAPABILITY_UNSUPPORTED: 当前模型不支持视觉能力，请选择支持视觉的模型';
	}

	/**
	 * 生成 QUOTA_ 错误提示
	 */
	generateQuotaError(): string {
		return 'QUOTA_EXHAUSTED: 内置轨道额度已耗尽，请切换到 BYOK 轨道或等待额度重置';
	}
}

/**
 * 创建能力预检器
 */
export function createImageCapabilityPreflight(): ImageCapabilityPreflight {
	return new ImageCapabilityPreflight();
}
