/**
 * RichUiHost - Rich UI 宿主
 * 
 * 负责渲染精灵卡片等 Rich UI 内容，支持 iframe 沙箱和降级文本。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §7.1 Rich UI (sandboxed iframe / HTML embed)
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §10 性能考虑（Rich UI 降级）
 */

/**
 * Rich UI 宿主配置
 */
export interface RichUiHostConfig {
	/** HTML 内容 */
	html: string;
	/** 降级文本 */
	fallback_text: string;
	/** 是否使用 iframe 沙箱 */
	use_iframe?: boolean;
	/** iframe 沙箱属性 */
	sandbox?: string;
	/** 宿主样式 */
	host_style?: string;
}

/**
 * 生成 Rich UI 宿主 HTML
 */
export function generateRichUiHost(config: RichUiHostConfig): string {
	const { html, fallback_text, use_iframe = false, sandbox = 'allow-scripts allow-same-origin', host_style = '' } = config;

	if (use_iframe) {
		// 使用 iframe 沙箱模式
		return `
			<div class="roco-rich-ui-host" style="${host_style}">
				<iframe 
					class="roco-rich-ui-iframe"
					sandbox="${sandbox}"
					srcdoc="${escapeHtmlAttribute(html)}"
					title="Rich UI Content"
				></iframe>
				<noscript>
					<div class="roco-rich-ui-fallback">
						<pre class="roco-rich-ui-fallback-text">${escapeHtml(fallback_text)}</pre>
					</div>
				</noscript>
			</div>
		`;
	} else {
		// 直接嵌入 HTML 模式
		return `
			<div class="roco-rich-ui-host" style="${host_style}">
				<div class="roco-rich-ui-content">
					${html}
				</div>
				<noscript>
					<div class="roco-rich-ui-fallback">
						<pre class="roco-rich-ui-fallback-text">${escapeHtml(fallback_text)}</pre>
					</div>
				</noscript>
			</div>
		`;
	}
}

/**
 * 生成 Rich UI 宿主 CSS
 * 手账风格：与主区保持一致的视觉语言
 */
export function generateRichUiHostCSS(): string {
	return `
		.roco-rich-ui-host {
			border: 1px solid var(--roco-border-warm);
			border-radius: var(--roco-border-radius-md);
			background-color: var(--roco-cream-surface);
			overflow: hidden;
			margin: var(--roco-spacing-md) 0;
			box-shadow: var(--roco-shadow-paper);
		}

		.roco-rich-ui-iframe {
			width: 100%;
			border: none;
			min-height: 300px;
			background-color: var(--roco-cream-surface);
		}

		.roco-rich-ui-content {
			padding: var(--roco-spacing-md);
		}

		.roco-rich-ui-fallback {
			padding: var(--roco-spacing-md);
			background-color: var(--roco-parchment-light);
			border: 1px dashed var(--roco-border-warm);
			border-radius: var(--roco-border-radius-sm);
		}

		.roco-rich-ui-fallback-text {
			font-family: var(--roco-font-family-primary);
			font-size: var(--roco-font-size-base);
			line-height: var(--roco-line-height-normal);
			color: var(--roco-text-primary);
			white-space: pre-wrap;
			word-break: break-word;
		}
	`;
}

/**
 * Rich UI 宿主管理器
 */
export class RichUiHostManager {
	private config: RichUiHostConfig;

	constructor(config: RichUiHostConfig) {
		this.config = config;
	}

	/**
	 * 渲染宿主
	 */
	render(): string {
		return generateRichUiHost(this.config);
	}

	/**
	 * 渲染降级文本
	 */
	renderFallback(): string {
		return `
			<div class="roco-rich-ui-fallback">
				<pre class="roco-rich-ui-fallback-text">${escapeHtml(this.config.fallback_text)}</pre>
			</div>
		`;
	}

	/**
	 * 更新配置
	 */
	updateConfig(config: Partial<RichUiHostConfig>): void {
		this.config = { ...this.config, ...config };
	}

	/**
	 * 检查是否可以使用 iframe
	 */
	canUseIframe(): boolean {
		// 检查浏览器是否支持 iframe
		return typeof window !== 'undefined' && typeof HTMLIFrameElement !== 'undefined';
	}
}

/**
 * 创建 Rich UI 宿主管理器
 */
export function createRichUiHostManager(config: RichUiHostConfig): RichUiHostManager {
	return new RichUiHostManager(config);
}

/**
 * HTML 属性转义
 */
function escapeHtmlAttribute(text: string): string {
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
