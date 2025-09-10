from google import genai
from google.genai.types import GenerateContentConfig, GenerateContentResponse

from drf_to_mkdoc.utils.ai_tools.exceptions import AIProviderError
from drf_to_mkdoc.utils.ai_tools.providers.base_provider import BaseProvider
from drf_to_mkdoc.utils.ai_tools.types import (
    ChatResponse,
    TokenUsage,
)


class GeminiProvider(BaseProvider):
    def _initialize_client(self) -> genai.Client:
        try:
            client = genai.Client(api_key=self.config.api_key)

        except Exception as e:
            raise AIProviderError(
                f"Failed to initialize Gemini client: {e!s}",
                provider="GeminiProvider",
                model=self.config.model_name,
            ) from e
        else:
            return client

    def _send_chat_request(
        self, formatted_messages, *args, **kwargs
    ) -> GenerateContentResponse:
        client: genai.Client = self.client
        try:
            return client.models.generate_content(
                model=self.config.model_name,
                contents=formatted_messages,
                config=GenerateContentConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens,
                    **(self.config.extra_params or {}).get("generate_content_config", {}),
                ),
            )

        except Exception as e:
            raise AIProviderError(
                f"Chat completion failed: Gemini API request failed: {e!s}",
                provider="GeminiProvider",
                model=self.config.model_name,
            ) from e

    def _parse_provider_response(self, response: GenerateContentResponse) -> ChatResponse:
        try:
            return ChatResponse(
                content=(getattr(response, "text", "") or "").strip(),
                model=self.config.model_name,
            )

        except Exception as e:
            raise AIProviderError(
                f"Failed to parse Gemini response: {e!s}",
                provider="GeminiProvider",
                model=self.config.model_name,
            ) from e

    def _extract_token_usage(self, response: GenerateContentResponse) -> TokenUsage:
        usage = getattr(response, "usage_metadata", None)
        if not usage:
            return TokenUsage(
                request_tokens=0,
                response_tokens=0,
                total_tokens=0,
                provider=self.__class__.__name__,
                model=self.config.model_name,
            )
        request_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
        response_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
        return TokenUsage(
            request_tokens=request_tokens,
            response_tokens=response_tokens,
            total_tokens=request_tokens + response_tokens,
            provider=self.__class__.__name__,
            model=self.config.model_name,
        )
