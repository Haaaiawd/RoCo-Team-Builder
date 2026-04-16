/**
 * AgentBackendClient - Agent 后端连接客户端
 * 
 * 负责与 agent-backend-system 的 HTTP 通信，包括模型列表拉取和对话请求。
 * 
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §5.2 跨系统接口协议
 * 参考：04_SYSTEM_DESIGN/web-ui-system.md §5.3 HTTP API / Connection Summary
 */

/**
 * 模型信息
 */
export interface ModelInfo {
	id: string;
	name: string;
	supports_vision: boolean;
	description?: string;
}

/**
 * 聊天完成请求
 */
export interface ChatCompletionRequest {
	messages: Array<{
		role: string;
		content: string | Array<{ type: string; text?: string; image_url?: { url: string } }>;
	}>;
	model: string;
	stream?: boolean;
}

/**
 * 聊天完成响应
 */
export interface ChatCompletionResponse {
	id: string;
	choices: Array<{
		message: {
			role: string;
			content: string;
		};
	}>;
	usage?: {
		total_tokens: number;
	};
}

/**
 * Agent 后端客户端
 */
export class AgentBackendClient {
	private baseUrl: string;
	private headers: Record<string, string>;

	constructor(config: { base_url: string; user_id?: string; chat_id?: string; internal_secret?: string }) {
		this.baseUrl = config.base_url;
		this.headers = {
			'Content-Type': 'application/json',
		};

		// 内部密钥验证 - 防止伪造会话头部
		if (config.internal_secret) {
			this.headers['X-Roco-Internal-Secret'] = config.internal_secret;
		}

		// 会话头传递契约
		if (config.user_id) {
			this.headers['X-OpenWebUI-User-Id'] = config.user_id;
		}
		if (config.chat_id) {
			this.headers['X-OpenWebUI-Chat-Id'] = config.chat_id;
		}
	}

	/**
	 * 拉取模型列表
	 * GET /v1/models
	 */
	async listModels(): Promise<ModelInfo[]> {
		const response = await fetch(`${this.baseUrl}/v1/models`, {
			method: 'GET',
			headers: this.headers,
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch models: ${response.status} ${response.statusText}`);
		}

		const data = await response.json();
		return data.data || [];
	}

	/**
	 * 发送聊天完成请求
	 * POST /v1/chat/completions
	 */
	async sendChatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
		const response = await fetch(`${this.baseUrl}/v1/chat/completions`, {
			method: 'POST',
			headers: this.headers,
			body: JSON.stringify(request),
		});

		if (!response.ok) {
			throw new Error(`Chat completion failed: ${response.status} ${response.statusText}`);
		}

		return await response.json();
	}

	/**
	 * 更新会话头
	 */
	updateSessionHeaders(user_id?: string, chat_id?: string): void {
		if (user_id) {
			this.headers['X-OpenWebUI-User-Id'] = user_id;
		} else {
			delete this.headers['X-OpenWebUI-User-Id'];
		}

		if (chat_id) {
			this.headers['X-OpenWebUI-Chat-Id'] = chat_id;
		} else {
			delete this.headers['X-OpenWebUI-Chat-Id'];
		}
	}

	/**
	 * 检查后端健康状态
	 * GET /healthz
	 */
	async checkHealth(): Promise<boolean> {
		try {
			const response = await fetch(`${this.baseUrl}/healthz`, {
				method: 'GET',
				headers: this.headers,
			});
			return response.ok;
		} catch {
			return false;
		}
	}

	/**
	 * 检查后端就绪状态
	 * GET /readyz
	 */
	async checkReady(): Promise<boolean> {
		try {
			const response = await fetch(`${this.baseUrl}/readyz`, {
				method: 'GET',
				headers: this.headers,
			});
			return response.ok;
		} catch {
			return false;
		}
	}
}

/**
 * 创建 Agent 后端客户端
 */
export function createAgentBackendClient(config: {
	base_url: string;
	user_id?: string;
	chat_id?: string;
	internal_secret?: string;
}): AgentBackendClient {
	return new AgentBackendClient(config);
}
