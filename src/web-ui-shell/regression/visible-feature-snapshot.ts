/**
 * VisibleFeatureSnapshot - UI 回归测试快照导出
 * 
 * 用于发布前比对 Open WebUI 升级后的功能可见性变化。
 * 确保 ADR-004 定义的白名单策略不被上游更新破坏。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §11.3 UI 回归测试
 */

import { VisibleFeaturePolicy, FeaturePolicySnapshot, createRocoDefaultPolicy } from '../guards/feature-whitelist/policy';

/**
 * 快照导出器
 */
export class SnapshotExporter {
	private policy: VisibleFeaturePolicy;

	constructor(policy: VisibleFeaturePolicy) {
		this.policy = policy;
	}

	/**
	 * 导出当前快照
	 */
	exportCurrent(): FeaturePolicySnapshot {
		return this.policy.exportSnapshot();
	}

	/**
	 * 导出为 JSON 字符串
	 */
	exportAsJsonString(): string {
		const snapshot = this.exportCurrent();
		return JSON.stringify(snapshot, null, 2);
	}

	/**
	 * 保存快照到 localStorage
	 * 用于浏览器端持久化基线
	 */
	saveToLocalStorage(baselineId: string): void {
		const snapshot = this.exportCurrent();
		snapshot.validation_baseline_id = baselineId;
		localStorage.setItem('roco_feature_snapshot', JSON.stringify(snapshot));
	}

	/**
	 * 从 localStorage 加载快照
	 */
	loadFromLocalStorage(): FeaturePolicySnapshot | null {
		const data = localStorage.getItem('roco_feature_snapshot');
		if (!data) return null;
		try {
			return JSON.parse(data) as FeaturePolicySnapshot;
		} catch {
			return null;
		}
	}

	/**
	 * 比对当前快照与基线快照
	 */
	compareWithBaseline(baseline: FeaturePolicySnapshot): SnapshotComparison {
		const current = this.exportCurrent();
		const visibleAdded = current.visible_entries.filter(
			e => !baseline.visible_entries.includes(e)
		);
		const visibleRemoved = baseline.visible_entries.filter(
			e => !current.visible_entries.includes(e)
		);
		const hiddenAdded = current.hidden_entries.filter(
			e => !baseline.hidden_entries.includes(e)
		);
		const hiddenRemoved = baseline.hidden_entries.filter(
			e => !current.hidden_entries.includes(e)
		);

		const hasRegressions = visibleAdded.length > 0 || hiddenRemoved.length > 0;

		return {
			baseline_id: baseline.validation_baseline_id,
			current_version: current.policy_version,
			baseline_version: baseline.policy_version,
			has_regressions: hasRegressions,
			visible_added: visibleAdded,
			visible_removed: visibleRemoved,
			hidden_added: hiddenAdded,
			hidden_removed: hiddenRemoved,
			regression_summary: this.buildRegressionSummary(
				visibleAdded,
				visibleRemoved,
				hiddenAdded,
				hiddenRemoved
			),
		};
	}

	/**
	 * 构建回归摘要
	 */
	private buildRegressionSummary(
		visibleAdded: string[],
		visibleRemoved: string[],
		hiddenAdded: string[],
		hiddenRemoved: string[]
	): string {
		const parts: string[] = [];

		if (visibleAdded.length > 0) {
			parts.push(`新增可见入口: ${visibleAdded.join(', ')}`);
		}
		if (visibleRemoved.length > 0) {
			parts.push(`移除可见入口: ${visibleRemoved.join(', ')}`);
		}
		if (hiddenAdded.length > 0) {
			parts.push(`新增隐藏入口: ${hiddenAdded.join(', ')}`);
		}
		if (hiddenRemoved.length > 0) {
			parts.push(`移除隐藏入口: ${hiddenRemoved.join(', ')}`);
		}

		return parts.length > 0 ? parts.join('; ') : '无变化';
	}
}

/**
 * 快照比对结果
 */
export interface SnapshotComparison {
	baseline_id: string | null;
	current_version: string;
	baseline_version: string;
	has_regressions: boolean;
	visible_added: string[];
	visible_removed: string[];
	hidden_added: string[];
	hidden_removed: string[];
	regression_summary: string;
}

/**
 * 创建默认快照导出器
 */
export function createDefaultSnapshotExporter(): SnapshotExporter {
	const policy = createRocoDefaultPolicy();
	return new SnapshotExporter(policy);
}

/**
 * 生成初始基线快照
 * 用于首次发布前建立基线
 */
export function generateInitialBaseline(): FeaturePolicySnapshot {
	const exporter = createDefaultSnapshotExporter();
	const snapshot = exporter.exportCurrent();
	snapshot.validation_baseline_id = `baseline-${Date.now()}`;
	return snapshot;
}
