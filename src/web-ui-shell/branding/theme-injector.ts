/**
 * ThemeInjector - 主题注入器
 * 
 * 负责将主题 CSS 和字体资源注入到页面，实现复古冒险者手账风。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §7.2 Visual Language & Theme Override Strategy
 */

/**
 * 主题注入器配置
 */
export interface ThemeInjectorConfig {
	/** 主题 CSS 路径 */
	themeCssPath: string;
	/** 字体加载配置 */
	fonts?: FontConfig[];
	/** 是否自动注入 */
	autoInject?: boolean;
}

/**
 * 字体配置
 */
export interface FontConfig {
	/** 字体名称 */
	name: string;
	/** 字体族 */
	family: string;
	/** 字体 URL */
	url: string;
	/** 字体格式 */
	format: 'woff2' | 'woff' | 'ttf';
}

/**
 * 默认字体配置
 * 使用 Google Fonts 加载手账风格字体
 */
export const DEFAULT_FONTS: FontConfig[] = [
	{
		name: 'Crimson Pro',
		family: 'Crimson Pro',
		url: 'https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&display=swap',
		format: 'woff2',
	},
	{
		name: 'Lato',
		family: 'Lato',
		url: 'https://fonts.googleapis.com/css2?family=Lato:wght@400;600;700&display=swap',
		format: 'woff2',
	},
	{
		name: 'Patrick Hand',
		family: 'Patrick Hand',
		url: 'https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap',
		format: 'woff2',
	},
];

/**
 * 主题注入器
 */
export class ThemeInjector {
	private config: ThemeInjectorConfig;
	private styleElementId = 'roco-theme-override';
	private fontLinkId = 'roco-fonts';

	constructor(config: Partial<ThemeInjectorConfig> = {}) {
		this.config = {
			themeCssPath: '/static/web-ui-shell/branding/theme-override.css',
			fonts: DEFAULT_FONTS,
			autoInject: false,
			...config,
		};
	}

	/**
	 * 注入主题到页面
	 * 验收标准：呈现统一的复古手账风，而非 Open WebUI 默认平台风格
	 */
	inject(): void {
		// 注入字体
		this.injectFonts();

		// 注入主题 CSS
		this.injectThemeCSS();
	}

	/**
	 * 注入字体
	 */
	private injectFonts(): void {
		// 移除旧的字体链接
		const existing = document.getElementById(this.fontLinkId);
		if (existing) {
			existing.remove();
		}

		// 创建字体链接元素
		const fontLink = document.createElement('link');
		fontLink.id = this.fontLinkId;
		fontLink.rel = 'stylesheet';
		
		// 组合所有 Google Fonts URL
		const fontUrls = this.config.fonts?.map(f => f.url).join('&');
		fontLink.href = fontUrls || '';

		// 插入到 head
		document.head.appendChild(fontLink);
	}

	/**
	 * 注入主题 CSS
	 */
	private injectThemeCSS(): void {
		// 移除旧的主题样式
		const existing = document.getElementById(this.styleElementId);
		if (existing) {
			existing.remove();
		}

		// 创建新的样式元素
		const style = document.createElement('style');
		style.id = this.styleElementId;
		
		// 加载主题 CSS 内容
		this.loadThemeCSS().then(cssContent => {
			style.textContent = cssContent;
			document.head.appendChild(style);
		}).catch(error => {
			console.error('Failed to load theme CSS:', error);
		});
	}

	/**
	 * 加载主题 CSS
	 */
	private async loadThemeCSS(): Promise<string> {
		try {
			const response = await fetch(this.config.themeCssPath);
			if (!response.ok) {
				throw new Error(`Failed to fetch theme CSS: ${response.status}`);
			}
			return await response.text();
		} catch (error) {
			// 如果加载失败，返回内联 CSS
			console.warn('Using inline theme CSS as fallback');
			return this.getInlineThemeCSS();
		}
	}

	/**
	 * 获取内联主题 CSS（降级方案）
	 */
	private getInlineThemeCSS(): string {
		return `
			/* 内联降级主题 CSS */
			:root {
				--roco-charcoal-sidebar: #1a1a1a;
				--roco-parchment-bg: #f5f0e6;
				--roco-warm-gold: #d4a017;
				--roco-cream-surface: #fefdf8;
				--roco-text-primary: #2c2416;
				--roco-border-warm: #c4a882;
			}
			
			aside, .sidebar {
				background-color: var(--roco-charcoal-sidebar) !important;
			}
			
			main, .chat-container {
				background-color: var(--roco-parchment-bg) !important;
				color: var(--roco-text-primary) !important;
			}
		`;
	}

	/**
	 * 移除主题注入
	 */
	remove(): void {
		const existingStyle = document.getElementById(this.styleElementId);
		if (existingStyle) {
			existingStyle.remove();
		}

		const existingFont = document.getElementById(this.fontLinkId);
		if (existingFont) {
			existingFont.remove();
		}
	}

	/**
	 * 检查主题是否已注入
	 */
	isInjected(): boolean {
		return document.getElementById(this.styleElementId) !== null;
	}
}

/**
 * 创建主题注入器
 */
export function createThemeInjector(config?: Partial<ThemeInjectorConfig>): ThemeInjector {
	return new ThemeInjector(config);
}

/**
 * 自动注入主题（页面加载时调用）
 */
export function autoInjectTheme(): void {
	if (typeof window !== 'undefined') {
		const injector = createThemeInjector({ autoInject: true });
		injector.inject();
	}
}
