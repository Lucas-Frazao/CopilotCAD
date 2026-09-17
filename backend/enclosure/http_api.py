"""
Thin HTTP surface for Grok / CoS bots.

    POST /v1/generate   { "part": "badge"|"cover"|"faceplate" }
    POST /v1/validate   { "part": "...", "artifact_id"?: "..." }
    POST /v1/export     { "part": "...", "format": "step"|"stl"|"iges", "dest"?: "..." }
    GET  /health

Auth: ``Authorization: Bearer <token>`` or ``X-Bot-Token``.
Default token is ``local-dogfood`` (override with ``COPILOTCAD_BOT_TOKEN``).
"""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from enclosure.service import EXPORT_FORMATS, PUBLIC_PARTS, export_part, generate_part, validate_part

DEFAULT_TOKEN = "local-dogfood"


def bot_token() -> str:
    return os.environ.get("COPILOTCAD_BOT_TOKEN") or DEFAULT_TOKEN


class EnclosureHandler(BaseHTTPRequestHandler):
    """Stdlib HTTP handler — no extra web framework dependency."""

    server_version = "CopilotCADEnclosure/0.1"

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
        expected = bot_token()
        header = self.headers.get("Authorization", "")
        token = ""
        if header.lower().startswith("bearer "):
            token = header[7:].strip()
        if not token:
            token = self.headers.get("X-Bot-Token", "").strip()
        return bool(token) and secrets.compare_digest(token, expected)

    def do_OPTIONS(self) -> None:  # noqa: N802 — http.server API
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Bot-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 — http.server API
        path = urlparse(self.path).path
        if path in {"/health", "/v1/health"}:
            self._send(200, {"ok": True, "service": "copilotcad-enclosure", "auth": "bot-token"})
            return
        self._send(404, {"ok": False, "error": f"unknown path {path}"})

    def do_POST(self) -> None:  # noqa: N802 — http.server API
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
        except (ValueError, KeyError, FileNotFoundError) as exc:
            self._send(400, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001 — HTTP boundary
            self._send(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})
            return

        self._send(404, {"ok": False, "error": f"unknown path {path}"})

    def _handle_generate(self, payload: dict[str, Any]) -> None:
        part = str(payload.get("part") or "")
        if part not in PUBLIC_PARTS:
            self._send(400, {"ok": False, "error": f"part must be one of {PUBLIC_PARTS}"})
            return
        self._send(200, generate_part(part))

    def _handle_validate(self, payload: dict[str, Any]) -> None:
        part = payload.get("part")
        artifact_id = payload.get("artifact_id")
        mate_artifact_id = payload.get("mate_artifact_id")
        if not part and not artifact_id:
            self._send(400, {"ok": False, "error": "part or artifact_id required"})
            return
        report = validate_part(
            part,
            artifact_id=artifact_id,
            mate_artifact_id=mate_artifact_id,
        )
        status = 200 if report.get("passed") else 422
        self._send(status, report)

    def _handle_export(self, payload: dict[str, Any]) -> None:
        part = payload.get("part")
        artifact_id = payload.get("artifact_id")
        fmt = str(payload.get("format") or "step").lower()
        if fmt not in EXPORT_FORMATS:
            self._send(400, {"ok": False, "error": f"format must be one of {EXPORT_FORMATS}"})
            return
        dest = payload.get("dest")
        if dest:
            dest_path = Path(dest)
        else:
            dest_path = Path(tempfile.mkdtemp(prefix="copilotcad-enclosure-")) / f"part.{fmt}"
        result = export_part(fmt, dest_path, part=part, artifact_id=artifact_id)
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
