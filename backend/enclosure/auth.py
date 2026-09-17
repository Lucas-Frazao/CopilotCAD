"""
Local bot-token stub for the enclosure connector.

HTTP requires ``Authorization: Bearer <token>`` (or ``X-Bot-Token``).
MCP stdio is process-local: the default stub ``local-dogfood`` is accepted
without a per-call token. If ``COPILOTCAD_BOT_TOKEN`` is set to anything else,
MCP tool calls must pass a matching ``token`` argument.
"""

from __future__ import annotations

import os
import secrets

DEFAULT_TOKEN = "local-dogfood"
TOKEN_ENV = "COPILOTCAD_BOT_TOKEN"


def bot_token() -> str:
    """Return the configured stub token (env override, else ``local-dogfood``)."""
    return os.environ.get(TOKEN_ENV) or DEFAULT_TOKEN


def token_matches(provided: str | None) -> bool:
    expected = bot_token()
    if not provided:
        return False
    return secrets.compare_digest(str(provided), expected)


def extract_http_token(authorization: str, x_bot_token: str) -> str:
    token = ""
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        token = x_bot_token.strip()
    return token


def authorize_http(authorization: str = "", x_bot_token: str = "") -> bool:
    return token_matches(extract_http_token(authorization, x_bot_token))


class BotAuthError(PermissionError):
    """Raised when a bot tool call is missing or has a bad token."""


def authorize_mcp(provided: str | None) -> None:
    """
    Check an optional MCP ``token`` argument.

    * Token present → must match ``bot_token()``.
    * Token omitted + default stub → allowed (local trusted stdio).
    * Token omitted + custom ``COPILOTCAD_BOT_TOKEN`` → rejected.
    """
    expected = bot_token()
    if provided:
        if not secrets.compare_digest(str(provided), expected):
            raise BotAuthError("missing or invalid bot token")
        return
    if expected != DEFAULT_TOKEN:
        raise BotAuthError("token required when COPILOTCAD_BOT_TOKEN is set")
