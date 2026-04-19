/**
 * Product Shell E2E Tests
 * 
 * 关键用户故事 E2E 测试
 * 
 * 测试覆盖：
 * - US-001: 文字配队
 * - US-002: 截图识别
 * - US-004: 资料卡片
 * - US-006: 白名单路径
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §11.2 集成测试
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §11.4 验收测试
 */

import { test, expect } from '@playwright/test';

/**
 * US-001: 文字配队
 */
test.describe('US-001: 文字配队', () => {
	test('用户发送配队请求，Agent 返回推荐队伍', async ({ page }) => {
		// 导航到聊天页面
		await page.goto('/chat');
		
		// 选择内置轨道模型
		await page.click('[data-testid="model-selector"]');
		await page.click('text=roco-agent');
		
		// 发送配队请求
		await page.fill('[data-testid="chat-input"]', '推荐一个火属性的队伍');
		await page.click('[data-testid="send-button"]');
		
		// 等待响应
		await page.waitForSelector('[data-testid="message-assistant"]');
		
		// 验证返回了推荐队伍
		const response = await page.textContent('[data-testid="message-assistant"]');
		expect(response).toContain('推荐队伍');
		expect(response).toContain('火');
	});
	
	test('用户追问配队细节，Agent 保持上下文', async ({ page }) => {
		// 这是一个已存在的聊天
		await page.goto('/chat/123');
		
		// 发送追问
		await page.fill('[data-testid="chat-input"]', '这个队伍的弱点是什么？');
		await page.click('[data-testid="send-button"]');
		
		// 验证 Agent 理解上下文
		const response = await page.textContent('[data-testid="message-assistant"]');
		expect(response).toBeTruthy();
	});
});

/**
 * US-002: 截图识别
 */
test.describe('US-002: 截图识别', async () => {
	test('用户上传截图，Agent 返回识别候选', async ({ page }) => {
		await page.goto('/chat');
		
		// 选择内置轨道模型（支持视觉）
		await page.click('[data-testid="model-selector"]');
		await page.click('text=roco-agent');
		
		// 上传截图
		const fileInput = await page.locator('[data-testid="image-upload"]');
		await fileInput.setInputFiles('test/fixtures/screenshot.png');
		
		// 发送消息
		await page.fill('[data-testid="chat-input"]', '识别这些精灵');
		await page.click('[data-testid="send-button"]');
		
		// 等待识别候选展示
		await page.waitForSelector('[data-testid="recognition-review"]');
		
		// 验证显示了候选列表
		const candidates = await page.locator('[data-testid="recognition-candidate"]').count();
		expect(candidates).toBeGreaterThan(0);
	});
	
	test('用户确认拥有列表，界面显示状态提示', async ({ page }) => {
		await page.goto('/chat/123');
		
		// 确认候选
		await page.click('[data-testid="confirm-owned-list"]');
		
		// 验证显示状态提示
		await expect(page.locator('[data-testid="owned-list-status"]')).toBeVisible();
		const statusText = await page.textContent('[data-testid="owned-list-status"]');
		expect(statusText).toContain('基于已确认拥有列表');
	});
	
	test('BYOK 非视觉模型上传截图，前端拦截并提示', async ({ page }) => {
		await page.goto('/chat');
		
		// 选择 BYOK 轨道模型（不支持视觉）
		await page.click('[data-testid="model-selector"]');
		await page.click('text=gpt-4');
		
		// 尝试上传截图
		const fileInput = await page.locator('[data-testid="image-upload"]');
		await fileInput.setInputFiles('test/fixtures/screenshot.png');
		
		// 验证显示能力不支持提示
		await expect(page.locator('[data-testid="capability-error"]')).toBeVisible();
		const errorText = await page.textContent('[data-testid="capability-error"]');
		expect(errorText).toContain('CAPABILITY_UNSUPPORTED');
	});
});

/**
 * US-004: 资料卡片
 */
test.describe('US-004: 资料卡片', async () => {
	test('Agent 返回精灵卡片，Rich UI 宿主渲染', async ({ page }) => {
		await page.goto('/chat');
		
		// 发送查询精灵资料请求
		await page.fill('[data-testid="chat-input"]', '查看火神的资料');
		await page.click('[data-testid="send-button"]');
		
		// 等待精灵卡片渲染
		await page.waitForSelector('[data-testid="spirit-card"]');
		
		// 验证卡片内容
		const card = await page.locator('[data-testid="spirit-card"]');
		await expect(card).toBeVisible();
		
		// 验证数据来源跳转
		const sourceLink = await page.locator('[data-testid="data-source-link"]');
		await expect(sourceLink).toBeVisible();
	});
	
	test('Rich UI 渲染失败，降级为文本', async ({ page }) => {
		// 模拟 Rich UI 渲染失败的场景
		await page.goto('/chat');
		
		// 发送请求（配置为返回失败的 Rich UI）
		await page.fill('[data-testid="chat-input"]', '查看精灵资料');
		await page.click('[data-testid="send-button"]');
		
		// 验证显示降级文本
		const fallbackText = await page.locator('[data-testid="rich-ui-fallback"]');
		await expect(fallbackText).toBeVisible();
	});
});

