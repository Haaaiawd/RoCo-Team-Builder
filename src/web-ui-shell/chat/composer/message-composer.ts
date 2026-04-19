/**
 * MessageComposer - 消息编写器
 * 
 * 整合能力预检和配额守卫，提供安全的消息发送接口。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §5.1 submit_text_message / submit_image_message
 */

import { UiRouteState } from '../../integrations/agent-backend-connection/route-state';
import { ImageCapabilityPreflight, PreflightResult, createImageCapabilityPreflight } from '../attachments/preflight';
import { QuotaGuard, QuotaAlert, createQuotaGuard } from '../../guards/route-isolation/quota-guard';

/**
 * 消息发送请求
 */
export interface SendMessageRequest {
	/** 文本内容 */
	text: string;
	/** 是否包含图片 */
	has_image: boolean;
	/** 图片文件（如果有） */
	image_file?: File;
}

/**
 * 消息发送结果
 */
export interface SendMessageResult {
	/** 是否允许发送 */
	allowed: boolean;
	/** 预检结果 */
	preflight?: PreflightResult;
	/** 配额提示 */
	quota_alert?: QuotaAlert;
	/** 错误消息 */
	error_message?: string;
}

/**
 * 消息编写器
 */
export class MessageComposer {
	private preflight: ImageCapabilityPreflight;
	private quotaGuard: QuotaGuard;

	constructor() {
		this.preflight = createImageCapabilityPreflight();
		this.quotaGuard = createQuotaGuard();
	}

	/**
	 * 准备发送消息
	 * 整合能力预检和配额守卫
	 */
	prepareSendMessage(routeState: UiRouteState, request: SendMessageRequest): SendMessageResult {
		// 执行能力预检
		const preflightResult = this.preflight.preflight(routeState, request.has_image);

		if (!preflightResult.allowed) {
			return {
				allowed: false,
				preflight: preflightResult,
				error_message: preflightResult.error_message,
			};
		}

		// 检查配额状态
		const quotaAlert = this.quotaGuard.checkQuota(routeState);

		if (!quotaAlert.allow_send) {
			return {
				allowed: false,
				quota_alert: quotaAlert,
				error_message: quotaAlert.message,
			};
		}

		// 验收标准：当前模型支持视觉且额度可用，请求进入正常的图文消息链路
		return {
			allowed: true,
			preflight: preflightResult,
			quota_alert: quotaAlert,
		};
	}

	/**
	 * 生成错误提示 HTML
	 */
	generateErrorAlert(result: SendMessageResult): string {
		if (result.allowed) {
			return '';
		}

		if (result.quota_alert?.show_alert) {
			return this.quotaGuard.generateQuotaAlertHTML(result.quota_alert);
		}

		if (result.preflight?.error_message) {
			const errorColor = '#fee2e2';
			const borderColor = '#fca5a5';
			const textColor = '#991b1b';

			return `
				<div class="roco-error-alert" style="
					background-color: ${errorColor};
					border: 1px dashed ${borderColor};
					border-radius: 8px;
					padding: 12px 16px;
					margin: 8px 0;
					color: ${textColor};
					font-family: var(--roco-font-family-ui);
					font-size: 14px;
					line-height: 1.5;
				">
					<div class="roco-error-alert-message" style="font-weight: 600; margin-bottom: 4px;">
						${result.preflight.error_type}: ${result.preflight.error_message}
					</div>
					<div class="roco-error-alert-action" style="font-size: 13px;">
						${result.preflight.next_step}
					</div>
				</div>
			`;
		}

		return '';
	}

	/**
	 * 检查是否可以发送文本消息
	 */
	canSendText(routeState: UiRouteState): boolean {
		// 文本消息不需要能力预检
		const quotaAlert = this.quotaGuard.checkQuota(routeState);
		return quotaAlert.allow_send;
	}

	/**
	 * 检查是否可以发送图片消息
	 */
	canSendImage(routeState: UiRouteState): boolean {
		const preflight = this.preflight.preflight(routeState, true);
		const quotaAlert = this.quotaGuard.checkQuota(routeState);
		return preflight.allowed && quotaAlert.allow_send;
	}
}

/**
 * 创建消息编写器
 */
export function createMessageComposer(): MessageComposer {
	return new MessageComposer();
}
