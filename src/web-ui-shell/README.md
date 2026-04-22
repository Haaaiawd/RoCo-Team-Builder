# Web UI Shell - RoCo Team Builder 前端产品壳层

这是 RoCo Team Builder 的前端产品壳层，基于 Open WebUI 的受控裁剪版本。

## 项目结构

```
src/web-ui-shell/
├── guards/
│   └── feature-whitelist/
│       ├── policy.ts              # 可见功能白名单策略（真理源）
│       └── policy.test.ts         # 策略单元测试
├── regression/
│   └── visible-feature-snapshot.ts  # UI 回归测试快照导出
└── shell/
    └── layout/
        └── theme-config.ts        # 复古冒险者手账风主题配置
```

## 核心功能

### 1. 可见功能白名单策略（VisibleFeaturePolicy）

这是 web-ui-system 的**唯一真理源**，定义终端用户可见的能力范围。

**允许的功能**：
- 聊天界面
- 图片上传
- 模型/Key 配置（内置轨道 + BYOK）
- 工具结果展示
- 富卡片宿主

**禁止的功能**（Open WebUI 原生功能）：
- Notes
- Channels
- Open Terminal
- Knowledge
- Admin Panel
- Documents
- Gallery
- Workspace
- Prompts
- Advanced Settings

### 2. UI 回归测试快照导出

用于发布前比对 Open WebUI 升级后的功能可见性变化，确保白名单策略不被上游更新破坏。

### 3. 复古冒险者手账风主题

**视觉语言**：
- 整体气质：复古冒险者手账风，不是通用 AI 平台控制台
- 主色结构：炭黑侧栏、羊皮纸主聊天区、暖金强调色、奶白表面层
- 纹理策略：主区叠加 5%-10% 透明度的地图线稿/山脉/齿轮类 SVG 纹理
- 版式语汇：侧栏与主区交界使用撕纸/笔刷边缘
- 聊天语汇：用户气泡是纸贴片；Agent 文本更接近直接书写在纸面上的记录；输入区采用胶囊形工具条
- 组件语汇：History 项、快捷按钮、工具卡片必须具备手账标签感

## 使用方法

### 初始化白名单策略

```typescript
import { createRocoDefaultPolicy } from './guards/feature-whitelist/policy';

const policy = createRocoDefaultPolicy();

// 检查功能是否可见
if (policy.allows(FeatureKey.CHAT_INTERFACE)) {
  // 显示聊天界面
}
```

### 导出快照

```typescript
import { createDefaultSnapshotExporter } from './regression/visible-feature-snapshot';

const exporter = createDefaultSnapshotExporter();
const snapshot = exporter.exportCurrent();

// 保存到 localStorage
exporter.saveToLocalStorage('baseline-v1');
```

### 注入主题

```typescript
import { createThemeInjector } from './shell/layout/theme-config';

const injector = createThemeInjector();
injector.inject();
```

## 测试

已接入 **vitest + TypeScript**：

```bash
cd src/web-ui-shell
npm install                 # 仅本目录，不污染仓库根
npm run typecheck           # tsc --noEmit
npm test                    # vitest run
```

- `**/*.vitest.ts`：真正可运行的 vitest 用例（当前仅 `guards/feature-whitelist/policy.vitest.ts` 冒烟）。
- `**/*.test.ts`：历史 console.log 风格的 runner（导出 `runXxxTests()` 函数），不进 vitest include，留给后续独立 PR 迁移。

`tsconfig.json` 开启 strict + DOM lib，目前 `tsc --noEmit` 对全部 `.ts` 零报错。

## 参考资料

- ADR-004: Web UI 裁剪与收敛策略
- 04_SYSTEM_DESIGN/web-ui-system.md
- asserts/ui-style.png（视觉设计稿）
- references/open-webui（Open WebUI 参考源）

## 注意事项

1. **白名单优先**：任何不在白名单中的功能都必须对终端用户不可见、不可达
2. **视觉一致性**：所有 UI 组件必须遵循"复古冒险者手账风"视觉语言
3. **UI 回归**：每次 Open WebUI 升级后必须运行快照比对，确保禁止入口不会重新暴露
