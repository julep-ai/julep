from __future__ import annotations

import base64
import threading
from urllib.parse import quote

import pytest

import julep.secrets as secrets_module
from julep import HAVE_TEMPORAL
from julep.execution.projection_store import InMemoryExecutionStore
from julep.secrets import (
    REDACTED,
    ResolvedSecret,
    SecretFetchError,
    SecretResolutionError,
    SecretResolver,
    VaultCipher,
    VaultConfigurationError,
    scrubber_for_values,
    validate_run_secrets,
)


def _cipher(*, active: str = "one") -> VaultCipher:
    return VaultCipher(
        {
            "one": bytes.fromhex("11" * 32),
            "two": bytes.fromhex("22" * 32),
        },
        active_key_id=active,
    )


def test_run_secret_limits_are_shared_and_byte_based() -> None:
    valid = {f"secret-{index}": "x" for index in range(32)}
    assert validate_run_secrets(valid) == valid
    with pytest.raises(ValueError, match="32 entries"):
        validate_run_secrets({**valid, "overflow": "x"})
    with pytest.raises(ValueError, match="16384 bytes"):
        validate_run_secrets({"token": "é" * 8193})
    with pytest.raises(ValueError, match="65536-byte total"):
        validate_run_secrets(
            {f"token-{index}": "x" * (16 * 1024) for index in range(4)}
        )


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_build_flow_input_reuses_run_secret_limits() -> None:
    from julep.execution.harness import build_flow_input

    with pytest.raises(ValueError, match="16384 bytes"):
        build_flow_input(
            session_id="run",
            flow_json={},
            manifest_json={},
            secrets={"token": "x" * (16 * 1024 + 1)},
        )


def test_vault_cipher_authenticates_name_and_generation() -> None:
    cipher = _cipher()
    ciphertext, key_id = cipher.encrypt("tracker-token", 1, "secret-value")
    assert cipher.decrypt("tracker-token", 1, ciphertext, key_id) == "secret-value"

    with pytest.raises(VaultConfigurationError, match="authentication failed"):
        cipher.decrypt("other-token", 1, ciphertext, key_id)
    with pytest.raises(VaultConfigurationError, match="authentication failed"):
        cipher.decrypt("tracker-token", 2, ciphertext, key_id)


def test_vault_cipher_env_rejects_payload_key_reuse() -> None:
    shared = "11" * 32
    with pytest.raises(VaultConfigurationError, match="distinct key material"):
        VaultCipher.from_env(
            {
                "JULEP_VAULT_KEYS": f"vault={shared}",
                "JULEP_VAULT_KEY_ID": "vault",
                "TEMPORAL_PAYLOAD_KEYS": f"payload={shared}",
            }
        )


def test_in_memory_vault_rotation_archive_and_maintenance_reencrypt() -> None:
    store = InMemoryExecutionStore()
    old = _cipher(active="one")
    first = store.put_secret("tracker-token", "first", "admin", old)
    second = store.put_secret("tracker-token", "second", "admin", old)
    store.put_secret("archived-token", "retired", "admin", old)
    store.archive_secret("archived-token", "admin")
    assert first["generation"] == 1
    assert second["generation"] == 2
    assert store.secret_key_counts() == {"one": 2}

    rotated = _cipher(active="two")
    report = store.reencrypt_secrets(rotated)
    assert report == {
        "total": 2,
        "reencrypted": 1,
        "metadata_updated": 1,
        "active_key_id": "two",
        "remaining_key_ids": {"two": 2},
    }
    row = store.get_secret("tracker-token")
    assert row is not None
    assert rotated.decrypt(
        "tracker-token", 2, row["ciphertext"], row["key_id"]
    ) == "second"

    store.create_run(
        run_id="active",
        idempotency_key="active",
        workflow_id="run-active",
        session_id="run-active",
        release_hash="sha256:" + "a" * 64,
        pipeline="summary",
        application="memory",
        principal={"key": "alice"},
        input_ref=None,
        started_at=1.0,
    )
    with pytest.raises(RuntimeError, match="non-terminal runs"):
        store.reencrypt_secrets(rotated)

    archived = store.archive_secret("tracker-token", "admin")
    assert archived is not None and archived["archived_at"] is not None
    assert store.get_secret("tracker-token")["ciphertext"] is None
    assert store.delete_secret("tracker-token") is True
    assert store.delete_secret("tracker-token") is False


