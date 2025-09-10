from dataclasses import dataclass, field
from typing import Any

from drf_to_mkdoc.utils.ai_tools.enums import MessageRole


@dataclass
class TokenUsage:
    """Standardized token usage across all providers"""

    request_tokens: int
    response_tokens: int
    total_tokens: int
    provider: str
    model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_tokens": self.request_tokens,
            "response_tokens": self.response_tokens,
            "total_tokens": self.total_tokens,
            "provider": self.provider,
            "model": self.model,
        }


@dataclass
class Message:
    """Chat message"""

    role: MessageRole
    content: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"role": self.role.value, "content": self.content}
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class ChatResponse:
    """Standardized response from AI providers"""

    content: str
    usage: TokenUsage | None = None
    model: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "content": self.content,
        }
        if self.usage:
            result["usage"] = self.usage.to_dict()
        if self.metadata:
            result["metadata"] = self.metadata
        if self.model is not None:
            result["model"] = self.model
        return result


@dataclass
class ProviderConfig:
    """Configuration for AI providers"""

    model_name: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int | None = None
    extra_params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_key": self.api_key,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "extra_params": self.extra_params,
        }
