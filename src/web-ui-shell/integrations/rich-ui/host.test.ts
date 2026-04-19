/**
 * RichUiHost 集成测试
 * 
 * 验证 Rich UI 宿主渲染、iframe 沙箱和降级文本
 */

import {
	generateRichUiHost,
	generateRichUiHostCSS,
	createRichUiHostManager,
} from './host';

// 测试函数（需要配置测试框架后才能运行）
export function runRichUiHostTests() {
	console.log('Testing Rich UI host...');

	// 测试直接嵌入模式
	const directConfig = {
		html: '<div class="spirit-card">Fire God</div>',
		fallback_text: 'Fire God - Fire Type',
		use_iframe: false,
	};
	const directHost = generateRichUiHost(directConfig);
	console.log('Direct embed host rendered:', directHost);
	if (!directHost.includes('spirit-card')) {
		throw new Error('Direct embed host should include HTML content');
	}
	if (!directHost.includes('roco-rich-ui-content')) {
		throw new Error('Direct embed host should have content container');
	}

	// 测试 iframe 沙箱模式
	const iframeConfig = {
		html: '<div class="spirit-card">Fire God</div>',
		fallback_text: 'Fire God - Fire Type',
		use_iframe: true,
		sandbox: 'allow-scripts allow-same-origin',
	};
	const iframeHost = generateRichUiHost(iframeConfig);
	console.log('Iframe host rendered:', iframeHost);
	if (!iframeHost.includes('iframe')) {
		throw new Error('Iframe host should include iframe element');
	}
	if (!iframeHost.includes('allow-scripts')) {
		throw new Error('Iframe host should have sandbox attributes');
	}

	// 测试降级文本
	const fallbackConfig = {
		html: '<div class="spirit-card">Fire God</div>',
		fallback_text: 'Fire God - Fire Type',
	};
	const fallbackHost = generateRichUiHost(fallbackConfig);
	console.log('Fallback host rendered:', fallbackHost);
	if (!fallbackHost.includes('Fire God - Fire Type')) {
		throw new Error('Fallback text should be included in noscript');
	}

	// 测试 CSS 生成
	const css = generateRichUiHostCSS();
	console.log('CSS generated:', css);
	if (!css.includes('roco-rich-ui-host')) {
		throw new Error('CSS should include host styles');
	}
	if (!css.includes('--roco-cream-surface')) {
		throw new Error('CSS should include cream surface color');
	}
	if (!css.includes('--roco-border-warm')) {
		throw new Error('CSS should include warm border color');
	}

	// 测试宿主管理器
	const manager = createRichUiHostManager({
		html: '<div class="spirit-card">Fire God</div>',
		fallback_text: 'Fire God - Fire Type',
	});
	const rendered = manager.render();
	console.log('Manager rendered:', rendered);
	if (!rendered.includes('spirit-card')) {
		throw new Error('Manager should render host correctly');
	}

	const fallback = manager.renderFallback();
	console.log('Manager fallback:', fallback);
	if (!fallback.includes('Fire God - Fire Type')) {
		throw new Error('Manager should render fallback text');
	}

	// 测试配置更新
	manager.updateConfig({ html: '<div class="spirit-card">Ice Dragon</div>' });
	const updated = manager.render();
	console.log('Updated manager rendered:', updated);
	if (!updated.includes('Ice Dragon')) {
		throw new Error('Manager should update config correctly');
	}

	// 测试 iframe 能力检查
	const canUseIframe = manager.canUseIframe();
	console.log('Can use iframe:', canUseIframe);
	// 在浏览器环境中应该返回 true，在 Node.js 环境中可能返回 false

	console.log('All Rich UI host tests passed!');
}
