import { defineConfig } from 'vitest/config';

export default defineConfig({
	test: {
		globals: true,
		environment: 'jsdom',
		include: ['**/*.vitest.ts'],
		// 现有 **/*.test.ts 文件是 pre-vitest 的 console.log 风格 runner
		// （导出 `runXxxTests()` 函数），迁移到 vitest 的工作由后续 PR 承接。
		// 暂以 `.vitest.ts` 后缀承载真正的 vitest 用例，避免把旧文件误收进来。
	},
});
