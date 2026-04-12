/**
 * 轨道状态管理集成测试
 * 
 * 验证轨道状态切换、canSend 检查和不可静默切轨规则
 * 
 * 验收标准：
 * - 当前轨道不可用时，不发生静默切轨，而是显示明确的下一步提示
 */

import {
	createRouteStateManager,
	UiRouteState,
} from './route-state';

// 测试函数（需要配置测试框架后才能运行）
export function runRouteStateTests() {
	console.log('Testing route state manager...');

	// 测试创建管理器
	const manager = createRouteStateManager();
	console.log('Created manager');

	// 测试初始状态
	const initialState = manager.getState();
	console.log('Initial state:', initialState);
	if (initialState.active_route !== 'builtin') {
		throw new Error('Initial route should be builtin');
	}

	// 测试设置活跃轨道
	manager.setActiveRoute('byok');
	const afterRouteChange = manager.getState();
	console.log('After route change:', afterRouteChange);
	if (afterRouteChange.active_route !== 'byok') {
		throw new Error('Route should be byok');
	}

	// 测试设置模型
	manager.setActiveModel('gpt-4');
	const afterModelChange = manager.getState();
	console.log('After model change:', afterModelChange);
	if (afterModelChange.active_model_id !== 'gpt-4') {
		throw new Error('Model should be gpt-4');
	}

	// 测试 canSend - 正常情况
	const canSendNormal = manager.canSend();
	console.log('canSend (normal):', canSendNormal);
	if (!canSendNormal.canSend) {
		throw new Error('Should be able to send with model selected');
	}

	// 测试 canSend - 无模型
	manager.setActiveModel(null);
	const canSendNoModel = manager.canSend();
	console.log('canSend (no model):', canSendNoModel);
	if (canSendNoModel.canSend) {
		throw new Error('Should not be able to send without model');
	}
	if (!canSendNoModel.nextStep) {
		throw new Error('Should provide next step when cannot send');
	}

	// 测试 canSend - 额度耗尽
	manager.setActiveModel('roco-agent');
	manager.setActiveRoute('builtin');
	manager.setBuiltinQuotaStatus('exhausted');
	const canSendExhausted = manager.canSend();
	console.log('canSend (exhausted):', canSendExhausted);
	if (canSendExhausted.canSend) {
		throw new Error('Should not be able to send when quota exhausted');
	}
	if (!canSendExhausted.nextStep) {
		throw new Error('Should provide next step when quota exhausted');
	}

	// 测试 canSend - 视觉能力不支持
	manager.setBuiltinQuotaStatus('available');
	manager.setUploading(true);
	manager.setModelVisionCapability(false);
	const canSendNoVision = manager.canSend();
	console.log('canSend (no vision):', canSendNoVision);
	if (canSendNoVision.canSend) {
		throw new Error('Should not be able to send when uploading but model does not support vision');
	}
	if (!canSendNoVision.nextStep) {
		throw new Error('Should provide next step when vision not supported');
	}

	console.log('All route state tests passed!');
}
