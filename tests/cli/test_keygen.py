from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from julep.bundle import bundle_signer_public_key
from julep.cli.main import app
from julep.cli.keygen import generate_dev_environment, render_dev_environment
from julep.execution.codec import parse_aes_gcm_keyring
from julep.secrets import parse_vault_keyring


def _deterministic_bytes() -> Callable[[int], bytes]:
    values = iter((b"p" * 32, b"v" * 32, b"s" * 32, b"a" * 32, b"w" * 32))

    def generate(size: int) -> bytes:
        assert size == 32
        return next(values)

    return generate


def test_generate_dev_environment_is_ready_for_api_and_worker() -> None:
    values = generate_dev_environment(random_bytes=_deterministic_bytes())
    payload = parse_aes_gcm_keyring(values["TEMPORAL_PAYLOAD_KEYS"])
    vault = parse_vault_keyring(values["JULEP_VAULT_KEYS"])
    assert payload == {"dev": "70" * 32}
    assert vault == {"dev": b"v" * 32}
    assert set(payload.values()).isdisjoint(value.hex() for value in vault.values())
    assert values["JULEP_BUNDLE_ALLOWED_SIGNERS"] == bundle_signer_public_key(
        values["JULEP_BUNDLE_SIGNING_KEY"]
    )
    admin, worker = values["JULEP_API_KEYS"].split(",")
    assert admin.split(":", 2) == [
        "local-admin",
        values["JULEP_API_KEY"],
        "admin",
    ]
    assert worker.split(":", 2) == [
        "local-worker",
        values["JULEP_WORKER_API_KEY"],
        "worker",
    ]


def test_render_dev_environment_supports_shell_and_json() -> None:
    values = {"A": "plain", "B": "has spaces"}
    assert render_dev_environment(values) == "export A=plain\nexport B='has spaces'\n"
    assert json.loads(render_dev_environment(values, format="json")) == values
    with pytest.raises(ValueError, match="env.*json"):
        render_dev_environment(values, format="yaml")


def test_generate_dev_environment_rejects_reused_random_material() -> None:
    with pytest.raises(ValueError, match="distinct"):
        generate_dev_environment(random_bytes=lambda _size: b"x" * 32)


def test_keygen_cli_prints_json_without_persisting(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["keygen", "--format", "json"])
    assert result.exit_code == 0, result.output
    values = json.loads(result.output)
    assert values["JULEP_API_KEY"]
    assert values["JULEP_WORKER_API_KEY"]
    assert list(tmp_path.iterdir()) == []


def test_keygen_cli_writes_private_file_and_refuses_implicit_overwrite(
    tmp_path,
) -> None:
    destination = tmp_path / "julep.env"
    runner = CliRunner()
    first = runner.invoke(app, ["keygen", "--output", str(destination)])
    assert first.exit_code == 0, first.output
    assert destination.stat().st_mode & 0o777 == 0o600
    original = destination.read_text(encoding="utf-8")

    second = runner.invoke(app, ["keygen", "--output", str(destination)])
    assert second.exit_code == 2
    assert "already exists" in second.output
    assert destination.read_text(encoding="utf-8") == original

    forced = runner.invoke(
        app,
        ["keygen", "--output", str(destination), "--force"],
    )
    assert forced.exit_code == 0, forced.output
    assert destination.read_text(encoding="utf-8") != original


def test_keygen_force_replaces_from_already_private_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "julep.env"
    destination.write_text("old", encoding="utf-8")
    destination.chmod(0o666)
    real_replace = os.replace
    source_modes: list[int] = []

    def checked_replace(source: str | Path, target: str | Path) -> None:
        source_modes.append(Path(source).stat().st_mode & 0o777)
        real_replace(source, target)

    monkeypatch.setattr("julep.cli.keygen.os.replace", checked_replace)

    result = CliRunner().invoke(
        app,
        ["keygen", "--output", str(destination), "--force"],
    )

    assert result.exit_code == 0, result.output
    assert source_modes == [0o600]
    assert destination.stat().st_mode & 0o777 == 0o600
