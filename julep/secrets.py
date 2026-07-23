"""Vault-lite encryption, ``secret://`` resolution, and value scrubbing.

The vault keyring is deliberately separate from Temporal payload encryption.
Ciphertext authenticates the immutable secret name and its generation so a row
or an older version cannot be replayed under another identity.
"""

from __future__ import annotations

import base64
import copy
import json
import logging
import os
import re
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, quote_plus
from urllib.request import Request, urlopen


SECRET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
SECRET_REF_RE = re.compile(r"^secret://([a-z0-9][a-z0-9_-]{0,63})$")
MAX_RUN_SECRETS = 32
MAX_RUN_SECRET_VALUE_BYTES = 16 * 1024
MAX_RUN_SECRETS_TOTAL_BYTES = 64 * 1024
_KEY_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_VAULT_AAD_PREFIX = b"julep/vault/aes-256-gcm/v1"
REDACTED = "[REDACTED]"
logger = logging.getLogger("julep.secrets")

Redactor = Callable[[Any], Any]
SecretFetcher = Callable[[str, str, float], Mapping[str, Any]]


class VaultConfigurationError(ValueError):
    """The dedicated vault keyring or active key selection is invalid."""


class SecretResolutionError(RuntimeError):
    """A logical secret could not be resolved without falling open."""

    def __init__(self, name: str, attempts: Iterable[str]) -> None:
        self.name = name
        self.attempts = tuple(attempts)
        super().__init__(
            f"secret {name!r} could not be resolved; tried "
            + "; ".join(self.attempts)
        )


class SecretFetchError(RuntimeError):
    """Typed control-plane failure used by the resolver's stale policy."""

    def __init__(self, detail: str, *, transient: bool, status_code: int | None = None):
        super().__init__(detail)
        self.transient = transient
        self.status_code = status_code


def validate_secret_name(name: str) -> str:
    """Validate and return one immutable logical vault name."""

    if SECRET_NAME_RE.fullmatch(name) is None:
        raise ValueError(
            "secret names must match ^[a-z0-9][a-z0-9_-]{0,63}$"
        )
    return name


def validate_run_secrets(
    secrets: Mapping[str, str] | None,
) -> dict[str, str]:
    """Validate the bounded caller-supplied map accepted by every start path."""

    if not secrets:
        return {}
    if not isinstance(secrets, Mapping):
        raise ValueError("run secrets must be a name-to-value mapping")
    if len(secrets) > MAX_RUN_SECRETS:
        raise ValueError(f"run secrets are limited to {MAX_RUN_SECRETS} entries")

    validated: dict[str, str] = {}
    total_bytes = 0
    for name, value in secrets.items():
        if not isinstance(name, str) or SECRET_NAME_RE.fullmatch(name) is None:
            raise ValueError(f"invalid run secret name: {name!r}")
        if not isinstance(value, str) or not value:
            raise ValueError(f"run secret value must be non-empty: {name}")
        try:
            name_bytes = name.encode("utf-8")
            value_bytes = value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError(f"run secret value must be valid UTF-8: {name}") from exc
        if len(value_bytes) > MAX_RUN_SECRET_VALUE_BYTES:
            raise ValueError(
                f"run secret value exceeds {MAX_RUN_SECRET_VALUE_BYTES} bytes: {name}"
            )
        total_bytes += len(name_bytes) + len(value_bytes)
        validated[name] = value
    if total_bytes > MAX_RUN_SECRETS_TOTAL_BYTES:
        raise ValueError(
            f"run secrets exceed the {MAX_RUN_SECRETS_TOTAL_BYTES}-byte total limit"
        )
    return validated


def parse_vault_keyring(value: str) -> dict[str, bytes]:
    """Parse ``key-id=64hex`` entries from ``JULEP_VAULT_KEYS``."""

    keys: dict[str, bytes] = {}
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        key_id, separator, raw_key = item.partition("=")
        key_id = key_id.strip()
        raw_key = raw_key.strip()
        if not separator or not key_id or not raw_key:
            raise VaultConfigurationError(
                "JULEP_VAULT_KEYS must use key-id=64hex entries separated by commas"
            )
        if _KEY_ID_RE.fullmatch(key_id) is None:
            raise VaultConfigurationError(
                "vault key IDs must contain only letters, digits, dot, underscore, or hyphen"
            )
        if key_id in keys:
            raise VaultConfigurationError(f"duplicate vault key ID {key_id!r}")
        if len(raw_key) != 64:
            raise VaultConfigurationError(
                f"AES-256-GCM vault key {key_id!r} must be 64 hexadecimal characters"
            )
        try:
            decoded = bytes.fromhex(raw_key)
        except ValueError as exc:
            raise VaultConfigurationError(
                f"AES-256-GCM vault key {key_id!r} is not hexadecimal"
            ) from exc
        if len(decoded) != 32:  # defensive; 64 valid hex chars imply this
            raise VaultConfigurationError(
                f"AES-256-GCM vault key {key_id!r} must contain exactly 32 bytes"
            )
        keys[key_id] = decoded
    if not keys:
        raise VaultConfigurationError("vault keyring is empty")
    return keys


