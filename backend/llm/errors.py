"""LLM adapter exceptions (F-005)."""


class LLMConfigurationError(Exception):
    """Raised when the LLM adapter cannot run (e.g. missing API key)."""


class LLMError(Exception):
    """Raised when the LLM API call fails."""
