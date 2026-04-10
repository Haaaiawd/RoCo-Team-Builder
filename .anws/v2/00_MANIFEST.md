# .anws v2 - 版本清单

**创建日期**: 2026-04-07
**状态**: Active
**前序版本**: v1
**最近一次更新**: `2026-04-07 — /genesis 升级：前端系统正式化 + Open WebUI 裁剪约束纳入架构基线`

## 版本目标
在 v1 的基础上演进架构真理源，正式提升 `web-ui-system` 的架构地位，明确“基于 Open WebUI，但必须进行能力裁剪与界面收敛”的产品与技术边界。

## 主要变更
- 将 `web-ui-system` 从“主要是配置文档”升级为需要正式设计的核心系统
- 将 Open WebUI 的裁剪、禁用、收敛策略写入 PRD / Architecture / ADR
- 为后续 `web-ui-system` 详细设计与实现精简版前端奠定版本化基线

## 文档清单
- [x] 00_MANIFEST.md (本文件)
- [x] 01_PRD.md
- [x] 02_ARCHITECTURE_OVERVIEW.md
- [x] 03_ADR/ADR_001_TECH_STACK.md
- [x] 03_ADR/ADR_002_DATA_LAYER_CACHE.md
- [x] 03_ADR/ADR_003_SESSION_MANAGEMENT.md
- [x] 03_ADR/ADR_004_WEB_UI_PRUNING_STRATEGY.md
- [x] 04_SYSTEM_DESIGN/
- [ ] 05_TASKS.md (由 /blueprint 生成)
- [x] 06_CHANGELOG.md
- [x] concept_model.json
