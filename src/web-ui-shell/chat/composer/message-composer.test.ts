/**
 * MessageComposer 集成测试
 * 
 * 验证消息编写器的整合逻辑
 */

import {
	MessageComposer,
	createMessageComposer,
} from './message-composer';
import { UiRouteState } from '../../integrations/agent-backend-connection/route-state';

// 测试函数（需要配置测试框架后才能运行）
export function runMessageComposerTests() {
	console.log('Testing message composer...');

	const composer = createMessageComposer();

	// 测试正常文本消息发送
	const normalState: UiRouteState = {
		active_route: 'builtin',
		active_model_id: 'roco-agent',
		chat_id: 'chat-1',
		is_uploading: false,
		rich_ui_available: false,
		active_model_supports_vision: true,
		builtin_quota_status: 'available',
	};
	const textRequest = {
		text: 'Hello',
		has_image: false,
	};
	const textResult = composer.prepareSendMessage(normalState, textRequest);
	console.log('Text result:', textResult);
	if (!textResult.allowed) {
		throw new Error('Should allow sending text message');
	}

	// 测试正常图片消息发送
	const imageRequest = {
		text: 'What is this?',
		has_image: true,
		image_file: new File([''], 'test.jpg'),
	};
	const imageResult = composer.prepareSendMessage(normalState, imageRequest);
	console.log('Image result:', imageResult);
	if (!imageResult.allowed) {
		throw new Error('Should allow sending image message when model supports vision and quota is available');
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
	const byokImageResult = composer.prepareSendMessage(byokNoVisionState, imageRequest);
	console.log('BYOK no vision result:', byokImageResult);
	if (byokImageResult.allowed) {
		throw new Error('Should block BYOK image when model does not support vision');
	}
	if (!byokImageResult.preflight) {
		throw new Error('Should have preflight result');
	}
	if (byokImageResult.preflight.error_type !== 'CAPABILITY_UNSUPPORTED') {
		throw new Error('Error type should be CAPABILITY_UNSUPPORTED');
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
	const quotaResult = composer.prepareSendMessage(builtinExhaustedState, textRequest);
	console.log('Quota exhausted result:', quotaResult);
	if (quotaResult.allowed) {
		throw new Error('Should block when builtin quota is exhausted');
	}
	if (!quotaResult.quota_alert) {
		throw new Error('Should have quota alert');
	}
	if (quotaResult.quota_alert.status !== 'exhausted') {
		throw new Error('Status should be exhausted');
	}

	// 测试错误提示 HTML 生成
	const errorHTML = composer.generateErrorAlert(byokImageResult);
	console.log('Error HTML length:', errorHTML.length);
	if (!errorHTML.includes('CAPABILITY_UNSUPPORTED')) {
		throw new Error('Error HTML should include CAPABILITY_UNSUPPORTED');
	}
	if (!errorHTML.includes('roco-error-alert')) {
		throw new Error('Error HTML should have roco-error-alert class');
	}

	const quotaHTML = composer.generateErrorAlert(quotaResult);
	console.log('Quota HTML length:', quotaHTML.length);
	if (!quotaHTML.includes('QUOTA_EXHAUSTED')) {
		throw new Error('Quota HTML should include QUOTA_EXHAUSTED');
	}
	if (!quotaHTML.includes('roco-quota-alert')) {
		throw new Error('Quota HTML should have roco-quota-alert class');
	}

	// 测试 canSendText
	const canSendTextAvailable = composer.canSendText(normalState);
	console.log('Can send text available:', canSendTextAvailable);
	if (!canSendTextAvailable) {
		throw new Error('Should be able to send text when quota is available');
	}

	const canSendTextExhausted = composer.canSendText(builtinExhaustedState);
	console.log('Can send text exhausted:', canSendTextExhausted);
	if (canSendTextExhausted) {
		throw new Error('Should not be able to send text when quota is exhausted');
	}

	// 测试 canSendImage
	const canSendImageAvailable = composer.canSendImage(normalState);
	console.log('Can send image available:', canSendImageAvailable);
	if (!canSendImageAvailable) {
		throw new Error('Should be able to send image when model supports vision and quota is available');
	}

	const canSendImageNoVision = composer.canSendImage(byokNoVisionState);
	console.log('Can send image no vision:', canSendImageNoVision);
	if (canSendImageNoVision) {
		throw new Error('Should not be able to send image when model does not support vision');
	}

	console.log('All message composer tests passed!');
}
