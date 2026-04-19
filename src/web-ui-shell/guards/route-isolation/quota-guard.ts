/**
 * QuotaGuard - 配额守卫
 * 
 * 在 builtin 超额时显示 QUOTA_ 语义引导，不发生静默切轨。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §5.1 submit_image_message
 * 参考：02_ARCHITECTURE_OVERVIEW.md §3.5 QUOTA_
 */

import { UiRouteState } from '../../integrations/agent-backend-connection/route-state';

/**
 * 配额状态
 */
export type QuotaStatus = 'available' | 'exhausted' | 'unknown';

/**
 * 配额提示信息
 */
export interface QuotaAlert {
	/** 是否显示配额提示 */
	show_alert: boolean;
	/** 配额状态 */
	status: QuotaStatus;
	/** 提示消息 */
	message: string;
	/** 引导操作 */
	next_action: string;
	/** 是否允许发送 */
	allow_send: boolean;
}

/**
 * 配额守卫
 */
export class QuotaGuard {
	/**
	 * 检查配额状态并生成提示
	 * 验收标准：显示 QUOTA_ 语义提示，并引导切换 BYOK 或等待重置，不发生静默切轨
	 */
	checkQuota(routeState: UiRouteState): QuotaAlert {
		const { active_route, builtin_quota_status } = routeState;

		// 如果不是 builtin 轨道，不显示配额提示
		if (active_route !== 'builtin') {
			return {
				show_alert: false,
				status: 'available',
				message: '',
				next_action: '',
				allow_send: true,
			};
		}

		// 检查配额状态
		switch (builtin_quota_status) {
			case 'exhausted':
				return {
					show_alert: true,
					status: 'exhausted',
					message: 'QUOTA_EXHAUSTED: 内置轨道额度已耗尽',
					next_action: '请切换到 BYOK 轨道或等待额度重置',
					allow_send: false,
				};
			case 'unknown':
				return {
					show_alert: true,
					status: 'unknown',
					message: 'QUOTA_UNKNOWN: 无法确定配额状态',
					next_action: '请检查后端连接状态',
					allow_send: false,
				};
			case 'available':
			default:
				return {
					show_alert: false,
					status: 'available',
					message: '',
					next_action: '',
					allow_send: true,
				};
		}
	}

	/**
	 * 生成 QUOTA_ 语义提示 HTML
	 */
	generateQuotaAlertHTML(alert: QuotaAlert): string {
		if (!alert.show_alert) {
			return '';
		}

		const statusColor = alert.status === 'exhausted' ? '#fee2e2' : '#fef3c7';
		const borderColor = alert.status === 'exhausted' ? '#fca5a5' : '#fcd34d';
		const textColor = alert.status === 'exhausted' ? '#991b1b' : '#92400e';

		return `
			<div class="roco-quota-alert" style="
				background-color: ${statusColor};
				border: 1px dashed ${borderColor};
				border-radius: 8px;
				padding: 12px 16px;
				margin: 8px 0;
				color: ${textColor};
				font-family: var(--roco-font-family-ui);
				font-size: 14px;
				line-height: 1.5;
			">
				<div class="roco-quota-alert-message" style="font-weight: 600; margin-bottom: 4px;">
					${alert.message}
				</div>
				<div class="roco-quota-alert-action" style="font-size: 13px;">
					${alert.next_action}
				</div>
			</div>
		`;
	}

	/**
	 * 检查是否可以发送消息
	 */
	canSend(routeState: UiRouteState): boolean {
		const alert = this.checkQuota(routeState);
		return alert.allow_send;
	}
}

/**
 * 创建配额守卫
 */
export function createQuotaGuard(): QuotaGuard {
	return new QuotaGuard();
}
