"""
test_evie_enclosure_http.py — thin HTTP connector for Grok / CoS
===============================================================

Auth is a local bot-token stub. Generate / validate / export share the
in-process artifact store. Geometry tests skip without pythonocc-core.
"""

from __future__ import annotations

import json
from importlib.util import find_spec
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from enclosure.http_api import bot_token, make_server

HAS_OCCT = find_spec("OCC") is not None
needs_occt = pytest.mark.skipif(not HAS_OCCT, reason="pythonocc-core not installed")


@pytest.fixture
def enclosure_server():
    server = make_server("127.0.0.1", 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    yield f"http://{host}:{port}"
    server.shutdown()
    thread.join(timeout=2)


def _post(url: str, path: str, payload: dict, token: str | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        url + path,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
            return response.status, body
    except HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8"))
        return exc.code, body


def _get(url: str, path: str, token: str | None = None) -> tuple[int, dict]:
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url + path, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
            return response.status, body
    except HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8"))
        return exc.code, body


def test_health_needs_no_token(enclosure_server):
    with urlopen(enclosure_server + "/health", timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    assert payload["ok"] is True


def test_generate_requires_token(enclosure_server):
    status, body = _post(enclosure_server, "/v1/generate", {"part": "badge"}, token=None)
    assert status == 401
    assert body["ok"] is False


def test_http_spec_requires_token(enclosure_server):
    status, body = _get(enclosure_server, "/v1/spec?format=json", token=None)
    assert status == 401
    assert body["ok"] is False


def test_http_get_evie_spec(enclosure_server):
    status, body = _get(enclosure_server, "/v1/spec?format=json", token=bot_token())
    assert status == 200
    assert body["ok"] is True
    assert body["project"] == "Evie"


@needs_occt
def test_http_generate_validate_export_badge(enclosure_server, tmp_path):
    token = bot_token()
    status, generated = _post(
        enclosure_server, "/v1/generate", {"part": "badge"}, token=token
    )
    assert status == 200
    assert generated["ok"] is True
    artifact_id = generated["artifact_id"]

    status, report = _post(
        enclosure_server,
        "/v1/validate",
        {"artifact_id": artifact_id},
        token=token,
    )
    assert status == 200
    assert report["passed"] is True

    dest = tmp_path / "badge.step"
    status, exported = _post(
        enclosure_server,
        "/v1/export",
        {"artifact_id": artifact_id, "format": "step", "dest": str(dest)},
        token=token,
    )
    assert status == 200
    assert exported["bytes"] > 0
    assert dest.is_file()


@needs_occt
def test_http_generate_inline_spec(enclosure_server):
    token = bot_token()
    inline = {
        "schema_version": "1.1",
        "project": "Evie",
        "parts": {
            "badge": {"extents": {"x": 45, "y": 15, "z": 2}, "extents_tol": 1.0}
        },
    }
    status, generated = _post(
        enclosure_server,
        "/v1/generate",
        {"part": "badge", "inline_spec": inline},
        token=token,
    )
    assert status == 200
    assert generated["spec_source"] == "inline"
    status, report = _post(
        enclosure_server,
        "/v1/validate",
        {"artifact_id": generated["artifact_id"], "inline_spec": inline},
        token=token,
    )
    assert status == 200
    assert report["passed"] is True
