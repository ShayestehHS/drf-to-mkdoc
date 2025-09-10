from google import genai
from google.genai.types import GenerateContentResponse

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
                model=self.config.model_name, contents=formatted_messages
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
                content=(response.text or "").strip(),
            )

        except Exception as e:
            raise AIProviderError(
                f"Failed to parse Gemini response: {e!s}",
                provider="GeminiProvider",
                model=self.config.model_name,
            ) from e

    def _extract_token_usage(self, response: GenerateContentResponse) -> TokenUsage:
        try:
            usage = response.usage_metadata
            request_tokens = getattr(usage, "prompt_token_count", 0)
            response_tokens = getattr(usage, "candidates_token_count", 0)

            return TokenUsage(
                request_tokens=request_tokens,
                response_tokens=response_tokens,
                total_tokens=request_tokens + response_tokens,
                provider=self.__class__.__name__,
                model=self.config.model_name,
            )

        except Exception:
            # Return zero usage if extraction fails
            return TokenUsage(
                request_tokens=0,
                response_tokens=0,
                total_tokens=0,
                provider="GeminiProvider",
                model=self.config.model_name,
            )
