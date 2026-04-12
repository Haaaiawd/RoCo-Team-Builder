/**
 * ThemeOverrideConfig - 产品视觉主题配置
 * 
 * 定义"复古冒险者手账风"的 CSS Variables、DOM 锚点和样式覆写策略。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §7.2 Visual Language & Theme Override Strategy
 * 参考：asserts/ui-style.png 视觉设计稿
 */

/**
 * 主题配置常量
 */
export const THEME_CONFIG = {
	// 主色结构
	colors: {
		// 炭黑侧栏
		charcoal_sidebar: '#1a1a1a',
		charcoal_sidebar_light: '#2a2a2a',
		
		// 羊皮纸主聊天区
		parchment_bg: '#f5f0e6',
		parchment_light: '#faf8f3',
		parchment_dark: '#e8e0d0',
		
		// 暖金强调色
		warm_gold: '#d4a017',
		warm_gold_light: '#e8c055',
		warm_gold_dark: '#b8860b',
		
		// 奶白表面层
		cream_surface: '#fefdf8',
		cream_surface_alt: '#f9f7f2',
		
		// 文本颜色
		text_primary: '#2c2416',
		text_secondary: '#5c4a32',
		text_muted: '#8b7355',
		
		// 边框颜色
		border_warm: '#c4a882',
		border_gold: '#d4a017',
	},
	
	// 纹理配置
	textures: {
		// 地图线稿纹理（5%-10% 透明度）
		map_pattern: 'url(/static/texture-map-pattern.svg)',
		// 山脉纹理
		mountain_pattern: 'url(/static/texture-mountain-pattern.svg)',
		// 齿轮纹理
		gear_pattern: 'url(/static/texture-gear-pattern.svg)',
		texture_opacity: 0.08,
		blend_mode: 'multiply',
	},
	
	// 版式配置
	typography: {
		// 主字体
		font_family_primary: '"Crimson Pro", "Georgia", serif',
		// UI 字体
		font_family_ui: '"Lato", "Helvetica Neue", sans-serif',
		// 手写字体（用于特殊强调）
		font_family_hand: '"Patrick Hand", cursive',
		
		// 字体大小
		font_size_base: '16px',
		font_size_sm: '14px',
		font_size_lg: '18px',
		font_size_xl: '24px',
		
		// 行高
		line_height_tight: 1.3,
		line_height_normal: 1.6,
		line_height_relaxed: 1.8,
	},
	
	// 间距配置
	spacing: {
		xs: '4px',
		sm: '8px',
		md: '16px',
		lg: '24px',
		xl: '32px',
		xxl: '48px',
	},
	
	// 圆角配置
	borderRadius: {
		sm: '4px',
		md: '8px',
		lg: '12px',
		xl: '16px',
		pill: '9999px', // 胶囊形
	},
	
	// 阴影配置
	shadows: {
		// 纸贴片阴影
		paper: '0 2px 4px rgba(44, 36, 22, 0.1), 0 1px 2px rgba(44, 36, 22, 0.06)',
		// 浮起阴影
		floating: '0 8px 16px rgba(44, 36, 22, 0.12), 0 4px 8px rgba(44, 36, 22, 0.08)',
		// 内阴影
		inset: 'inset 0 2px 4px rgba(44, 36, 22, 0.06)',
	},
	
	// 动画配置
	animations: {
		duration_fast: '150ms',
		duration_normal: '300ms',
		duration_slow: '500ms',
		easing_ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
		easing_bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
	},
};

/**
 * DOM 选择器映射
 * 用于精确定位 Open WebUI 的语义容器和组件
 */
export const DOM_SELECTOR_MAP = {
	// 语义容器
	aside: 'aside', // 侧栏
	main: 'main', // 主聊天区
	form: 'form', // 输入表单
	textarea: 'textarea', // 输入框
	iframe: 'iframe', // Rich UI 宿主
	
	// Open WebUI 特定类名（可能需要根据实际情况调整）
	sidebar: '.sidebar',
	sidebar_item: '.sidebar-item',
	chat_container: '.chat-container',
	message_bubble: '.message-bubble',
	input_container: '.input-container',
	button: 'button',
	history_item: '.history-item',
	
	// 特定组件
	model_selector: '.model-selector',
	settings_panel: '.settings-panel',
	tool_card: '.tool-card',
	rich_ui_host: '.rich-ui-host',
};

