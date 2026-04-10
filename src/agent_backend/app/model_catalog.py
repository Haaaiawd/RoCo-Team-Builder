"""
受控虚拟模型目录 — 管理对外暴露的模型 ID 与能力元数据。

对齐: agent-backend-system.md §4.2 Model Catalog
     agent-backend-system.detail.md §1 MODEL_CATALOG_POLICY, §2 ModelCatalogEntry
     agent-backend-system.detail.md §3.4 list_models(catalog)

不直接透传 provider 模型名。public_model_id 是产品层面的虚拟身份。
"""

from __future__ import annotations

import os
from dataclasses import dataclass


MODEL_CATALOG_POLICY = {
    "owned_by": "roco-agent",
    "default_visibility": "controlled",
    "supports_vision_flag": True,
}


@dataclass
class ModelCatalogEntry:
    """模型目录条目 — 管理单个虚拟模型的 provider 映射与能力。"""

    public_model_id: str
    provider_model_name: str
    provider_base_url: str
    supports_vision: bool
    enabled: bool
    default_temperature: float | None = None

    def can_accept_image(self) -> bool:
        """是否能接受图片输入。"""
        return self.enabled and self.supports_vision


class ModelCatalog:
    """受控虚拟模型目录。

    从环境变量或默认配置初始化。
    agent-backend-system 不允许直接暴露 provider 原生模型名。
    """

    def __init__(self, entries: list[ModelCatalogEntry] | None = None) -> None:
        self._entries: dict[str, ModelCatalogEntry] = {}
        if entries:
            for e in entries:
                self._entries[e.public_model_id] = e
        else:
            self._load_defaults()

    def _load_defaults(self) -> None:
        """从环境变量加载默认模型配置。"""
        self._entries["roco-agent"] = ModelCatalogEntry(
            public_model_id="roco-agent",
            provider_model_name=os.environ.get("ROCO_PROVIDER_MODEL", "gpt-4o-mini"),
            provider_base_url=os.environ.get(
                "ROCO_PROVIDER_BASE_URL", "https://api.openai.com/v1"
            ),
            supports_vision=True,
            enabled=True,
        )

    def get(self, model_id: str) -> ModelCatalogEntry | None:
        """查找模型条目。"""
        return self._entries.get(model_id)

    def list_models(self) -> list[dict]:
        """返回受控虚拟模型列表 — OpenAI /v1/models 响应体。

        对齐: agent-backend-system.detail.md §3.4
        """
        visible = []
        for entry in self._entries.values():
            if not entry.enabled:
                continue
            visible.append(
                {
                    "id": entry.public_model_id,
                    "object": "model",
                    "created": 0,
                    "owned_by": MODEL_CATALOG_POLICY["owned_by"],
                    "metadata": {
                        "supports_vision": entry.supports_vision,
                    },
                }
            )
        return visible

    @property
    def entries(self) -> dict[str, ModelCatalogEntry]:
        return dict(self._entries)
