/**
 * QuotaGuard 集成测试
 * 
 * 验证配额守卫逻辑
 */

import {
	QuotaGuard,
	createQuotaGuard,
} from './quota-guard';
import { UiRouteState } from '../../integrations/agent-backend-connection/route-state';

// 测试函数（需要配置测试框架后才能运行）
export function runQuotaGuardTests() {
	console.log('Testing quota guard...');

	const guard = createQuotaGuard();

	// 测试 BYOK 轨道（不显示配额提示）
	const byokState: UiRouteState = {
		active_route: 'byok',
		active_model_id: 'gpt-4',
		chat_id: 'chat-1',
		is_uploading: false,
		rich_ui_available: false,
		active_model_supports_vision: true,
		builtin_quota_status: 'available',
	};
	const byokAlert = guard.checkQuota(byokState);
	console.log('BYOK alert:', byokAlert);
	if (byokAlert.show_alert) {
		throw new Error('BYOK route should not show quota alert');
	}
	if (!byokAlert.allow_send) {
		throw new Error('BYOK route should allow sending');
	}

	// 测试内置轨道配额可用
	const builtinAvailableState: UiRouteState = {
		active_route: 'builtin',
		active_model_id: 'roco-agent',
		chat_id: 'chat-1',
		is_uploading: false,
		rich_ui_available: false,
		active_model_supports_vision: true,
		builtin_quota_status: 'available',
	};
	const builtinAvailableAlert = guard.checkQuota(builtinAvailableState);
	console.log('Builtin available alert:', builtinAvailableAlert);
	if (builtinAvailableAlert.show_alert) {
		throw new Error('Available quota should not show alert');
	}
	if (!builtinAvailableAlert.allow_send) {
		throw new Error('Available quota should allow sending');
	}

	// 测试内置轨道配额耗尽
	const builtinExhaustedState: UiRouteState = {
		active_route: 'builtin',
		active_model_id: 'roco-agent',
		chat_id: 'chat-1',
		is_uploading: false,
		rich_ui_available: false,
		active_model_supports_vision: true,
		builtin_quota_status: 'exhausted',
	};
	const builtinExhaustedAlert = guard.checkQuota(builtinExhaustedState);
	console.log('Builtin exhausted alert:', builtinExhaustedAlert);
	if (!builtinExhaustedAlert.show_alert) {
		throw new Error('Exhausted quota should show alert');
	}
	if (builtinExhaustedAlert.status !== 'exhausted') {
		throw new Error('Status should be exhausted');
	}
	if (!builtinExhaustedAlert.message.includes('QUOTA_EXHAUSTED')) {
		throw new Error('Message should include QUOTA_EXHAUSTED');
	}
	if (builtinExhaustedAlert.allow_send) {
		throw new Error('Exhausted quota should not allow sending');
	}

	// 测试内置轨道配额未知
	const builtinUnknownState: UiRouteState = {
		active_route: 'builtin',
		active_model_id: 'roco-agent',
		chat_id: 'chat-1',
		is_uploading: false,
		rich_ui_available: false,
		active_model_supports_vision: true,
		builtin_quota_status: 'unknown',
	};
	const builtinUnknownAlert = guard.checkQuota(builtinUnknownState);
	console.log('Builtin unknown alert:', builtinUnknownAlert);
	if (!builtinUnknownAlert.show_alert) {
		throw new Error('Unknown quota should show alert');
	}
	if (builtinUnknownAlert.status !== 'unknown') {
		throw new Error('Status should be unknown');
	}
	if (builtinUnknownAlert.allow_send) {
		throw new Error('Unknown quota should not allow sending');
	}

	// 测试生成配额提示 HTML
	const alertHTML = guard.generateQuotaAlertHTML(builtinExhaustedAlert);
	console.log('Alert HTML length:', alertHTML.length);
	if (!alertHTML.includes('QUOTA_EXHAUSTED')) {
		throw new Error('Alert HTML should include QUOTA_EXHAUSTED');
	}
	if (!alertHTML.includes('roco-quota-alert')) {
		throw new Error('Alert HTML should have roco-quota-alert class');
	}

	// 测试 canSend 方法
	const canSendAvailable = guard.canSend(builtinAvailableState);
	console.log('Can send available:', canSendAvailable);
	if (!canSendAvailable) {
		throw new Error('Should be able to send when quota is available');
	}

	const canSendExhausted = guard.canSend(builtinExhaustedState);
	console.log('Can send exhausted:', canSendExhausted);
	if (canSendExhausted) {
		throw new Error('Should not be able to send when quota is exhausted');
	}

	console.log('All quota guard tests passed!');
}
