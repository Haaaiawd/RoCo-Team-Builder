/**
 * MessageArtifacts 集成测试
 * 
 * 验证消息工件渲染、工具调用折叠卡片和 Rich UI 宿主
 */

import {
	renderToolCallCard,
	renderRichUiHost,
	renderMessageArtifacts,
	parseMessageArtifacts,
} from './message-artifacts';

// 测试函数（需要配置测试框架后才能运行）
export function runMessageArtifactsTests() {
	console.log('Testing message artifacts...');

	// 测试工具调用卡片渲染
	const toolCallEvent = {
		tool_name: 'get_spirit_profile',
		input: { spirit_name: '火神' },
		output: { spirit_profile: { name: '火神', type: '火' } },
	};
	const toolCard = renderToolCallCard(toolCallEvent);
	console.log('Tool card rendered:', toolCard);
	if (!toolCard.includes('get_spirit_profile')) {
		throw new Error('Tool card should include tool name');
	}

	// 测试错误工具调用卡片
	const errorEvent = {
		tool_name: 'get_spirit_profile',
		input: { spirit_name: '火神' },
		error: 'Spirit not found',
	};
	const errorCard = renderToolCallCard(errorEvent);
	console.log('Error card rendered:', errorCard);
	if (!errorCard.includes('失败')) {
		throw new Error('Error card should show failure status');
	}

	// 测试 Rich UI 宿主渲染
	const richUiPayload = {
		type: 'spirit_card' as const,
		html: '<div class="spirit-card">Fire God</div>',
		fallback_text: 'Fire God - Fire Type',
	};
	const richUiHost = renderRichUiHost(richUiPayload);
	console.log('Rich UI host rendered:', richUiHost);
	if (!richUiHost.includes('spirit-card')) {
		throw new Error('Rich UI host should include HTML content');
	}

	// 测试消息工件渲染
	const artifacts = {
		tool_calls: [toolCallEvent],
		rich_ui: richUiPayload,
	};
	const rendered = renderMessageArtifacts(artifacts, { rich_ui_enabled: true });
	console.log('Message artifacts rendered:', rendered);
	if (!rendered.includes('get_spirit_profile')) {
		throw new Error('Rendered artifacts should include tool calls');
	}
	if (!rendered.includes('spirit-card')) {
		throw new Error('Rendered artifacts should include Rich UI');
	}

	// 测试 Rich UI 降级
	const renderedFallback = renderMessageArtifacts(artifacts, { rich_ui_enabled: false });
	console.log('Message artifacts with fallback:', renderedFallback);
	if (renderedFallback.includes('spirit-card')) {
		throw new Error('Rich UI should be disabled when policy says so');
	}
	if (!renderedFallback.includes('Fire God - Fire Type')) {
		throw new Error('Fallback text should be shown when Rich UI disabled');
	}

	// 测试解析消息工件
	const message = {
		tool_calls: [
			{
				function: {
					name: 'get_spirit_profile',
					arguments: JSON.stringify({ spirit_name: '火神' }),
				},
				output: { spirit_profile: { name: '火神', type: '火' } },
			},
		],
		card_html: '<div class="spirit-card">Fire God</div>',
		card_fallback_text: 'Fire God - Fire Type',
	};
	const parsed = parseMessageArtifacts(message);
	console.log('Parsed artifacts:', parsed);
	if (parsed.tool_calls.length !== 1) {
		throw new Error('Should parse 1 tool call');
	}
	if (parsed.tool_calls[0].tool_name !== 'get_spirit_profile') {
		throw new Error('Tool name should be parsed correctly');
	}
	if (!parsed.rich_ui) {
		throw new Error('Rich UI should be parsed');
	}

	console.log('All message artifacts tests passed!');
}