def test_resolver_env_whole_string_and_fail_closed_detail() -> None:
    resolver = SecretResolver(
        env={"JULEP_SECRET_TRACKER_TOKEN": "local-secret"}
    )
    resolved = resolver.resolve("tracker-token")
    assert (resolved.value, resolved.generation, resolved.source) == (
        "local-secret",
        None,
        "env",
    )
    assert resolver.resolve_ref("secret://tracker-token") == "local-secret"
    assert resolver.resolve_ref("Bearer secret://tracker-token") == (
        "Bearer secret://tracker-token"
    )
    with pytest.raises(ValueError, match="invalid secret reference"):
        resolver.resolve_ref("secret://Uppercase")
    with pytest.raises(SecretResolutionError) as raised:
        resolver.resolve("missing")
    assert "JULEP_SECRET_MISSING" in str(raised.value)


def test_resolver_cache_stale_policy_and_terminal_eviction() -> None:
    now = [0.0]
    calls: list[str] = []
    outcomes: list[object] = [
        {"value": "remote", "generation": 7},
        SecretFetchError("unavailable", transient=True, status_code=503),
        SecretFetchError("revoked", transient=False, status_code=410),
    ]

    def fetch(url: str, token: str, timeout: float):
        assert token == "worker-token" and timeout == 1.0
        calls.append(url)
        result = outcomes.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    resolver = SecretResolver(
        api_url="https://julep.example",
        api_key="worker-token",
        env={"JULEP_SECRET_TRACKER_TOKEN": "must-not-resurrect"},
        cache_ttl_s=60,
        stale_max_s=900,
        timeout_s=1,
        fetcher=fetch,
        clock=lambda: now[0],
    )
    assert resolver.resolve("tracker-token").generation == 7
    now[0] = 30
    assert resolver.resolve("tracker-token").value == "remote"
    assert len(calls) == 1
    now[0] = 61
    assert resolver.resolve("tracker-token").value == "remote"
    now[0] = 62
    with pytest.raises(SecretResolutionError, match="revoked"):
        resolver.resolve("tracker-token")


def test_resolver_concurrent_fetch_cannot_regress_generation() -> None:
    first_started = threading.Event()
    release_first = threading.Event()
    call_lock = threading.Lock()
    calls = 0

    def fetch(_url: str, _token: str, _timeout: float):
        nonlocal calls
        with call_lock:
            calls += 1
            call = calls
        if call == 1:
            first_started.set()
            assert release_first.wait(timeout=2)
            return {"value": "old", "generation": 1}
        return {"value": "new", "generation": 2}

    resolver = SecretResolver(
        api_url="https://julep.example",
        api_key="worker-token",
        fetcher=fetch,
    )
    results: dict[str, ResolvedSecret] = {}

    def resolve_into(name: str) -> None:
        results[name] = resolver.resolve("tracker-token")

    first = threading.Thread(target=resolve_into, args=("first",))
    second = threading.Thread(target=resolve_into, args=("second",))
    first.start()
    assert first_started.wait(timeout=2)
    second.start()
    second.join(timeout=2)
    assert not second.is_alive()
    release_first.set()
    first.join(timeout=2)
    assert not first.is_alive()

    assert results["second"].generation == 2
    assert results["first"].generation == 2
    assert resolver.resolve("tracker-token").value == "new"
    assert calls == 2


