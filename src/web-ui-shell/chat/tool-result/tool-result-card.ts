/**
 * ToolResultCard - 工具结果卡片组件
 * 
 * 可折叠的工具调用结果展示组件，符合手账风格。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §7.2 组件语汇
 */

/**
 * 工具结果卡片配置
 */
export interface ToolResultCardConfig {
	/** 工具名称 */
	tool_name: string;
	/** 输入参数 */
	input: Record<string, any>;
	/** 输出结果 */
	output?: Record<string, any>;
	/** 错误信息 */
	error?: string;
	/** 是否展开 */
	expanded?: boolean;
	/** 手账标签样式 */
	label_style?: 'default' | 'warm' | 'gold';
}

/**
 * 生成工具结果卡片 HTML
 */
export function generateToolResultCard(config: ToolResultCardConfig): string {
	const { tool_name, input, output, error, expanded = false, label_style = 'default' } = config;

	const labelClass = `roco-tool-card-label-${label_style}`;
	const expandedClass = expanded ? 'roco-expanded' : '';

	if (error) {
		return `
			<div class="roco-tool-result-card roco-tool-result-card-error">
				<div class="roco-tool-result-card-header">
					<span class="roco-tool-result-card-icon">⚠️</span>
					<span class="roco-tool-result-card-name ${labelClass}">${tool_name}</span>
					<span class="roco-tool-result-card-status roco-tool-result-card-status-error">失败</span>
				</div>
				<div class="roco-tool-result-card-body ${expandedClass}">
					<pre class="roco-tool-result-card-error-msg">${escapeHtml(error)}</pre>
				</div>
			</div>
		`;
	}

	return `
		<div class="roco-tool-result-card">
			<div class="roco-tool-result-card-header">
				<span class="roco-tool-result-card-icon">🔧</span>
				<span class="roco-tool-result-card-name ${labelClass}">${tool_name}</span>
				<span class="roco-tool-result-card-status roco-tool-result-card-status-success">完成</span>
			</div>
			<div class="roco-tool-result-card-body ${expandedClass}">
				<div class="roco-tool-result-card-section">
					<div class="roco-tool-result-card-section-title">输入</div>
					<pre class="roco-tool-result-card-code">${escapeHtml(JSON.stringify(input, null, 2))}</pre>
				</div>
				${output ? `
					<div class="roco-tool-result-card-section">
						<div class="roco-tool-result-card-section-title">输出</div>
						<pre class="roco-tool-result-card-code">${escapeHtml(JSON.stringify(output, null, 2))}</pre>
					</div>
				` : ''}
			</div>
		</div>
	`;
}

/**
 * 生成工具结果卡片 CSS
 * 手账标签风格：暖金色 Hover/Active + 虚线内框
 */
export function generateToolResultCardCSS(): string {
	return `
		.roco-tool-result-card {
			background-color: var(--roco-cream-surface);
			border: 1px solid var(--roco-border-warm);
			border-radius: var(--roco-border-radius-md);
			padding: var(--roco-spacing-md);
			margin: var(--roco-spacing-md) 0;
			box-shadow: var(--roco-shadow-paper);
			transition: all var(--roco-duration-fast) var(--roco-easing-ease);
		}

		.roco-tool-result-card:hover {
			background-color: var(--roco-warm-gold);
			border-color: var(--roco-border-gold);
			transform: translateY(-1px);
			box-shadow: var(--roco-shadow-floating);
		}

		.roco-tool-result-card-error {
			background-color: #fef2f2;
			border-color: #fecaca;
		}

		.roco-tool-result-card-error:hover {
			background-color: #fee2e2;
			border-color: #fca5a5;
		}

		.roco-tool-result-card-header {
			display: flex;
			align-items: center;
			gap: var(--roco-spacing-sm);
			margin-bottom: var(--roco-spacing-sm);
		}

		.roco-tool-result-card-icon {
			font-size: var(--roco-font-size-lg);
		}

		.roco-tool-result-card-name {
			font-family: var(--roco-font-family-ui);
			font-size: var(--roco-font-size-base);
			font-weight: 600;
			color: var(--roco-text-primary);
			flex: 1;
		}

		.roco-tool-result-card-label-warm {
			color: var(--roco-warm-gold);
		}

		.roco-tool-result-card-label-gold {
			color: var(--roco-warm-gold-dark);
		}

		.roco-tool-result-card-status {
			font-family: var(--roco-font-family-ui);
			font-size: var(--roco-font-size-sm);
			font-weight: 600;
			padding: var(--roco-spacing-xs) var(--roco-spacing-sm);
			border-radius: var(--roco-border-radius-sm);
		}

		.roco-tool-result-card-status-success {
			background-color: #dcfce7;
			color: #166534;
		}

		.roco-tool-result-card-status-error {
			background-color: #fee2e2;
			color: #991b1b;
		}

		.roco-tool-result-card-body {
			max-height: 0;
			overflow: hidden;
			transition: max-height var(--roco-duration-normal) var(--roco-easing-ease);
		}

		.roco-tool-result-card-body.roco-expanded {
			max-height: 500px;
		}

		.roco-tool-result-card-section {
			margin-top: var(--roco-spacing-md);
		}

		.roco-tool-result-card-section-title {
			font-family: var(--roco-font-family-ui);
			font-size: var(--roco-font-size-sm);
			font-weight: 600;
			color: var(--roco-text-secondary);
			margin-bottom: var(--roco-spacing-xs);
		}

		.roco-tool-result-card-code {
			background-color: var(--roco-cream-surface-alt);
			border: 1px dashed var(--roco-border-warm);
			border-radius: var(--roco-border-radius-sm);
			padding: var(--roco-spacing-sm);
			font-family: monospace;
			font-size: var(--roco-font-size-sm);
			color: var(--roco-text-primary);
			white-space: pre-wrap;
			word-break: break-word;
		}

		.roco-tool-result-card-error-msg {
			background-color: #fef2f2;
			border: 1px dashed #fecaca;
			color: #991b1b;
		}
	`;
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
