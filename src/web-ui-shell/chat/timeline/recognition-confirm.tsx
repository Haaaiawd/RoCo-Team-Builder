/**
 * 截图识别确认卡片组件
 * 
 * 展示多模态 LLM 识别的精灵候选列表，用户可确认或取消。
 * 确认后通过 POST /v1/recognition/confirm 发送信号到后端。
 * 
 * 验收标准: FIX-RECOGNITION-CLOSURE
 * - 包含 [data-testid="recognition-review"] 容器
 * - 包含 [data-testid="recognition-candidate"] 候选列表项
 * - 包含 [data-testid="confirm-owned-list"] 确认按钮
 * - 包含 [data-testid="owned-list-status"] 状态提示
 */

import React, { useState } from 'react';

export interface RecognitionConfirmProps {
	/** 识别的精灵候选列表 */
	candidates: string[];
	/** 确认回调 */
	onConfirm: (spirits: string[]) => void;
	/** 取消回调 */
	onCancel: () => void;
}

export function RecognitionConfirm({
	candidates,
	onConfirm,
	onCancel,
}: RecognitionConfirmProps) {
	const [selectedSpirits, setSelectedSpirits] = useState<string[]>(candidates);

	const handleConfirm = () => {
		onConfirm(selectedSpirits);
	};

	const handleCancel = () => {
		onCancel();
	};

	const toggleSpirit = (spirit: string) => {
		setSelectedSpirits(prev =>
			prev.includes(spirit)
				? prev.filter(s => s !== spirit)
				: [...prev, spirit]
		);
	};

	return (
		<div data-testid="recognition-review" className="recognition-confirm-card">
			<h3>确认识别结果</h3>
			<p>请确认以下精灵是否为您拥有的：</p>
			
			<div className="candidates-list">
				{candidates.map((spirit) => (
					<div
						key={spirit}
						data-testid="recognition-candidate"
						className={`candidate-item ${selectedSpirits.includes(spirit) ? 'selected' : ''}`}
						onClick={() => toggleSpirit(spirit)}
					>
						<input
							type="checkbox"
							checked={selectedSpirits.includes(spirit)}
							onChange={() => toggleSpirit(spirit)}
						/>
						<span>{spirit}</span>
					</div>
				))}
			</div>

			<div className="action-buttons">
				<button
					data-testid="confirm-owned-list"
					className="confirm-button"
					onClick={handleConfirm}
					disabled={selectedSpirits.length === 0}
				>
					确认拥有 ({selectedSpirits.length})
				</button>
				<button
					className="cancel-button"
					onClick={handleCancel}
				>
					取消
				</button>
			</div>
		</div>
	);
}

/**
 * 已确认拥有列表状态提示组件
 */
export function OwnedListStatus() {
	return (
		<div data-testid="owned-list-status" className="owned-list-status">
			基于已确认拥有列表
		</div>
	);
}