def test_resolver_revocation_invalidates_older_inflight_success() -> None:
    first_started = threading.Event()
    release_first = threading.Event()
    call_lock = threading.Lock()
    calls = 0

    def fetch(_url: str, _token: str, _timeout: float):
        nonlocal calls
        with call_lock:
            calls += 1
            call = calls
        if call == 1:
            first_started.set()
            assert release_first.wait(timeout=2)
            return {"value": "revoked", "generation": 1}
        raise SecretFetchError("HTTP 410", transient=False, status_code=410)

    resolver = SecretResolver(
        api_url="https://julep.example",
        api_key="worker-token",
        fetcher=fetch,
    )
    errors: dict[str, SecretResolutionError] = {}

    def resolve_into(name: str) -> None:
        try:
            resolver.resolve("tracker-token")
        except SecretResolutionError as exc:
            errors[name] = exc

    first = threading.Thread(target=resolve_into, args=("first",))
    second = threading.Thread(target=resolve_into, args=("second",))
    first.start()
    assert first_started.wait(timeout=2)
    second.start()
    second.join(timeout=2)
    assert not second.is_alive()
    assert "HTTP 410" in str(errors["second"])
    release_first.set()
    first.join(timeout=2)
    assert not first.is_alive()
    assert "invalidated during fetch" in str(errors["first"])

    with pytest.raises(SecretResolutionError, match="HTTP 410"):
        resolver.resolve("tracker-token")
    assert calls == 3


@pytest.mark.parametrize("next_generation", [1, 2])
def test_resolver_accepts_delete_recreate_generation_reset(
    next_generation: int,
) -> None:
    now = [0.0]
    outcomes = iter(
        [
            {"value": "before-delete", "generation": 2},
            {"value": "after-recreate", "generation": next_generation},
        ]
    )
    resolver = SecretResolver(
        api_url="https://julep.example",
        api_key="worker-token",
        cache_ttl_s=60,
        fetcher=lambda *_args: next(outcomes),
        clock=lambda: now[0],
    )
    assert resolver.resolve("tracker-token").value == "before-delete"
    now[0] = 61
    recreated = resolver.resolve("tracker-token")
    assert recreated.value == "after-recreate"
    assert recreated.generation == next_generation
    assert resolver.resolve("tracker-token") == recreated


def test_control_plane_malformed_json_is_not_transient(monkeypatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self) -> bytes:
            return b"not-json"

    monkeypatch.setattr(secrets_module, "urlopen", lambda *_args, **_kwargs: Response())
    with pytest.raises(SecretFetchError) as raised:
        secrets_module._fetch_control_plane("https://julep.example", "token", 1)
    assert raised.value.transient is False


def test_scrubber_catches_raw_base64_and_urlencoded_values() -> None:
    secret = "token: value/with space"
    scrub = scrubber_for_values([secret], base=lambda value: value)
    encoded = base64.b64encode(secret.encode()).decode()
    urlencoded = quote(secret, safe="")
    assert scrub(
        {
            "raw": f"prefix {secret} suffix",
            "base64": encoded,
            "url": urlencoded,
            f"raw-key:{secret}": "one",
            f"base64-key:{encoded}": "two",
            f"url-key:{urlencoded}": "three",
            "safe": "visible",
        }
    ) == {
        "raw": f"prefix {REDACTED} suffix",
        "base64": REDACTED,
        "url": REDACTED,
        f"raw-key:{REDACTED}": "one",
        f"base64-key:{REDACTED}": "two",
        f"url-key:{REDACTED}": "three",
        "safe": "visible",
    }


def test_scrubber_drops_mapping_entries_whose_redacted_keys_collide() -> None:
    secret = "tenant-secret"
    encoded = base64.b64encode(secret.encode()).decode()
    scrub = scrubber_for_values([secret], base=lambda value: value)
    assert scrub({secret: "one", encoded: "two"}) == {}