/**
 * CSS Variables 生成器
 * 生成用于注入到 :root 的 CSS 变量
 */
export function generateCSSVariables(): string {
	const { colors, textures, typography, spacing, borderRadius, shadows, animations } = THEME_CONFIG;
	
	return `
	:root {
		/* 主色结构 */
		--roco-charcoal-sidebar: ${colors.charcoal_sidebar};
		--roco-charcoal-sidebar-light: ${colors.charcoal_sidebar_light};
		--roco-parchment-bg: ${colors.parchment_bg};
		--roco-parchment-light: ${colors.parchment_light};
		--roco-parchment-dark: ${colors.parchment_dark};
		--roco-warm-gold: ${colors.warm_gold};
		--roco-warm-gold-light: ${colors.warm_gold_light};
		--roco-warm-gold-dark: ${colors.warm_gold_dark};
		--roco-cream-surface: ${colors.cream_surface};
		--roco-cream-surface-alt: ${colors.cream_surface_alt};
		
		/* 文本颜色 */
		--roco-text-primary: ${colors.text_primary};
		--roco-text-secondary: ${colors.text_secondary};
		--roco-text-muted: ${colors.text_muted};
		
		/* 边框颜色 */
		--roco-border-warm: ${colors.border_warm};
		--roco-border-gold: ${colors.border_gold};
		
		/* 字体 */
		--roco-font-family-primary: ${typography.font_family_primary};
		--roco-font-family-ui: ${typography.font_family_ui};
		--roco-font-family-hand: ${typography.font_family_hand};
		--roco-font-size-base: ${typography.font_size_base};
		--roco-font-size-sm: ${typography.font_size_sm};
		--roco-font-size-lg: ${typography.font_size_lg};
		--roco-font-size-xl: ${typography.font_size_xl};
		--roco-line-height-tight: ${typography.line_height_tight};
		--roco-line-height-normal: ${typography.line_height_normal};
		--roco-line-height-relaxed: ${typography.line_height_relaxed};
		
		/* 间距 */
		--roco-spacing-xs: ${spacing.xs};
		--roco-spacing-sm: ${spacing.sm};
		--roco-spacing-md: ${spacing.md};
		--roco-spacing-lg: ${spacing.lg};
		--roco-spacing-xl: ${spacing.xl};
		--roco-spacing-xxl: ${spacing.xxl};
		
		/* 圆角 */
		--roco-border-radius-sm: ${borderRadius.sm};
		--roco-border-radius-md: ${borderRadius.md};
		--roco-border-radius-lg: ${borderRadius.lg};
		--roco-border-radius-xl: ${borderRadius.xl};
		--roco-border-radius-pill: ${borderRadius.pill};
		
		/* 阴影 */
		--roco-shadow-paper: ${shadows.paper};
		--roco-shadow-floating: ${shadows.floating};
		--roco-shadow-inset: ${shadows.inset};
		
		/* 动画 */
		--roco-duration-fast: ${animations.duration_fast};
		--roco-duration-normal: ${animations.duration_normal};
		--roco-duration-slow: ${animations.duration_slow};
		--roco-easing-ease: ${animations.easing_ease};
		--roco-easing-bounce: ${animations.easing_bounce};
	}
	`;
}

/**
 * 生成自定义 CSS 覆写
 * 用于强制覆写 Open WebUI 的默认样式
 */
