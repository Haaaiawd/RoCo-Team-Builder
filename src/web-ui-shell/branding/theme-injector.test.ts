/**
 * ThemeInjector 集成测试
 * 
 * 验证主题注入、字体加载和主题移除
 */

import {
	ThemeInjector,
	createThemeInjector,
	DEFAULT_FONTS,
	autoInjectTheme,
} from './theme-injector';

// 测试函数（需要配置测试框架后才能运行）
export function runThemeInjectorTests() {
	console.log('Testing theme injector...');

	// 测试默认字体配置
	console.log('Default fonts:', DEFAULT_FONTS);
	if (DEFAULT_FONTS.length === 0) {
		throw new Error('Default fonts should not be empty');
	}
	if (!DEFAULT_FONTS.some(f => f.name === 'Crimson Pro')) {
		throw new Error('Default fonts should include Crimson Pro');
	}
	if (!DEFAULT_FONTS.some(f => f.name === 'Patrick Hand')) {
		throw new Error('Default fonts should include Patrick Hand');
	}

	// 创建注入器
	const injector = createThemeInjector({
		themeCssPath: '/static/web-ui-shell/branding/theme-override.css',
	});
	console.log('Theme injector created');

	// 测试注入前状态
	const isInjectedBefore = injector.isInjected();
	console.log('Is injected before:', isInjectedBefore);
	// 在测试环境中可能为 false

	// 测试注入（在浏览器环境中）
	if (typeof window !== 'undefined') {
		injector.inject();
		console.log('Theme injected');

		const isInjectedAfter = injector.isInjected();
		console.log('Is injected after:', isInjectedAfter);
		if (!isInjectedAfter) {
			throw new Error('Theme should be injected after calling inject()');
		}

		// 测试移除
		injector.remove();
		console.log('Theme removed');

		const isInjectedAfterRemove = injector.isInjected();
		console.log('Is injected after remove:', isInjectedAfterRemove);
		if (isInjectedAfterRemove) {
			throw new Error('Theme should be removed after calling remove()');
		}
	} else {
		console.log('Skipping injection test (not in browser environment)');
	}

	// 测试内联 CSS 降级
	const inlineCSS = (injector as any).getInlineThemeCSS();
	console.log('Inline CSS length:', inlineCSS.length);
	if (!inlineCSS.includes('--roco-charcoal-sidebar')) {
		throw new Error('Inline CSS should include CSS variables');
	}
	if (!inlineCSS.includes('--roco-parchment-bg')) {
		throw new Error('Inline CSS should include parchment background');
	}

	console.log('All theme injector tests passed!');
}
