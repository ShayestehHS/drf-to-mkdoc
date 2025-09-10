class AIProviderError(Exception):
    """Base exception for AI provider errors"""

    def __init__(self, message: str, provider: str | None = None, model: str | None = None):
        self.provider = provider
        self.model = model
        super().__init__(message)
