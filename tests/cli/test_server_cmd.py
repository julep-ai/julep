from __future__ import annotations

import subprocess
import sys
from typing import Any

from julep.cli.main import serve_api
from julep.server.settings import ServerSettings


class _Store:
    def __init__(self) -> None:
        self.migrated = False
        self.closed = False

    def apply_schema(self) -> None:
        self.migrated = True

    def close(self) -> None:
        self.closed = True


def test_serve_api_applies_overrides_and_optional_migration(monkeypatch) -> None:
    settings = ServerSettings(execution_store_dsn="postgresql://test")
    store = _Store()
    captured: dict[str, Any] = {}
    api = object()

    def fake_create_app(*, settings: ServerSettings) -> object:
        captured["settings"] = settings
        return api

    monkeypatch.setattr(
        "julep.server.settings.ServerSettings.from_env",
        lambda: settings,
    )
    monkeypatch.setattr(
        "julep.server.settings.ServerSettings.build_store",
        lambda _settings: store,
    )
    monkeypatch.setattr(
        "julep.server.app.create_app",
        fake_create_app,
    )
    monkeypatch.setattr(
        "uvicorn.run",
        lambda app, *, host, port: captured.update(app=app, host=host, port=port),
    )

    serve_api(host="0.0.0.0", port=9090, migrate=True)

    assert store.migrated is True
    assert store.closed is True
    assert captured["settings"].host == "0.0.0.0"
    assert captured["settings"].port == 9090
    assert captured["app"] is api
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 9090


def test_core_and_cli_import_without_loading_server_dependencies() -> None:
    code = """
import sys
import julep
from julep.cli import main
assert 'fastapi' not in sys.modules
assert 'uvicorn' not in sys.modules
assert 'psycopg' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
