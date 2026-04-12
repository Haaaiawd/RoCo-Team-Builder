/**
 * Visible Feature Policy E2E Tests
 * 
 * 白名单回归测试
 * 
 * 测试覆盖：
 * - 白名单快照比对
 * - 入口暴露检测
 * - UI 回归检查
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §11.3 UI 回归测试
 */

import { test, expect } from '@playwright/test';

/**
 * 白名单回归测试
 */
test.describe('白名单回归测试', () => {
	test('终端用户首页不出现禁止入口', async ({ page }) => {
		await page.goto('/');
		
		// 验证禁止入口不可见
		const forbiddenEntries = [
			'[data-testid="notes-entry"]',
			'[data-testid="channels-entry"]',
			'[data-testid="knowledge-entry"]',
			'[data-testid="admin-entry"]',
			'[data-testid="terminal-entry"]',
			'[data-testid="workspaces-entry"]',
			'[data-testid="prompts-entry"]',
			'[data-testid="documents-entry"]',
		];
		
		for (const selector of forbiddenEntries) {
			await expect(page.locator(selector)).not.toBeVisible();
		}
	});
	
	test('侧边栏、顶部栏、空状态页、设置面板都满足白名单约束', async ({ page }) => {
		await page.goto('/');
		
		// 检查侧边栏
		const sidebar = page.locator('aside');
		await expect(sidebar).toBeVisible();
		
		// 检查侧边栏导航项
		const sidebarItems = await page.locator('[data-testid="sidebar-item"]').all();
		for (const item of sidebarItems) {
			const text = await item.textContent();
			expect(text).not.toMatch(/notes|channels|knowledge|admin|terminal/i);
		}
		
		// 检查设置面板
		await page.click('[data-testid="settings-entry"]');
		await page.waitForSelector('[data-testid="settings-panel"]');
		
		// 验证设置面板不包含禁止入口
		const settingsPanel = page.locator('[data-testid="settings-panel"]');
		const settingsText = await settingsPanel.textContent();
		expect(settingsText).not.toMatch(/notes|channels|knowledge/i);
	});
	
	test('管理员登录时必要后台能力仍可访问', async ({ page }) => {
		// 模拟管理员登录
		await page.goto('/login');
		await page.fill('[data-testid="username"]', 'admin');
		await page.fill('[data-testid="password"]', 'admin');
		await page.click('[data-testid="login-button"]');
		
		// 验证管理员可以访问 Admin 入口
		await page.goto('/admin');
		await expect(page.locator('[data-testid="admin-panel"]')).toBeVisible();
	});
	
	test('VisibleFeaturePolicy 导出快照与基线一致', async ({ page }) => {
		await page.goto('/');
		
		// 获取当前快照
		const currentSnapshot = await page.evaluate(() => {
			// 这里需要调用 VisibleFeaturePolicy.exportSnapshot()
			// 由于这是前端代码，需要通过 window 对象暴露
			// @ts-ignore
			return window.rocoPolicy?.exportSnapshot();
		});
		
		// 加载基线
		const baselineSnapshot = {
			expected_visible_entries: ['chat', 'settings', 'models', 'connections'],
			expected_hidden_entries: ['notes', 'channels', 'knowledge', 'admin', 'terminal'],
		};
		
		// 验证快照与基线一致
		expect(currentSnapshot).toBeDefined();
		expect(currentSnapshot.expected_visible_entries).toEqual(
			baselineSnapshot.expected_visible_entries
		);
		expect(currentSnapshot.expected_hidden_entries).toEqual(
			baselineSnapshot.expected_hidden_entries
		);
	});
	
	test('检测新增暴露入口并判定回归未通过', async ({ page }) => {
		await page.goto('/');
		
		// 获取当前可见入口
		const visibleEntries = await page.locator('[data-testid="sidebar-item"]').all();
		const visibleTexts = await Promise.all(
			visibleEntries.map(item => item.textContent())
		);
		
		// 基线中的允许入口
		const allowedEntries = ['chat', 'settings', 'models', 'connections'];
		
		// 检查是否有新增暴露入口
		const unexpectedEntries = visibleTexts.filter(text => {
			const lowerText = text?.toLowerCase() || '';
			return !allowedEntries.some(allowed => lowerText.includes(allowed));
		});
		
		// 如果有新增入口，判定回归失败
		expect(unexpectedEntries.length).toBe(0);
	});
});

/**
 * UI 回归测试
 */
test.describe('UI 回归测试', () => {
	test('炭黑侧栏、撕纸边缘、羊皮纸纹理、暖金高亮保持一致', async ({ page }) => {
		await page.goto('/');
		
		// 验证侧栏颜色
		const sidebarColor = await page.locator('aside').evaluate(el => {
			return window.getComputedStyle(el).backgroundColor;
		});
		expect(sidebarColor).toBe('rgb(26, 26, 26)'); // 炭黑
		
		// 验证主区背景
		const mainColor = await page.locator('main').evaluate(el => {
			return window.getComputedStyle(el).backgroundColor;
		});
		expect(mainColor).toBe('rgb(245, 240, 230)'); // 羊皮纸
		
		// 验证暖金高亮
		const button = await page.locator('button').first();
		const buttonColor = await button.evaluate(el => {
			return window.getComputedStyle(el).backgroundColor;
		});
		expect(buttonColor).toMatch(/rgb\((212|232).*/); // 暖金
	});
	
	test('标签式 History 项与胶囊输入框保持一致', async ({ page }) => {
		await page.goto('/');
		
		// 验证 History 项样式
		const historyItem = await page.locator('[data-testid="history-item"]').first();
		await expect(historyItem).toHaveCSS('border-style', 'solid');
		await expect(historyItem).toHaveCSS('border-width', '1px');
		
		// 验证输入框胶囊形状
		const inputContainer = await page.locator('[data-testid="input-container"]');
		const borderRadius = await inputContainer.evaluate(el => {
			return window.getComputedStyle(el).borderRadius;
		});
		expect(borderRadius).toMatch(/9999px|50px/); // 胶囊形
	});
	
	test('Agent 文本、用户气泡、工具卡片保持手账记录一致气质', async ({ page }) => {
		await page.goto('/chat');
		
		// 发送消息生成对话
		await page.fill('[data-testid="chat-input"]', 'Hello');
		await page.click('[data-testid="send-button"]');
		
		// 验证用户气泡样式
		const userBubble = await page.locator('[data-testid="message-user"]').first();
		await expect(userBubble).toHaveCSS('transform', /rotate/); // 纸贴片旋转效果
		
		// 验证 Agent 消息样式
		const agentMessage = await page.locator('[data-testid="message-assistant"]').first();
		const fontFamily = await agentMessage.evaluate(el => {
			return window.getComputedStyle(el).fontFamily;
		});
		expect(fontFamily).toMatch(/Crimson Pro|Georgia|serif/i); // 手写风格字体
	});
	
	test('桌面端与移动端都保持同源视觉语言', async ({ page }) => {
		// 桌面端测试
		await page.setViewportSize({ width: 1920, height: 1080 });
		await page.goto('/');
		
		const desktopSidebarColor = await page.locator('aside').evaluate(el => {
			return window.getComputedStyle(el).backgroundColor;
		});
		
		// 移动端测试
		await page.setViewportSize({ width: 375, height: 667 });
		await page.goto('/');
		
		const mobileSidebarColor = await page.locator('aside').evaluate(el => {
			return window.getComputedStyle(el).backgroundColor;
		});
		
		// 验证视觉语言一致
		expect(desktopSidebarColor).toBe(mobileSidebarColor);
	});
});