class VaultCipher:
    """Encrypt and decrypt UTF-8 secret values with name/generation AAD."""

    def __init__(
        self,
        keys: Mapping[str, bytes | str],
        *,
        active_key_id: str,
    ) -> None:
        if not active_key_id:
            raise VaultConfigurationError("JULEP_VAULT_KEY_ID must be non-empty")
        materialized: dict[str, bytes] = {}
        for key_id, value in keys.items():
            if isinstance(value, str):
                parsed = parse_vault_keyring(f"{key_id}={value}")
                materialized[key_id] = parsed[key_id]
            else:
                raw = bytes(value)
                if _KEY_ID_RE.fullmatch(key_id) is None or len(raw) != 32:
                    raise VaultConfigurationError(
                        f"invalid AES-256-GCM vault key {key_id!r}"
                    )
                materialized[key_id] = raw
        if active_key_id not in materialized:
            raise VaultConfigurationError(
                f"active vault key ID {active_key_id!r} is not present in JULEP_VAULT_KEYS"
            )
        self._keys = materialized
        self.active_key_id = active_key_id

    @classmethod
    def from_env(
        cls, env: Optional[Mapping[str, str]] = None
    ) -> "VaultCipher":
        source = os.environ if env is None else env
        raw_keys = source.get("JULEP_VAULT_KEYS")
        active_key_id = source.get("JULEP_VAULT_KEY_ID")
        if not raw_keys or not active_key_id:
            raise VaultConfigurationError(
                "JULEP_VAULT_KEYS and JULEP_VAULT_KEY_ID must be set together"
            )
        keys = parse_vault_keyring(raw_keys)
        payload_keys = source.get("TEMPORAL_PAYLOAD_KEYS")
        if payload_keys:
            from ._payload_encryption import parse_aes_gcm_keyring

            payload_material = {
                bytes.fromhex(value)
                for value in parse_aes_gcm_keyring(payload_keys).values()
            }
            if payload_material & set(keys.values()):
                raise VaultConfigurationError(
                    "vault and Temporal payload encryption must use distinct key material"
                )
        return cls(keys, active_key_id=active_key_id)

    @property
    def key_ids(self) -> frozenset[str]:
        return frozenset(self._keys)

    @staticmethod
    def _aad(name: str, generation: int) -> bytes:
        validate_secret_name(name)
        if generation < 1:
            raise ValueError("secret generation must be positive")
        return (
            _VAULT_AAD_PREFIX
            + b"\0"
            + name.encode("ascii")
            + b"\0"
            + str(generation).encode("ascii")
        )

    def encrypt(self, name: str, generation: int, value: str) -> tuple[bytes, str]:
        if not isinstance(value, str) or not value:
            raise ValueError("secret value must be a non-empty string")
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ModuleNotFoundError as exc:  # pragma: no cover - server extra pins it
            raise RuntimeError(
                "vault encryption requires cryptography; install 'julep[server]'"
            ) from exc
        nonce = os.urandom(12)
        key_id = self.active_key_id
        ciphertext = AESGCM(self._keys[key_id]).encrypt(
            nonce,
            value.encode("utf-8"),
            self._aad(name, generation),
        )
        return nonce + ciphertext, key_id

    def decrypt(
        self,
        name: str,
        generation: int,
        ciphertext: bytes,
        key_id: str,
    ) -> str:
        try:
            from cryptography.exceptions import InvalidTag
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ModuleNotFoundError as exc:  # pragma: no cover - server extra pins it
            raise RuntimeError(
                "vault encryption requires cryptography; install 'julep[server]'"
            ) from exc
        key = self._keys.get(key_id)
        if key is None:
            raise VaultConfigurationError(
                f"secret references unavailable vault key ID {key_id!r}"
            )
        envelope = bytes(ciphertext)
        if len(envelope) < 29:
            raise VaultConfigurationError("vault ciphertext is truncated")
        try:
            raw = AESGCM(key).decrypt(
                envelope[:12],
                envelope[12:],
                self._aad(name, generation),
            )
        except InvalidTag as exc:
            raise VaultConfigurationError(
                f"vault ciphertext authentication failed for secret {name!r}"
            ) from exc
        try:
            return bytes(raw).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise VaultConfigurationError(
                f"vault plaintext for secret {name!r} is not UTF-8"
            ) from exc


