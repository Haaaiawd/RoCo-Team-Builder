/**
 * MessageArtifacts - 消息工件渲染
 * 
 * 负责渲染工具调用折叠卡片和 Rich UI 宿主，支持 fallback 文本降级。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §5.1 render_message_artifacts
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §10 性能考虑（Rich UI 降级）
 */

/**
 * 工具调用事件
 */
export interface ToolCallEvent {
	tool_name: string;
	input: Record<string, any>;
	output?: Record<string, any>;
	error?: string;
}

/**
 * Rich UI Payload
 */
export interface RichUiPayload {
	type: 'spirit_card' | 'tool_result';
	html: string;
	fallback_text: string;
	metadata?: Record<string, any>;
}

/**
 * 消息工件
 */
export interface MessageArtifacts {
	tool_calls: ToolCallEvent[];
	rich_ui: RichUiPayload | null;
}

/**
 * 渲染工具调用折叠卡片
 */
export function renderToolCallCard(event: ToolCallEvent, expanded: boolean = false): string {
	const { tool_name, input, output, error } = event;

	if (error) {
		return `
			<div class="roco-tool-card roco-tool-card-error">
				<div class="roco-tool-card-header">
					<span class="roco-tool-card-icon">⚠️</span>
					<span class="roco-tool-card-name">${tool_name}</span>
					<span class="roco-tool-card-status">失败</span>
				</div>
				<div class="roco-tool-card-body ${expanded ? 'roco-expanded' : ''}">
					<pre class="roco-tool-card-error-msg">${escapeHtml(error)}</pre>
				</div>
			</div>
		`;
	}

	return `
		<div class="roco-tool-card">
			<div class="roco-tool-card-header">
				<span class="roco-tool-card-icon">🔧</span>
				<span class="roco-tool-card-name">${tool_name}</span>
				<span class="roco-tool-card-status">完成</span>
			</div>
			<div class="roco-tool-card-body ${expanded ? 'roco-expanded' : ''}">
				<div class="roco-tool-card-section">
					<div class="roco-tool-card-section-title">输入</div>
					<pre class="roco-tool-card-code">${escapeHtml(JSON.stringify(input, null, 2))}</pre>
				</div>
				${output ? `
					<div class="roco-tool-card-section">
						<div class="roco-tool-card-section-title">输出</div>
						<pre class="roco-tool-card-code">${escapeHtml(JSON.stringify(output, null, 2))}</pre>
					</div>
				` : ''}
			</div>
		</div>
	`;
}

/**
 * 渲染 Rich UI 宿主
 */
export function renderRichUiHost(payload: RichUiPayload): string {
	if (!payload) return '';

	return `
		<div class="roco-rich-ui-host">
			${payload.html}
			<noscript>
				<div class="roco-rich-ui-fallback">
					<pre class="roco-rich-ui-fallback-text">${escapeHtml(payload.fallback_text)}</pre>
				</div>
			</noscript>
		</div>
	`;
}

/**
 * 渲染消息工件
 * 验收标准：工具调用可折叠展开，精灵卡片以 Rich UI 宿主渲染，必要时降级为文本
 */
export function renderMessageArtifacts(artifacts: MessageArtifacts, policy: { rich_ui_enabled: boolean }): string {
	let html = '';

	// 渲染工具调用
	if (artifacts.tool_calls.length > 0) {
		html += '<div class="roco-tool-cards-container">';
		artifacts.tool_calls.forEach(event => {
			html += renderToolCallCard(event);
		});
		html += '</div>';
	}

	// 渲染 Rich UI
	if (artifacts.rich_ui && policy.rich_ui_enabled) {
		html += renderRichUiHost(artifacts.rich_ui);
	} else if (artifacts.rich_ui) {
		// Rich UI 降级为文本
		html += `
			<div class="roco-rich-ui-fallback">
				<pre class="roco-rich-ui-fallback-text">${escapeHtml(artifacts.rich_ui.fallback_text)}</pre>
			</div>
		`;
	}

	return html;
}

/**
 * HTML 转义
 */
function escapeHtml(text: string): string {
	const map: Record<string, string> = {
		'&': '&amp;',
		'<': '&lt;',
		'>': '&gt;',
		'"': '&quot;',
		"'": '&#039;',
	};
	return text.replace(/[&<>"']/g, char => map[char]);
}

/**
 * 解析消息工件
 * 从 SSE 流或 API 响应中提取工具调用和 Rich UI payload
 */
export function parseMessageArtifacts(message: any): MessageArtifacts {
	const artifacts: MessageArtifacts = {
		tool_calls: [],
		rich_ui: null,
	};

	// 提取工具调用
	if (message.tool_calls && Array.isArray(message.tool_calls)) {
		artifacts.tool_calls = message.tool_calls.map((call: any) => ({
			tool_name: call.function?.name || call.tool_name,
			input: call.function?.arguments ? JSON.parse(call.function.arguments) : call.input,
			output: call.output,
			error: call.error,
		}));
	}

	// 提取 Rich UI payload
	if (message.rich_ui || message.card_html) {
		artifacts.rich_ui = {
			type: message.rich_ui?.type || 'spirit_card',
			html: message.rich_ui?.html || message.card_html || '',
			fallback_text: message.rich_ui?.fallback_text || message.card_fallback_text || '',
			metadata: message.rich_ui?.metadata || {},
		};
	}

	return artifacts;
}
