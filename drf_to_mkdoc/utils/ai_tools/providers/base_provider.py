import json
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import Any

from django.template import RequestContext

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.ai_tools.exceptions import AIProviderError
from drf_to_mkdoc.utils.ai_tools.types import (
    ChatResponse,
    Message,
    ProviderConfig,
    TokenUsage,
)
from drf_to_mkdoc.utils.commons.schema_utils import OperationExtractor


class BaseProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._client = None

    @property
    def client(self):
        """Lazy load client"""
        if self._client is None:
            if not hasattr(self, "_client_lock"):
                # If providers are shared across threads, guard initialization.
                self._client_lock = Lock()
            with self._client_lock:
                if self._client is None:
                    self._client = self._initialize_client()
        return self._client

    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize provider-specific client"""
        pass

    @abstractmethod
    def _send_chat_request(self, formatted_messages: Any, **kwargs) -> Any:
        """Send request to provider's API"""
        pass

    @abstractmethod
    def _parse_provider_response(self, response: Any) -> ChatResponse:
        """Parse provider response to standard ChatResponse"""
        pass

    @abstractmethod
    def _extract_token_usage(self, response: Any) -> TokenUsage:
        """Extract token usage from provider response"""
        pass

    def format_messages_for_provider(self, messages: list[Message]) -> Any:
        """
        Convert your Message objects into a single string for chat.send_message().
        This is a default behavior. You can override it your self as you want.
        """
        lines = []
        for message in messages:
            lines.append(f"{message.role.value}: {message.content}")

        return "\n".join(lines)

    def chat_completion(self, messages: list[Message], **kwargs) -> ChatResponse:
        """
        Send chat completion request without functions

        Args:
            messages: List of chat messages
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse with AI's response
        """
        try:
            formatted_messages = self.format_messages_for_provider(messages)

            raw_response = self._send_chat_request(formatted_messages, **kwargs)

            response = self._parse_provider_response(raw_response)

            response.usage = self._extract_token_usage(raw_response)
            response.model = self.config.model_name

        except Exception as e:
            raise AIProviderError(
                f"Chat completion failed: {e!s}",
                provider=self.__class__.__name__,
                model=self.config.model_name,
            ) from e
        else:
            return response

    def _get_operation_info(
        self, operation_id: str, context: RequestContext | None = None
    ) -> dict[str, Any]:
        return OperationExtractor().operation_map.get(operation_id)

    def _get_model_info(self, app_label: str, model_name: str) -> dict[str, Any]:
        docs_file = Path(drf_to_mkdoc_settings.MODEL_DOCS_FILE)

        if not docs_file.exists():
            raise FileNotFoundError(f"Model documentation file not found: {docs_file}")

        with docs_file.open("r", encoding="utf-8") as f:
            model_docs = json.load(f)

        if app_label not in model_docs:
            raise LookupError(f"App '{app_label}' not found in model documentation.")

        if model_name not in model_docs[app_label]:
            raise LookupError(f"Model '{model_name}' not found in model documentation.")

        return model_docs[app_label][model_name]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.__class__.__name__}, model={self.config.model_name})"
