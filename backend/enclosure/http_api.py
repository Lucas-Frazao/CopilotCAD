"""
Thin HTTP surface for Grok / CoS bots.

    POST /v1/generate   { "part"?: "...", "inline_spec"?: {}|string }
    POST /v1/validate   { "part"?: "...", "artifact_id"?: "...", "inline_spec"?: ... }
    POST /v1/export     { "part"?: "...", "format": "step"|"stl"|"iges", "dest"?: "..." }
    GET  /v1/spec       ?format=yaml|json
    GET  /health

Auth: ``Authorization: Bearer <token>`` or ``X-Bot-Token``.
Default token is ``local-dogfood`` (override with ``COPILOTCAD_BOT_TOKEN``).
"""

from __future__ import annotations

import json
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from enclosure.auth import DEFAULT_TOKEN, authorize_http, bot_token
from enclosure.service import (
    EXPORT_FORMATS,
    PUBLIC_PARTS,
    export_part,
    generate_part,
    get_evie_spec,
    validate_part,
)

__all__ = ["DEFAULT_TOKEN", "EnclosureHandler", "bot_token", "make_server", "serve_forever"]


class EnclosureHandler(BaseHTTPRequestHandler):
    """Stdlib HTTP handler — no extra web framework dependency."""

    server_version = "CopilotCADEnclosure/0.2"

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep test output quiet; operators can wrap the process for access logs.
        return

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _unauthorized(self) -> None:
        self._send(401, {"ok": False, "error": "missing or invalid bot token"})

    def _authorized(self) -> bool:
        return authorize_http(
            self.headers.get("Authorization", ""),
            self.headers.get("X-Bot-Token", ""),
        )

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Bot-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in {"/health", "/v1/health"}:
            self._send(200, {"ok": True, "service": "copilotcad-enclosure", "auth": "bot-token"})
            return
        if path in {"/v1/spec", "/v1/get_evie_spec"}:
            if not self._authorized():
                self._unauthorized()
                return
            query = parse_qs(parsed.query)
            fmt = (query.get("format") or ["yaml"])[0]
            try:
                self._send(200, get_evie_spec(format=fmt))
            except ValueError as exc:
                self._send(400, {"ok": False, "error": str(exc)})
            return
        self._send(404, {"ok": False, "error": f"unknown path {path}"})

    def do_POST(self) -> None:
        if not self._authorized():
            self._unauthorized()
            return

        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, {"ok": False, "error": "invalid JSON"})
            return
        if not isinstance(payload, dict):
            self._send(400, {"ok": False, "error": "JSON object required"})
            return

        try:
            if path == "/v1/generate":
                self._handle_generate(payload)
                return
            if path == "/v1/validate":
                self._handle_validate(payload)
                return
            if path == "/v1/export":
                self._handle_export(payload)
                return
            if path in {"/v1/spec", "/v1/get_evie_spec"}:
                self._send(200, get_evie_spec(format=str(payload.get("format") or "yaml")))
                return
        except (ValueError, KeyError, FileNotFoundError, TypeError) as exc:
            self._send(400, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001
            self._send(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})
            return

        self._send(404, {"ok": False, "error": f"unknown path {path}"})

    def _handle_generate(self, payload: dict[str, Any]) -> None:
        part = payload.get("part")
        inline_spec = payload.get("inline_spec")
        if part is None and inline_spec is None:
            self._send(400, {"ok": False, "error": "part or inline_spec required"})
            return
        if part is not None:
            part = str(part)
            if part not in PUBLIC_PARTS:
                self._send(400, {"ok": False, "error": f"part must be one of {PUBLIC_PARTS}"})
                return
        self._send(200, generate_part(part, inline_spec=inline_spec))

    def _handle_validate(self, payload: dict[str, Any]) -> None:
        part = payload.get("part")
        artifact_id = payload.get("artifact_id")
        mate_artifact_id = payload.get("mate_artifact_id")
        inline_spec = payload.get("inline_spec")
        if not part and not artifact_id and inline_spec is None:
            self._send(400, {"ok": False, "error": "part, artifact_id, or inline_spec required"})
            return
        report = validate_part(
            part,
            artifact_id=artifact_id,
            mate_artifact_id=mate_artifact_id,
            inline_spec=inline_spec,
        )
        status = 200 if report.get("passed") else 422
        self._send(status, report)

    def _handle_export(self, payload: dict[str, Any]) -> None:
        part = payload.get("part")
        artifact_id = payload.get("artifact_id")
        inline_spec = payload.get("inline_spec")
        fmt = str(payload.get("format") or "step").lower()
        if fmt not in EXPORT_FORMATS:
            self._send(400, {"ok": False, "error": f"format must be one of {EXPORT_FORMATS}"})
            return
        dest = payload.get("dest")
        if dest:
            dest_path = Path(dest)
        else:
            dest_path = Path(tempfile.mkdtemp(prefix="copilotcad-enclosure-")) / f"part.{fmt}"
        result = export_part(
            fmt,
            dest_path,
            part=part,
            artifact_id=artifact_id,
            inline_spec=inline_spec,
        )
        self._send(200, result)


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), EnclosureHandler)


def serve_forever(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = make_server(host, port)
    print(f"copilotcad-enclosure listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
