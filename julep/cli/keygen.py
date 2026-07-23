"""Development key generation for the durable local stack."""

from __future__ import annotations

import base64
import json
import os
import secrets
import shlex
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path


def generate_dev_environment(
    *,
    random_bytes: Callable[[int], bytes] = secrets.token_bytes,
) -> dict[str, str]:
    """Generate mutually independent local-only encryption and signing keys.

    The returned mapping is a supervisor input, not a shared child-process
    environment: ``julep dev up`` partitions server, publisher, and worker
    credentials by role. No value is persisted by Julep; callers choose whether
    to print it, feed a secret manager, or write a protected environment file.
    """

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "julep keygen requires cryptography; install 'julep[temporal]' or 'julep[store]'"
        ) from exc

    payload_key = random_bytes(32)
    vault_key = random_bytes(32)
    signing_seed = random_bytes(32)
    admin_api_secret = random_bytes(32)
    worker_api_secret = random_bytes(32)
    if len(payload_key) != 32 or len(vault_key) != 32 or len(signing_seed) != 32:
        raise ValueError("key generator must return exactly 32 bytes")
    if len(admin_api_secret) != 32 or len(worker_api_secret) != 32:
        raise ValueError("API token generator must return exactly 32 bytes")
    if len({payload_key, vault_key, signing_seed, admin_api_secret, worker_api_secret}) != 5:
        raise ValueError("generated development keys must be distinct")

    public_key = (
        Ed25519PrivateKey.from_private_bytes(signing_seed)
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        .hex()
    )
    admin_api_token = base64.urlsafe_b64encode(admin_api_secret).decode("ascii").rstrip("=")
    worker_api_token = base64.urlsafe_b64encode(worker_api_secret).decode("ascii").rstrip("=")
    return {
        "TEMPORAL_PAYLOAD_KEYS": f"dev={payload_key.hex()}",
        "TEMPORAL_PAYLOAD_KEY_ID": "dev",
        "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED": "true",
        "JULEP_VAULT_KEYS": f"dev={vault_key.hex()}",
        "JULEP_VAULT_KEY_ID": "dev",
        "JULEP_BUNDLE_SIGNING_KEY": signing_seed.hex(),
        "JULEP_BUNDLE_ALLOWED_SIGNERS": public_key,
        "JULEP_API_KEYS": (
            f"local-admin:{admin_api_token}:admin,local-worker:{worker_api_token}:worker"
        ),
        # The admin token drives publication and ordinary client requests. The
        # worker token is kept separate because admin credentials cannot read
        # operator-vault values and must never be handed to worker code.
        "JULEP_API_KEY": admin_api_token,
        "JULEP_WORKER_API_KEY": worker_api_token,
    }


def render_dev_environment(
    values: Mapping[str, str],
    *,
    format: str = "env",
) -> str:
    """Render generated keys as shell exports or a JSON object."""

    if format == "json":
        return json.dumps(dict(values), indent=2, sort_keys=True) + "\n"
    if format != "env":
        raise ValueError("key output format must be 'env' or 'json'")
    return "".join(f"export {name}={shlex.quote(value)}\n" for name, value in values.items())


def write_private_file(path: str | Path, content: str, *, replace: bool = False) -> None:
    """Write a mode-0600 secret file, atomically replacing only when requested."""

    destination = Path(path)
    if not replace:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(destination, flags, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                descriptor = -1
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            if descriptor >= 0:
                os.close(descriptor)
            try:
                destination.unlink()
            except OSError:
                pass
            raise
        return

    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


__all__ = ["generate_dev_environment", "render_dev_environment", "write_private_file"]
