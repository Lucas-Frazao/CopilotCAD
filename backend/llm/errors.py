"""
============================================================================
FILE: errors.py — Exceptions for the LLM (AI) adapter layer (F-005)
============================================================================

The LLM adapter talks to external AI services (e.g. Claude) to turn natural
language into structured CAD "intent". When setup is wrong or the API fails,
this module's exception types let the rest of the app show clear errors.

F-005 introduced LLM integration; these errors are caught and mapped to
user-friendly messages in the UI (see formatUserError.ts in the frontend).
============================================================================
"""


class LLMConfigurationError(Exception):
    """
    Raised when the LLM adapter cannot run at all.

    Typical cause: missing ANTHROPIC_API_KEY environment variable or invalid
    local model configuration. This is a "fix your setup" error, not a bad prompt.
    """


class LLMError(Exception):
    """
    Raised when configuration is OK but the LLM API call itself fails.

    Examples: network timeout, rate limit, or an unexpected API response.
    """
