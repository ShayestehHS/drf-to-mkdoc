class AIProviderError(Exception):
    """Base exception for AI provider errors"""

    def __init__(self, message: str, provider: str | None = None, model: str | None = None):
        self.provider = provider
        self.model = model
        super().__init__(message)

    def __str__(self) -> str:
        base = super().__str__()
        meta = ", ".join(
            part
            for part in (
                f"provider={self.provider}" if self.provider else None,
                f"model={self.model}" if self.model else None,
            )
            if part
        )
        return f"{base} ({meta})" if meta else base
