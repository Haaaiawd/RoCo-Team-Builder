/**
 * ToolResultCard 集成测试
 * 
 * 验证工具结果卡片渲染和手账风格样式
 */

import {
	generateToolResultCard,
	generateToolResultCardCSS,
} from './tool-result-card';

// 测试函数（需要配置测试框架后才能运行）
export function runToolResultCardTests() {
	console.log('Testing tool result card...');

	// 测试成功卡片渲染
	const successConfig = {
		tool_name: 'get_spirit_profile',
		input: { spirit_name: '火神' },
		output: { spirit_profile: { name: '火神', type: '火' } },
	};
	const successCard = generateToolResultCard(successConfig);
	console.log('Success card rendered:', successCard);
	if (!successCard.includes('get_spirit_profile')) {
		throw new Error('Card should include tool name');
	}
	if (!successCard.includes('完成')) {
		throw new Error('Success card should show success status');
	}
	if (!successCard.includes('roco-tool-result-card')) {
		throw new Error('Card should have roco-tool-result-card class');
	}

	// 测试错误卡片渲染
	const errorConfig = {
		tool_name: 'get_spirit_profile',
		input: { spirit_name: '火神' },
		error: 'Spirit not found',
	};
	const errorCard = generateToolResultCard(errorConfig);
	console.log('Error card rendered:', errorCard);
	if (!errorCard.includes('失败')) {
		throw new Error('Error card should show failure status');
	}
	if (!errorCard.includes('roco-tool-result-card-error')) {
		throw new Error('Error card should have error class');
	}

	// 测试展开状态
	const expandedConfig = {
		...successConfig,
		expanded: true,
	};
	const expandedCard = generateToolResultCard(expandedConfig);
	console.log('Expanded card rendered:', expandedCard);
	if (!expandedCard.includes('roco-expanded')) {
		throw new Error('Expanded card should have expanded class');
	}

	// 测试标签样式
	const warmConfig = {
		...successConfig,
		label_style: 'warm' as const,
	};
	const warmCard = generateToolResultCard(warmConfig);
	console.log('Warm label card rendered:', warmCard);
	if (!warmCard.includes('roco-tool-result-card-label-warm')) {
		throw new Error('Warm label card should have warm label class');
	}

	// 测试 CSS 生成
	const css = generateToolResultCardCSS();
	console.log('CSS generated:', css);
	if (!css.includes('roco-tool-result-card')) {
		throw new Error('CSS should include card styles');
	}
	if (!css.includes('--roco-warm-gold')) {
		throw new Error('CSS should include warm gold color');
	}
	if (!css.includes('dashed')) {
		throw new Error('CSS should include dashed border for hand journal style');
	}

	console.log('All tool result card tests passed!');
}