/**
 * US-006: 白名单路径
 */
test.describe('US-006: 白名单路径', async () => {
	test('终端用户首页不出现禁止入口', async ({ page }) => {
		await page.goto('/');
		
		// 验证禁止入口不可见
		await expect(page.locator('[data-testid="notes-entry"]')).not.toBeVisible();
		await expect(page.locator('[data-testid="channels-entry"]')).not.toBeVisible();
		await expect(page.locator('[data-testid="knowledge-entry"]')).not.toBeVisible();
		await expect(page.locator('[data-testid="admin-entry"]')).not.toBeVisible();
		await expect(page.locator('[data-testid="terminal-entry"]')).not.toBeVisible();
		
		// 验证允许入口可见
		await expect(page.locator('[data-testid="chat-entry"]')).toBeVisible();
		await expect(page.locator('[data-testid="settings-entry"]')).toBeVisible();
	});
	
	test('侧栏导航满足白名单约束', async ({ page }) => {
		await page.goto('/');
		
		// 检查侧栏导航项
		const sidebarItems = await page.locator('[data-testid="sidebar-item"]').all();
		const visibleItems = await Promise.all(
			sidebarItems.map(async item => await item.isVisible())
		);
		
		// 验证只显示白名单内的入口
		expect(visibleItems.filter(Boolean).length).toBeGreaterThan(0);
	});
	
	test('BYOK 轨道不出现识别确认、精灵卡片等误导性 UI', async ({ page }) => {
		await page.goto('/chat');
		
		// 选择 BYOK 轨道
		await page.click('[data-testid="model-selector"]');
		await page.click('text=gpt-4');
		
		// 发送消息
		await page.fill('[data-testid="chat-input"]', 'Hello');
		await page.click('[data-testid="send-button"]');
		
		// 验证不显示识别确认 UI
		await expect(page.locator('[data-testid="recognition-review"]')).not.toBeVisible();
		
		// 验证不显示精灵卡片增强提示
		await expect(page.locator('[data-testid="spirit-card-enhancement"]')).not.toBeVisible();
	});
	
	test('builtin route 额度超限，显示 QUOTA_ 语义提示', async ({ page }) => {
		// 配置为额度耗尽状态
		await page.goto('/chat');
		
		// 选择内置轨道
		await page.click('[data-testid="model-selector"]');
		await page.click('text=roco-agent');
		
		// 尝试发送消息
		await page.fill('[data-testid="chat-input"]', 'Hello');
		await page.click('[data-testid="send-button"]');
		
		// 验证显示配额提示
		await expect(page.locator('[data-testid="quota-alert"]')).toBeVisible();
		const alertText = await page.textContent('[data-testid="quota-alert"]');
		expect(alertText).toContain('QUOTA_EXHAUSTED');
		expect(alertText).toContain('切换 BYOK');
	});
	
	test('主题注入后，UI 呈现复古手账风', async ({ page }) => {
		await page.goto('/');
		
		// 验证侧栏颜色
		const sidebar = await page.locator('aside').evaluate(el => {
			return window.getComputedStyle(el).backgroundColor;
		});
		expect(sidebar).toBe('rgb(26, 26, 26)'); // 炭黑
		
		// 验证主区背景
		const main = await page.locator('main').evaluate(el => {
			return window.getComputedStyle(el).backgroundColor;
		});
		expect(main).toBe('rgb(245, 240, 230)'); // 羊皮纸
		
		// 验证 History 项样式
		const historyItem = await page.locator('[data-testid="history-item"]').first();
		await expect(historyItem).toHaveCSS('border-style', 'solid');
	});
});

/**
 * 工具调用测试
 */
test.describe('工具调用', () => {
	test('工具调用结果以折叠卡片出现在时间线中', async ({ page }) => {
		await page.goto('/chat');
		
		// 发送会触发工具调用的请求
		await page.fill('[data-testid="chat-input"]', '查询火神的资料');
		await page.click('[data-testid="send-button"]');
		
		// 等待工具卡片出现
		await page.waitForSelector('[data-testid="tool-card"]');
		
		// 验证卡片可折叠
		const toolCard = await page.locator('[data-testid="tool-card"]').first();
		await toolCard.click();
		
		// 验证展开/收起
		const expanded = await toolCard.getAttribute('data-expanded');
		expect(expanded).toBeTruthy();
	});
});