def _variants(values: Iterable[str]) -> tuple[str, ...]:
    variants: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value:
            continue
        raw = value.encode("utf-8")
        variants.add(value)
        for encoded in (
            base64.b64encode(raw).decode("ascii"),
            base64.urlsafe_b64encode(raw).decode("ascii"),
        ):
            variants.add(encoded)
            variants.add(encoded.rstrip("="))
        for encoded in (quote(value, safe=""), quote_plus(value, safe="")):
            variants.add(encoded)
            variants.add(
                re.sub(
                    r"%[0-9A-F]{2}",
                    lambda match: match.group(0).lower(),
                    encoded,
                )
            )
    variants.discard("")
    return tuple(sorted(variants, key=lambda item: (-len(item), item)))


def _scrub_with_variants(value: Any, variants: tuple[str, ...]) -> Any:
    if isinstance(value, str):
        scrubbed = value
        for secret in variants:
            scrubbed = scrubbed.replace(secret, REDACTED)
        return scrubbed
    if isinstance(value, Mapping):
        scrubbed_mapping: dict[Any, Any] = {}
        collided: set[Any] = set()
        for key, child in value.items():
            scrubbed_key = (
                _scrub_with_variants(key, variants)
                if isinstance(key, str)
                else copy.deepcopy(key)
            )
            if scrubbed_key in collided:
                continue
            if scrubbed_key in scrubbed_mapping:
                # Multiple secret-bearing spellings can collapse to the same
                # redacted key. Drop every colliding entry rather than retain
                # one caller-controlled value nondeterministically.
                scrubbed_mapping.pop(scrubbed_key, None)
                collided.add(scrubbed_key)
                continue
            scrubbed_mapping[scrubbed_key] = _scrub_with_variants(child, variants)
        return scrubbed_mapping
    if isinstance(value, tuple):
        return [_scrub_with_variants(child, variants) for child in value]
    if isinstance(value, list):
        return [_scrub_with_variants(child, variants) for child in value]
    return copy.deepcopy(value)


def scrubber_for_values(
    values: Iterable[str],
    *,
    base: Redactor | None = None,
) -> Redactor:
    """Build a redactor for exact, base64, and URL-encoded value echoes.

    ``base`` runs first, preserving the existing key/path-pattern floor.  The
    returned callable owns an immutable snapshot and is therefore safe for a
    run-scoped scrubber without global registration.
    """

    variants = _variants(values)

    def redact(value: Any) -> Any:
        prepared = value if base is None else base(value)
        return _scrub_with_variants(prepared, variants)

    return redact


class DynamicSecretScrubber:
    """Process-wide registry for operator/env values resolved by this process."""

    def __init__(self) -> None:
        self._values: set[str] = set()
        self._variants: tuple[str, ...] = ()
        self._lock = threading.RLock()

    def register(self, value: str) -> None:
        if not value:
            return
        with self._lock:
            if value in self._values:
                return
            self._values.add(value)
            self._variants = _variants(self._values)

    def redact(self, value: Any, *, base: Redactor | None = None) -> Any:
        prepared = value if base is None else base(value)
        with self._lock:
            variants = self._variants
        return _scrub_with_variants(prepared, variants)

    def compose(self, base: Redactor | None = None) -> Redactor:
        return lambda value: self.redact(value, base=base)


GLOBAL_SECRET_SCRUBBER = DynamicSecretScrubber()


def register_secret_value(value: str) -> None:
    """Register one operator/env value with the process-wide scrubber."""

    GLOBAL_SECRET_SCRUBBER.register(value)


def operator_secret_redactor(base: Redactor | None = None) -> Redactor:
    """Compose the live process-wide operator scrubber over ``base``."""

    return GLOBAL_SECRET_SCRUBBER.compose(base)


@dataclass(frozen=True)
class ResolvedSecret:
    value: str
    generation: int | None
    source: str


@dataclass
class _CacheEntry:
    resolved: ResolvedSecret
    fetched_at: float