export function generateCustomCSS(): string {
	return `
	/* 侧栏：炭黑背景 + 撕纸边缘 */
	${DOM_SELECTOR_MAP.aside}, ${DOM_SELECTOR_MAP.sidebar} {
		background-color: var(--roco-charcoal-sidebar) !important;
		border-right: none !important;
		/* 撕纸边缘效果将通过 CSS ::before 伪元素实现 */
	}
	
	${DOM_SELECTOR_MAP.aside}::before,
	${DOM_SELECTOR_MAP.sidebar}::before {
		content: '';
		position: absolute;
		top: 0;
		right: 0;
		bottom: 0;
		width: 8px;
		background: linear-gradient(
			to right,
			transparent 0%,
			rgba(26, 26, 26, 0.8) 50%,
			transparent 100%
		);
		/* 撕纸边缘纹理 */
		mask-image: url(/static/tear-edge-pattern.svg);
		mask-size: 100% 100%;
		pointer-events: none;
	}
	
	/* 主聊天区：羊皮纸背景 + 地图纹理 */
	${DOM_SELECTOR_MAP.main}, ${DOM_SELECTOR_MAP.chat_container} {
		background-color: var(--roco-parchment-bg) !important;
		background-image: ${THEME_CONFIG.textures.map_pattern} !important;
		background-blend-mode: ${THEME_CONFIG.textures.blend_mode} !important;
		background-size: 256px 256px !important;
		background-repeat: repeat !important;
		color: var(--roco-text-primary) !important;
		font-family: var(--roco-font-family-primary) !important;
	}
	
	/* 用户气泡：纸贴片效果 */
	.message-bubble.user,
	${DOM_SELECTOR_MAP.message_bubble}.user {
		background-color: var(--roco-cream-surface) !important;
		border-radius: var(--roco-border-radius-md) var(--roco-border-radius-lg) 
		                   var(--roco-border-radius-lg) var(--roco-border-radius-sm) !important;
		box-shadow: var(--roco-shadow-paper) !important;
		border: 1px solid var(--roco-border-warm) !important;
		transform: rotate(-1deg) !important;
		transition: transform var(--roco-duration-fast) var(--roco-easing-ease) !important;
	}
	
	.message-bubble.user:hover,
	${DOM_SELECTOR_MAP.message_bubble}.user:hover {
		transform: rotate(0deg) translateY(-2px) !important;
		box-shadow: var(--roco-shadow-floating) !important;
	}
	
	/* Agent 消息：手写风格 */
	.message-bubble.assistant,
	${DOM_SELECTOR_MAP.message_bubble}.assistant {
		background-color: transparent !important;
		color: var(--roco-text-primary) !important;
		font-family: var(--roco-font-family-primary) !important;
		line-height: var(--roco-line-height-relaxed) !important;
		border: none !important;
		box-shadow: none !important;
	}
	
	/* 输入区：胶囊形工具条 */
	${DOM_SELECTOR_MAP.form}, ${DOM_SELECTOR_MAP.input_container} {
		background-color: var(--roco-cream-surface-alt) !important;
		border-radius: var(--roco-border-radius-pill) !important;
		border: 2px solid var(--roco-border-warm) !important;
		box-shadow: var(--roco-shadow-paper) !important;
	}
	
	${DOM_SELECTOR_MAP.textarea} {
		background-color: transparent !important;
		border: none !important;
		font-family: var(--roco-font-family-ui) !important;
		font-size: var(--roco-font-size-base) !important;
		color: var(--roco-text-primary) !important;
		resize: none !important;
	}
	
	${DOM_SELECTOR_MAP.textarea}::placeholder {
		color: var(--roco-text-muted) !important;
		font-style: italic !important;
	}
	
	/* History 项：手账标签风格 */
	${DOM_SELECTOR_MAP.history_item} {
		background-color: var(--roco-parchment-light) !important;
		border: 1px solid var(--roco-border-warm) !important;
		border-radius: var(--roco-border-radius-sm) !important;
		padding: var(--roco-spacing-sm) var(--roco-spacing-md) !important;
		margin-bottom: var(--roco-spacing-sm) !important;
		font-family: var(--roco-font-family-ui) !important;
		font-size: var(--roco-font-size-sm) !important;
		color: var(--roco-text-secondary) !important;
		transition: all var(--roco-duration-fast) var(--roco-easing-ease) !important;
	}
	
	${DOM_SELECTOR_MAP.history_item}:hover {
		background-color: var(--roco-warm-gold) !important;
		color: var(--roco-text-primary) !important;
		border-color: var(--roco-border-gold) !important;
		transform: translateX(4px) !important;
	}
	
	${DOM_SELECTOR_MAP.history_item}.active {
		background-color: var(--roco-warm-gold) !important;
		border-color: var(--roco-border-gold) !important;
		border-style: dashed !important;
	}
	
	/* 按钮：手账标签感 */
	${DOM_SELECTOR_MAP.button} {
		background-color: var(--roco-warm-gold) !important;
		color: var(--roco-text-primary) !important;
		border: 1px solid var(--roco-border-gold) !important;
		border-radius: var(--roco-border-radius-md) !important;
		font-family: var(--roco-font-family-ui) !important;
		font-weight: 600 !important;
		padding: var(--roco-spacing-sm) var(--roco-spacing-lg) !important;
		transition: all var(--roco-duration-fast) var(--roco-easing-ease) !important;
	}
	
	${DOM_SELECTOR_MAP.button}:hover {
		background-color: var(--roco-warm-gold-light) !important;
		transform: translateY(-1px) !important;
		box-shadow: var(--roco-shadow-paper) !important;
	}
	
	${DOM_SELECTOR_MAP.button}:active {
		transform: translateY(0) !important;
	}
	
	/* 工具卡片：手账标签风格 */
	${DOM_SELECTOR_MAP.tool_card} {
		background-color: var(--roco-cream-surface) !important;
		border: 1px solid var(--roco-border-warm) !important;
		border-radius: var(--roco-border-radius-md) !important;
		padding: var(--roco-spacing-md) !important;
		margin: var(--roco-spacing-md) 0 !important;
		box-shadow: var(--roco-shadow-paper) !important;
	}
	
	/* Rich UI 宿主：iframe 沙箱 */
	${DOM_SELECTOR_MAP.iframe}, ${DOM_SELECTOR_MAP.rich_ui_host} {
		border: 1px solid var(--roco-border-warm) !important;
		border-radius: var(--roco-border-radius-md) !important;
		background-color: var(--roco-cream-surface) !important;
	}
	
	/* 模型选择器 */
	${DOM_SELECTOR_MAP.model_selector} {
		background-color: var(--roco-cream-surface) !important;
		border: 1px solid var(--roco-border-warm) !important;
		border-radius: var(--roco-border-radius-md) !important;
		color: var(--roco-text-primary) !important;
	}
	
	/* 设置面板 */
	${DOM_SELECTOR_MAP.settings_panel} {
		background-color: var(--roco-parchment-light) !important;
		border: 1px solid var(--roco-border-warm) !important;
		border-radius: var(--roco-border-radius-lg) !important;
	}
	`;
}

/**
 * 主题注入器
 * 将 CSS Variables 和自定义样式注入到页面
 */
export class ThemeInjector {
	private styleElementId = 'roco-theme-override';
	
	/**
	 * 注入主题到页面
	 */
	inject(): void {
		// 移除旧的主题样式
		const existing = document.getElementById(this.styleElementId);
		if (existing) {
			existing.remove();
		}
		
		// 创建新的样式元素
		const style = document.createElement('style');
		style.id = this.styleElementId;
		
		// 组合 CSS Variables 和自定义样式
		const cssContent = generateCSSVariables() + generateCustomCSS();
		style.textContent = cssContent;
		
		// 插入到 head
		document.head.appendChild(style);
	}
	
	/**
	 * 移除主题注入
	 */
	remove(): void {
		const existing = document.getElementById(this.styleElementId);
		if (existing) {
			existing.remove();
		}
	}
}

/**
 * 创建主题注入器实例
 */
export function createThemeInjector(): ThemeInjector {
	return new ThemeInjector();
}
