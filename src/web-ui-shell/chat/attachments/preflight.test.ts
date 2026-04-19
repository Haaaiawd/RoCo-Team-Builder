/**
 * ImageCapabilityPreflight 集成测试
 * 
 * 验证图片能力预检逻辑
 */

import {
	ImageCapabilityPreflight,
	createImageCapabilityPreflight,
} from './preflight';
import { UiRouteState } from '../../integrations/agent-backend-connection/route-state';

// 测试函数（需要配置测试框架后才能运行）
export function runPreflightTests() {
	console.log('Testing image capability preflight...');

	const preflight = createImageCapabilityPreflight();

	// 测试无图片情况
	const noImageState: UiRouteState = {
		active_route: 'builtin',
		active_model_id: 'roco-agent',
		chat_id: 'chat-1',
		is_uploading: false,
		rich_ui_available: false,
		active_model_supports_vision: true,
		builtin_quota_status: 'available',
	};
	const noImageResult = preflight.preflight(noImageState, false);
	console.log('No image result:', noImageResult);
	if (!noImageResult.allowed) {
		throw new Error('Should allow sending without image');
	}

	// 测试 BYOK 轨道且模型不支持视觉
	const byokNoVisionState: UiRouteState = {
		active_route: 'byok',
		active_model_id: 'gpt-4',
		chat_id: 'chat-1',
		is_uploading: true,
		rich_ui_available: false,
		active_model_supports_vision: false,
		builtin_quota_status: 'available',
	};
	const byokNoVisionResult = preflight.preflight(byokNoVisionState, true);
	console.log('BYOK no vision result:', byokNoVisionResult);
	if (byokNoVisionResult.allowed) {
		throw new Error('Should block BYOK image when model does not support vision');
	}
	if (byokNoVisionResult.error_type !== 'CAPABILITY_UNSUPPORTED') {
		throw new Error('Error type should be CAPABILITY_UNSUPPORTED');
	}

	// 测试内置轨道配额耗尽
	const builtinExhaustedState: UiRouteState = {
		active_route: 'builtin',
		active_model_id: 'roco-agent',
		chat_id: 'chat-1',
		is_uploading: true,
		rich_ui_available: false,
		active_model_supports_vision: true,
		builtin_quota_status: 'exhausted',
	};
	const builtinExhaustedResult = preflight.preflight(builtinExhaustedState, true);
	console.log('Builtin exhausted result:', builtinExhaustedResult);
	if (builtinExhaustedResult.allowed) {
		throw new Error('Should block when builtin quota is exhausted');
	}
	if (builtinExhaustedResult.error_type !== 'QUOTA_EXHAUSTED') {
		throw new Error('Error type should be QUOTA_EXHAUSTED');
	}

	// 测试正常情况
	const normalState: UiRouteState = {
		active_route: 'builtin',
		active_model_id: 'roco-agent',
		chat_id: 'chat-1',
		is_uploading: true,
		rich_ui_available: false,
		active_model_supports_vision: true,
		builtin_quota_status: 'available',
	};
	const normalResult = preflight.preflight(normalState, true);
	console.log('Normal result:', normalResult);
	if (!normalResult.allowed) {
		throw new Error('Should allow sending when model supports vision and quota is available');
	}

	// 测试未选择模型
	const noModelState: UiRouteState = {
		active_route: 'builtin',
		active_model_id: null,
		chat_id: 'chat-1',
		is_uploading: true,
		rich_ui_available: false,
		active_model_supports_vision: true,
		builtin_quota_status: 'available',
	};
	const noModelResult = preflight.preflight(noModelState, true);
	console.log('No model result:', noModelResult);
	if (noModelResult.allowed) {
		throw new Error('Should block when no model is selected');
	}

	console.log('All preflight tests passed!');
}
