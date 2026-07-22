from __future__ import annotations

import hmac

import pytest
from fastapi import HTTPException

from julep.server.auth import ApiKey, KeyRing, merge_principal, owner_scoped, parse_api_keys
from julep.server.settings import ServerSettings


def test_server_settings_overlay_and_environment_precedence(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.julep.server]
api_keys = ["config:config-token"]
execution_store_dsn = "postgresql://config"
artifact_store_url = "file:///config-artifacts"
host = "0.0.0.0"
port = 9000
temporal_namespace = "config-ns"
temporal_tls = false

[tool.julep.server.queue_by_lane]
summary = "summary-config"
""",
        encoding="utf-8",
    )
    (tmp_path / "julep.toml").write_text(
        """
[server]
host = "127.0.0.2"
projection_batch_size = 30
""",
        encoding="utf-8",
    )

    settings = ServerSettings.from_env(
        {
            "JULEP_API_KEYS": "alice:alice-token bob:bob-token:admin",
            "JULEP_EXECUTION_STORE_DSN": "postgresql://environment",
            "JULEP_SERVER_PORT": "8088",
            "TEMPORAL_TLS": "true",
            "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED": "false",
        },
        root=tmp_path,
    )

    assert [(key.name, key.admin) for key in settings.api_keys] == [
        ("alice", False),
        ("bob", True),
    ]
    assert settings.execution_store_dsn == "postgresql://environment"
    assert settings.artifact_store_url == "file:///config-artifacts"
    assert settings.host == "127.0.0.2"
    assert settings.port == 8088
    assert settings.temporal_namespace == "config-ns"
    assert settings.temporal_tls is True
    assert settings.projection_batch_size == 30
    assert settings.queue_by_lane == {"summary": "summary-config"}


def test_server_settings_require_store_only_when_built(tmp_path) -> None:
    settings = ServerSettings.from_env(
        {"TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED": "false"},
        root=tmp_path,
    )
    with pytest.raises(ValueError, match="JULEP_EXECUTION_STORE_DSN is required"):
        settings.build_store()


def test_required_payload_encryption_rejects_missing_keys(tmp_path) -> None:
    with pytest.raises(ValueError, match="payload encryption is required"):
        ServerSettings.from_env({}, root=tmp_path)
    with pytest.raises(ValueError, match="payload encryption is required"):
        ServerSettings.from_env(
            {"TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED": "true"},
            root=tmp_path,
        )


def test_api_key_parser_redacts_tokens_and_marks_admin() -> None:
    keys = parse_api_keys("alice:secret bob:more-secret:admin")
    assert keys[0].principal_base == {"key": "alice"}
    assert keys[1].admin is True
    assert "secret" not in repr(keys[0])
    with pytest.raises(ValueError, match="duplicate API key tokens"):
        parse_api_keys("alice:same bob:same")


def test_keyring_compares_every_key_and_reloads(monkeypatch: pytest.MonkeyPatch) -> None:
    keys = parse_api_keys("alice:a bob:b admin:c:admin")
    calls: list[tuple[str, str]] = []
    real_compare = hmac.compare_digest

    def compare(left: str, right: str) -> bool:
        calls.append((left, right))
        return real_compare(left, right)

    monkeypatch.setattr("julep.server.auth.hmac.compare_digest", compare)
    reloads = [parse_api_keys("new:new-token")]
    ring = KeyRing(keys, reload_source=lambda: reloads[0])

    assert ring.authenticate("b") == keys[1]
    assert calls == [("b", "a"), ("b", "b"), ("b", "c")]
    ring.reload()
    assert ring.authenticate("new-token") == reloads[0][0]
    assert ring.authenticate("b") is None


def test_principal_merge_collision_and_owner_scope() -> None:
    alice = ApiKey("alice", "a")
    admin = ApiKey("admin", "root", admin=True)
    assert merge_principal(alice, {"tenant": "one"}) == {
        "key": "alice",
        "tenant": "one",
    }
    assert merge_principal(alice, {"key": "alice"}) == {"key": "alice"}
    with pytest.raises(HTTPException) as raised:
        merge_principal(alice, {"key": "bob"})
    assert raised.value.status_code == 400

    row = {"principal": {"key": "alice", "tenant": "one"}}
    assert owner_scoped(alice, row) is True
    assert owner_scoped(ApiKey("bob", "b"), row) is False
    assert owner_scoped(admin, row) is True
