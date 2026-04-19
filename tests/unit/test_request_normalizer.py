from __future__ import annotations

import pytest

from agent_backend.api.error_mapping import ProductError
from agent_backend.app.model_catalog import ModelCatalog, ModelCatalogEntry
from agent_backend.app.request_normalizer import REQUEST_LIMITS, normalize_chat_request


class TestNormalizeChatRequest:
    def test_text_request_success(self):
        catalog = ModelCatalog()
        payload = {
            "model": "roco-agent",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
        }
        headers = {
            "x-openwebui-user-id": "user-1",
            "x-openwebui-chat-id": "chat-1",
        }

        context = normalize_chat_request(payload, headers, catalog)

        assert context.session_key == "user-1:chat-1"
        assert context.model_entry.public_model_id == "roco-agent"
        assert context.messages[0]["content"] == "hello"
        assert context.stream is False

    def test_multimodal_request_preserves_image_part(self):
        catalog = ModelCatalog()
        payload = {
            "model": "roco-agent",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "看看这只精灵"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/png;base64,abc123",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
        }
        headers = {
            "x-openwebui-user-id": "user-1",
            "x-openwebui-chat-id": "chat-1",
        }

        context = normalize_chat_request(payload, headers, catalog)

        content = context.messages[0]["content"]
        assert isinstance(content, list)
        assert content[1]["type"] == "image_url"
        assert content[1]["image_url"]["url"] == "data:image/png;base64,abc123"

    def test_unknown_model_raises_model_error(self):
        catalog = ModelCatalog()
        payload = {
            "model": "missing-model",
            "messages": [{"role": "user", "content": "hello"}],
        }
        headers = {
            "x-openwebui-user-id": "user-1",
            "x-openwebui-chat-id": "chat-1",
        }

        with pytest.raises(ProductError) as exc_info:
            normalize_chat_request(payload, headers, catalog)

        assert exc_info.value.code == "MODEL_NOT_FOUND"

    def test_non_vision_model_rejects_image(self):
        catalog = ModelCatalog(
            entries=[
                ModelCatalogEntry(
                    public_model_id="text-only",
                    provider_model_name="provider/text-only",
                    provider_base_url="http://test",
                    supports_vision=False,
                    enabled=True,
                )
            ]
        )
        payload = {
            "model": "text-only",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "看看这只精灵"},
                        {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}},
                    ],
                }
            ],
        }
        headers = {
            "x-openwebui-user-id": "user-1",
            "x-openwebui-chat-id": "chat-1",
        }

        with pytest.raises(ProductError) as exc_info:
            normalize_chat_request(payload, headers, catalog)

        assert exc_info.value.code == "CAPABILITY_VISION_UNSUPPORTED"

    def test_missing_headers_raises_session_error(self):
        catalog = ModelCatalog()
        payload = {
            "model": "roco-agent",
            "messages": [{"role": "user", "content": "hello"}],
        }

        with pytest.raises(ProductError) as exc_info:
            normalize_chat_request(payload, {}, catalog)

        assert exc_info.value.code == "SESSION_MISSING_IDENTITY"

    def test_empty_messages_rejected(self):
        catalog = ModelCatalog()
        payload = {"model": "roco-agent", "messages": []}
        headers = {
            "x-openwebui-user-id": "user-1",
            "x-openwebui-chat-id": "chat-1",
        }

        with pytest.raises(ProductError) as exc_info:
            normalize_chat_request(payload, headers, catalog)

        assert exc_info.value.code == "VALIDATION_INVALID_REQUEST"

    def test_text_too_long_rejected(self):
        catalog = ModelCatalog()
        payload = {
            "model": "roco-agent",
            "messages": [{"role": "user", "content": "x" * (REQUEST_LIMITS["max_text_chars"] + 1)}],
        }
        headers = {
            "x-openwebui-user-id": "user-1",
            "x-openwebui-chat-id": "chat-1",
        }

        with pytest.raises(ProductError) as exc_info:
            normalize_chat_request(payload, headers, catalog)

        assert exc_info.value.code == "VALIDATION_PAYLOAD_TOO_LARGE"

    def test_max_tokens_too_large_rejected(self):
        catalog = ModelCatalog()
        payload = {
            "model": "roco-agent",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": REQUEST_LIMITS["max_tokens"] + 1,
        }
        headers = {
            "x-openwebui-user-id": "user-1",
            "x-openwebui-chat-id": "chat-1",
        }

        with pytest.raises(ProductError) as exc_info:
            normalize_chat_request(payload, headers, catalog)

        assert exc_info.value.code == "VALIDATION_PAYLOAD_TOO_LARGE"
