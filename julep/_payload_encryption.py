"""Temporal-independent validation for payload-encryption key material."""

from __future__ import annotations

import re

_KEY_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class PayloadEncryptionError(ValueError):
    """An encrypted payload or encryption keyring is invalid."""


def parse_aes_gcm_keyring(value: str) -> dict[str, str]:
    """Parse ``key-id=64hex,key-id-2=64hex`` from a secret-backed env value."""

    keys: dict[str, str] = {}
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        key_id, separator, key = item.partition("=")
        if not separator or not key_id.strip() or not key.strip():
            raise PayloadEncryptionError(
                "TEMPORAL_PAYLOAD_KEYS must use key-id=64hex entries separated by commas"
            )
        key_id = key_id.strip()
        if key_id in keys:
            raise PayloadEncryptionError(f"duplicate payload key ID {key_id!r}")
        key = key.strip()
        decode_aes_gcm_key(key_id, key)
        keys[key_id] = key
    if not keys:
        raise PayloadEncryptionError("payload encryption keyring is empty")
    return keys


def decode_aes_gcm_key(key_id: str, value: bytes | str) -> bytes:
    """Validate and materialize one named AES-256-GCM key."""

    if _KEY_ID.fullmatch(key_id) is None:
        raise PayloadEncryptionError(
            "key IDs must contain only letters, digits, dot, underscore, or hyphen"
        )
    if isinstance(value, str):
        if len(value) != 64:
            raise PayloadEncryptionError(
                f"AES-256-GCM key {key_id!r} must be 64 hexadecimal characters"
            )
        try:
            decoded = bytes.fromhex(value)
        except ValueError as exc:
            raise PayloadEncryptionError(
                f"AES-256-GCM key {key_id!r} is not hexadecimal"
            ) from exc
    else:
        decoded = bytes(value)
    if len(decoded) != 32:
        raise PayloadEncryptionError(
            f"AES-256-GCM key {key_id!r} must contain exactly 32 bytes"
        )
    return decoded


__all__ = [
    "PayloadEncryptionError",
    "decode_aes_gcm_key",
    "parse_aes_gcm_keyring",
]
