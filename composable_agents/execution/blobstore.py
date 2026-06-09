"""Pure blob-durability contract for Temporal-backed agent execution.

Blob stores are content-addressed, immutable, integrity-checked on read, and
tenant-scoped. Production stores must also retain blobs for at least the
workflow history retention horizon, so garbage collection never removes a blob
reachable from a non-expired Temporal history. They must encrypt blobs at rest
when payloads are sensitive.

``InMemoryBlobStore`` is only the reference implementation for tests and local
use: it has no retention or garbage-collection policy, and it does not encrypt
payloads. This module intentionally imports no ``temporalio`` symbols, keeping
the contract importable and unit-testable without Temporal installed.
"""

from __future__ import annotations

import hashlib
from typing import Protocol

HASH_ALGO = "sha256"
_SHA256_HEX_LENGTH = 64


class BlobError(Exception):
    pass


class BlobNotFound(BlobError):
    pass


class BlobIntegrityError(BlobError):
    pass


class BlobImmutabilityError(BlobError):
    pass


class BlobTenantError(BlobError):
    pass


def content_ref(tenant: str, data: bytes) -> str:
    """Return the tenant-scoped sha256 content address for ``data``."""
    if not tenant or "/" in tenant:
        raise BlobTenantError(f"invalid blob tenant: {tenant!r}")

    digest = hashlib.sha256(data).hexdigest()
    return f"{tenant}/{HASH_ALGO}:{digest}"


def parse_ref(ref: str) -> tuple[str, str]:
    """Return ``(tenant, "sha256:<hex>")`` for a valid blob ref."""
    tenant, separator, rest = ref.partition("/")
    if not separator or not tenant:
        raise BlobTenantError(f"malformed blob ref: {ref!r}")

    algo, colon, digest = rest.partition(":")
    if colon != ":" or algo != HASH_ALGO:
        raise BlobTenantError(f"malformed blob ref: {ref!r}")

    if len(digest) != _SHA256_HEX_LENGTH or not digest:
        raise BlobTenantError(f"malformed blob ref: {ref!r}")

    if any(char not in "0123456789abcdef" for char in digest):
        raise BlobTenantError(f"malformed blob ref: {ref!r}")

    return tenant, f"{HASH_ALGO}:{digest}"


class BlobStore(Protocol):
    async def put(self, tenant: str, data: bytes) -> str: ...
    async def get(self, tenant: str, ref: str) -> bytes: ...


class InMemoryBlobStore:
    """Reference BlobStore backed by a ``dict`` from ref to bytes."""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    async def put(self, tenant: str, data: bytes) -> str:
        ref = content_ref(tenant, data)
        if ref in self._blobs:
            if self._blobs[ref] == data:
                return ref
            raise BlobImmutabilityError(f"blob already exists with different bytes: {ref}")

        self._blobs[ref] = data
        return ref

    async def get(self, tenant: str, ref: str) -> bytes:
        ref_tenant, _ = parse_ref(ref)
        if ref_tenant != tenant:
            raise BlobTenantError(f"blob ref tenant {ref_tenant!r} does not match {tenant!r}")

        if ref not in self._blobs:
            raise BlobNotFound(f"blob not found: {ref}")

        stored = self._blobs[ref]
        if content_ref(tenant, stored) != ref:
            raise BlobIntegrityError(f"blob failed integrity check: {ref}")

        return stored
