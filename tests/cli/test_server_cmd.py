from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import typer
from typer.testing import CliRunner

from julep.cli.main import app, db_reencrypt_secrets, serve_api
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
        lambda *_args: settings,
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

    serve_api(
        host="0.0.0.0",
        port=9090,
        migrate=True,
        local=False,
        context_factory=None,
    )

    assert store.migrated is True
    assert store.closed is True
    assert captured["settings"].host == "0.0.0.0"
    assert captured["settings"].port == 9090
    assert captured["app"] is api
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 9090


def test_serve_api_local_builds_zero_daemon_app(monkeypatch, tmp_path) -> None:
    settings = ServerSettings(host="127.0.0.1", port=8080)
    captured: dict[str, Any] = {}
    api = object()
    factory = object()

    def fake_create_local_app(*, project_root: Path, host: str, context_factory: object) -> object:
        captured.update(
            project_root=project_root,
            local_host=host,
            context_factory=context_factory,
        )
        return api

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "julep.server.settings.ServerSettings.from_env",
        lambda *_args: settings,
    )
    serve_module = importlib.import_module("julep.execution.serve")
    monkeypatch.setattr(
        serve_module,
        "load_context_factory",
        lambda spec: factory if spec == "example:make_context" else None,
    )
    monkeypatch.setattr(
        "julep.server.create_local_app",
        fake_create_local_app,
        raising=False,
    )
    monkeypatch.setattr(
        "uvicorn.run",
        lambda app, *, host, port: captured.update(app=app, host=host, port=port),
    )

    result = CliRunner().invoke(
        app,
        [
            "serve",
            "api",
            "--local",
            "--host",
            "127.0.0.2",
            "--port",
            "9091",
            "--context-factory",
            "example:make_context",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured == {
        "project_root": tmp_path,
        "local_host": "127.0.0.2",
        "context_factory": factory,
        "app": api,
        "host": "127.0.0.2",
        "port": 9091,
    }


def test_serve_api_local_rejects_migration(monkeypatch, capsys) -> None:
    called = False

    def fake_create_local_app(**_kwargs) -> object:
        nonlocal called
        called = True
        return object()

    monkeypatch.setattr(
        "julep.server.create_local_app",
        fake_create_local_app,
        raising=False,
    )

    with pytest.raises(typer.Exit) as exc_info:
        serve_api(
            host=None,
            port=None,
            migrate=True,
            local=True,
            context_factory=None,
        )

    assert exc_info.value.exit_code == 2
    assert called is False
    assert "--migrate cannot be used with --local" in capsys.readouterr().err


def test_serve_api_context_factory_requires_local(capsys) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        serve_api(
            host=None,
            port=None,
            migrate=False,
            local=False,
            context_factory="example:make_context",
        )

    assert exc_info.value.exit_code == 2
    assert "--context-factory requires --local" in capsys.readouterr().err


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


def test_reencrypt_secrets_reports_progress_and_closes(monkeypatch, capsys) -> None:
    stores: list[Any] = []

    class Store:
        def __init__(self, dsn: str) -> None:
            assert dsn == "postgresql://vault"
            self.migrated = False
            self.closed = False
            stores.append(self)

        def apply_schema(self) -> None:
            self.migrated = True

        def reencrypt_secrets(self, cipher: object, progress):
            assert cipher is sentinel
            progress(1, 1, "tracker-token")
            return {
                "reencrypted": 1,
                "active_key_id": "new",
                "remaining_key_ids": {"new": 1},
            }

        def close(self) -> None:
            self.closed = True

    sentinel = object()
    monkeypatch.setattr(
        "julep.execution.projection_store.PostgresExecutionStore", Store
    )
    monkeypatch.setattr(
        "julep.secrets.VaultCipher.from_env", lambda _env: sentinel
    )

    db_reencrypt_secrets(dsn="postgresql://vault")

    assert stores[0].migrated is True
    assert stores[0].closed is True
    output = capsys.readouterr().out
    assert "processed 1/1: tracker-token" in output
    assert "remaining key references: new=1" in output
