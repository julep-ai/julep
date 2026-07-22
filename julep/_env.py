"""Canonical environment-variable names used by Julep.

This module is intentionally stdlib-only so importing a name does not pull in
any optional runtime dependencies.  Legacy names are data for migration
diagnostics only: callers always read the canonical names and never fall back.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from types import MappingProxyType
from typing import Final, overload

JULEP_BUNDLE_SIGNING_KEY: Final = "JULEP_BUNDLE_SIGNING_KEY"
JULEP_BUNDLE_ALLOWED_SIGNERS: Final = "JULEP_BUNDLE_ALLOWED_SIGNERS"
JULEP_BUNDLES: Final = "JULEP_BUNDLES"
JULEP_BUNDLE_NATIVE_EXEC: Final = "JULEP_BUNDLE_NATIVE_EXEC"
JULEP_PURE_NATIVE_DEPS: Final = "JULEP_PURE_NATIVE_DEPS"
JULEP_WORKER_BUILD_ID: Final = "JULEP_WORKER_BUILD_ID"
JULEP_WORKER_VERSIONING: Final = "JULEP_WORKER_VERSIONING"
JULEP_BATCH_RESULT_TIMEOUT_S: Final = "JULEP_BATCH_RESULT_TIMEOUT_S"
JULEP_ENV: Final = "JULEP_ENV"
JULEP_SOURCE_CAPTURE: Final = "JULEP_SOURCE_CAPTURE"
JULEP_NATIVE_VENV_CACHE_DIR: Final = "JULEP_NATIVE_VENV_CACHE_DIR"
JULEP_WASM_FUEL: Final = "JULEP_WASM_FUEL"
JULEP_WASM_CACHE_DIR: Final = "JULEP_WASM_CACHE_DIR"
JULEP_WASM_EPOCH_MS: Final = "JULEP_WASM_EPOCH_MS"
JULEP_API_URL: Final = "JULEP_API_URL"
JULEP_API_KEY: Final = "JULEP_API_KEY"
JULEP_ARTIFACT_STORE_URL: Final = "JULEP_ARTIFACT_STORE_URL"

LEGACY_ENV_VAR_RENAMES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "CA_BUNDLE_SIGNING_KEY": JULEP_BUNDLE_SIGNING_KEY,
        "CA_BUNDLE_ALLOWED_SIGNERS": JULEP_BUNDLE_ALLOWED_SIGNERS,
        "CA_BUNDLES": JULEP_BUNDLES,
        "CA_BUNDLE_NATIVE_EXEC": JULEP_BUNDLE_NATIVE_EXEC,
        "CA_PURE_NATIVE_DEPS": JULEP_PURE_NATIVE_DEPS,
        "CA_WORKER_BUILD_ID": JULEP_WORKER_BUILD_ID,
        "CA_WORKER_VERSIONING": JULEP_WORKER_VERSIONING,
        "CA_BATCH_RESULT_TIMEOUT_S": JULEP_BATCH_RESULT_TIMEOUT_S,
        "CA_ENV": JULEP_ENV,
        "JULEP_CAS_URL": JULEP_ARTIFACT_STORE_URL,
        "STORE_URL": JULEP_ARTIFACT_STORE_URL,
        "COMPOSABLE_AGENTS_SOURCE_CAPTURE": JULEP_SOURCE_CAPTURE,
        "COMPOSABLE_NATIVE_VENV_CACHE_DIR": JULEP_NATIVE_VENV_CACHE_DIR,
        "COMPOSABLE_WASM_FUEL": JULEP_WASM_FUEL,
        "COMPOSABLE_WASM_CACHE_DIR": JULEP_WASM_CACHE_DIR,
        "COMPOSABLE_WASM_EPOCH_MS": JULEP_WASM_EPOCH_MS,
    }
)

CANONICAL_ENV_VAR_NAMES: Final[frozenset[str]] = frozenset(
    LEGACY_ENV_VAR_RENAMES.values()
)


@overload
def get(
    name: str,
    default: str,
    *,
    environ: Mapping[str, str] | None = None,
) -> str: ...


@overload
def get(
    name: str,
    default: None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> str | None: ...


def get(
    name: str,
    default: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Read a canonical variable from an explicit or process environment."""

    source = os.environ if environ is None else environ
    return source.get(name, default)


def set_default(
    name: str,
    value: str,
    *,
    environ: MutableMapping[str, str] | None = None,
) -> str:
    """Set a canonical process variable only when it is currently absent."""

    target = os.environ if environ is None else environ
    return target.setdefault(name, value)


def snapshot(*, environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return a detached copy of an explicit or process environment."""

    source = os.environ if environ is None else environ
    return dict(source)


__all__ = [
    "CANONICAL_ENV_VAR_NAMES",
    "JULEP_API_KEY",
    "JULEP_API_URL",
    "JULEP_ARTIFACT_STORE_URL",
    "JULEP_BATCH_RESULT_TIMEOUT_S",
    "JULEP_BUNDLES",
    "JULEP_BUNDLE_ALLOWED_SIGNERS",
    "JULEP_BUNDLE_NATIVE_EXEC",
    "JULEP_BUNDLE_SIGNING_KEY",
    "JULEP_ENV",
    "JULEP_NATIVE_VENV_CACHE_DIR",
    "JULEP_PURE_NATIVE_DEPS",
    "JULEP_SOURCE_CAPTURE",
    "JULEP_WASM_CACHE_DIR",
    "JULEP_WASM_EPOCH_MS",
    "JULEP_WASM_FUEL",
    "JULEP_WORKER_BUILD_ID",
    "JULEP_WORKER_VERSIONING",
    "LEGACY_ENV_VAR_RENAMES",
    "get",
    "set_default",
    "snapshot",
]