def _fetch_control_plane(url: str, token: str, timeout_s: float) -> Mapping[str, Any]:
    request = Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_s) as response:  # noqa: S310 - configured API URL
            payload = json.loads(response.read())
    except HTTPError as exc:
        status = int(exc.code)
        raise SecretFetchError(
            f"control plane returned HTTP {status}",
            transient=500 <= status <= 599,
            status_code=status,
        ) from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SecretFetchError(
            "control plane returned malformed JSON",
            transient=False,
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise SecretFetchError(
            f"control plane request failed ({type(exc).__name__})",
            transient=True,
        ) from exc
    if not isinstance(payload, Mapping):
        raise SecretFetchError("control plane returned a non-object", transient=False)
    return payload


class SecretResolver:
    """Resolve whole-string references from the vault or local env fallback."""

    def __init__(
        self,
        *,
        api_url: str | None = None,
        api_key: str | None = None,
        env: Optional[Mapping[str, str]] = None,
        cache_ttl_s: float = 60.0,
        stale_max_s: float = 15 * 60.0,
        timeout_s: float = 10.0,
        fetcher: SecretFetcher = _fetch_control_plane,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if cache_ttl_s < 0 or stale_max_s < cache_ttl_s or timeout_s <= 0:
            raise ValueError("invalid secret resolver TTL/timeout configuration")
        self.api_url = api_url.rstrip("/") if api_url else None
        self.api_key = api_key or None
        self.env = os.environ if env is None else env
        self.cache_ttl_s = float(cache_ttl_s)
        self.stale_max_s = float(stale_max_s)
        self.timeout_s = float(timeout_s)
        self._fetcher = fetcher
        self._clock = clock
        self._cache: dict[tuple[str, int], _CacheEntry] = {}
        self._current_generation: dict[str, int] = {}
        # Request ordering, rather than generation ordering, resolves races:
        # hard delete + recreate legitimately resets a row to generation 1.
        self._request_sequence: dict[str, int] = {}
        self._committed_sequence: dict[str, int] = {}
        self._invalidated_sequence: dict[str, int] = {}
        self._lock = threading.RLock()

    @classmethod
    def from_env(
        cls,
        env: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> "SecretResolver":
        source = os.environ if env is None else env
        return cls(
            api_url=source.get("JULEP_API_URL"),
            api_key=source.get("JULEP_API_KEY"),
            env=source,
            **kwargs,
        )

    @staticmethod
    def env_name(name: str) -> str:
        validate_secret_name(name)
        return "JULEP_SECRET_" + name.upper().replace("-", "_")

    def evict(self, name: str) -> None:
        with self._lock:
            sequence = self._request_sequence.get(name, 0) + 1
            self._request_sequence[name] = sequence
            self._invalidated_sequence[name] = sequence
            self._current_generation.pop(name, None)
            for cache_key in [key for key in self._cache if key[0] == name]:
                self._cache.pop(cache_key, None)

    def resolve(self, name: str) -> ResolvedSecret:
        validate_secret_name(name)
        attempts: list[str] = []
        now = self._clock()

        if self.api_url is not None or self.api_key is not None:
            if self.api_url is None or self.api_key is None:
                attempts.append("control plane misconfigured (URL and worker key must be paired)")
                raise SecretResolutionError(name, attempts)
            with self._lock:
                current_generation = self._current_generation.get(name)
                cached = (
                    None
                    if current_generation is None
                    else self._cache.get((name, current_generation))
                )
                if cached is not None and now - cached.fetched_at <= self.cache_ttl_s:
                    return cached.resolved
                request_sequence = self._request_sequence.get(name, 0) + 1
                self._request_sequence[name] = request_sequence

            url = f"{self.api_url}/v1/secrets/{name}/value"
            try:
                payload = self._fetcher(url, self.api_key, self.timeout_s)
                value = payload.get("value")
                generation = payload.get("generation")
                if (
                    not isinstance(value, str)
                    or not value
                    or not isinstance(generation, int)
                    or isinstance(generation, bool)
                    or generation < 1
                ):
                    raise SecretFetchError(
                        "control plane returned an invalid secret envelope",
                        transient=False,
                    )
                resolved = ResolvedSecret(
                    value=value,
                    generation=generation,
                    source="control-plane",
                )
                with self._lock:
                    invalidated_sequence = self._invalidated_sequence.get(name, 0)
                    committed_sequence = self._committed_sequence.get(name, 0)
                    current_generation = self._current_generation.get(name)
                    current = (
                        None
                        if current_generation is None
                        else self._cache.get((name, current_generation))
                    )
                    if request_sequence <= invalidated_sequence:
                        raise SecretFetchError(
                            "secret resolution was invalidated during fetch",
                            transient=False,
                        )
                    if request_sequence < committed_sequence:
                        if current is None:
                            raise SecretFetchError(
                                "secret cache request index is inconsistent",
                                transient=False,
                            )
                        resolved = current.resolved
                    else:
                        for cache_key in [key for key in self._cache if key[0] == name]:
                            self._cache.pop(cache_key, None)
                        self._cache[(name, generation)] = _CacheEntry(
                            resolved=resolved, fetched_at=now
                        )
                        self._current_generation[name] = generation
                        self._committed_sequence[name] = request_sequence
                register_secret_value(resolved.value)
                return resolved
            except SecretFetchError as exc:
                attempts.append(str(exc))
                if not exc.transient:
                    with self._lock:
                        committed_sequence = self._committed_sequence.get(name, 0)
                        current_generation = self._current_generation.get(name)
                        current = (
                            None
                            if current_generation is None
                            else self._cache.get((name, current_generation))
                        )
                        if request_sequence < committed_sequence and current is not None:
                            resolved = current.resolved
                        else:
                            self._invalidated_sequence[name] = max(
                                request_sequence,
                                self._invalidated_sequence.get(name, 0),
                            )
                            self._current_generation.pop(name, None)
                            for cache_key in [
                                key for key in self._cache if key[0] == name
                            ]:
                                self._cache.pop(cache_key, None)
                            resolved = None
                    if resolved is not None:
                        register_secret_value(resolved.value)
                        return resolved
                    raise SecretResolutionError(name, attempts) from exc
                with self._lock:
                    current_generation = self._current_generation.get(name)
                    current = (
                        None
                        if current_generation is None
                        else self._cache.get((name, current_generation))
                    )
                stale = current or cached
                if stale is not None and now - stale.fetched_at <= self.stale_max_s:
                    logger.warning(
                        "serving stale vault secret name=%s generation=%s age_seconds=%.1f",
                        name,
                        stale.resolved.generation,
                        now - stale.fetched_at,
                    )
                    return stale.resolved
                raise SecretResolutionError(name, attempts) from exc

        env_name = self.env_name(name)
        value = self.env.get(env_name)
        attempts.append(f"environment {env_name}")
        if value:
            register_secret_value(value)
            return ResolvedSecret(value=value, generation=None, source="env")
        raise SecretResolutionError(name, attempts)

    def resolve_ref(self, value: str) -> str:
        """Resolve only an entire ``secret://name`` string; pass literals through."""

        if not isinstance(value, str):
            raise TypeError("secret-capable values must be strings")
        match = SECRET_REF_RE.fullmatch(value)
        if match is None:
            if value.startswith("secret://"):
                raise ValueError(
                    "invalid secret reference; expected secret:// followed by a "
                    "lowercase logical name"
                )
            return value
        return self.resolve(match.group(1)).value


def materialize_secret_environment(
    env: Mapping[str, str],
    *,
    resolver: SecretResolver | None = None,
) -> dict[str, str]:
    """Resolve whole-string references in a worker's startup environment.

    Bootstrap variables are excluded because they are needed to reach the
    resolver itself. ``JULEP_SECRET_*`` entries are source values, not consumer
    slots. The caller decides whether to apply the returned overlay.
    """

    effective_resolver = resolver or SecretResolver.from_env(env)
    bootstrap_names = {
        "JULEP_API_KEY",
        "JULEP_API_URL",
        "JULEP_VAULT_KEYS",
        "JULEP_VAULT_KEY_ID",
    }
    return {
        name: effective_resolver.resolve_ref(value)
        for name, value in env.items()
        if name not in bootstrap_names
        and not name.startswith("JULEP_SECRET_")
        and SECRET_REF_RE.fullmatch(value) is not None
    }


__all__ = [
    "DynamicSecretScrubber",
    "GLOBAL_SECRET_SCRUBBER",
    "MAX_RUN_SECRETS",
    "MAX_RUN_SECRET_VALUE_BYTES",
    "MAX_RUN_SECRETS_TOTAL_BYTES",
    "REDACTED",
    "ResolvedSecret",
    "SECRET_NAME_RE",
    "SECRET_REF_RE",
    "SecretFetchError",
    "SecretResolutionError",
    "SecretResolver",
    "VaultCipher",
    "VaultConfigurationError",
    "operator_secret_redactor",
    "materialize_secret_environment",
    "parse_vault_keyring",
    "register_secret_value",
    "scrubber_for_values",
    "validate_run_secrets",
    "validate_secret_name",
]
