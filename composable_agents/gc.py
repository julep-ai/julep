"""Lease-backed garbage collection for content-addressed bundles.

CAS stores intentionally expose no public delete API because replay depends on
immutable bundle bytes remaining available. This module is the narrow exception:
it deletes only through a private mark-sweep path after computing live roots from
persistent leases.

Only ``LocalDirCAS`` is enumerable and collectable in this implementation. S3
stores require paginated listing plus object deletes and are deliberately left
unsupported here; attempting to GC one raises ``GCError`` with an actionable
message before any deletion can occur.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

from .cas import (
    CASError,
    CASStore,
    LocalDirCAS,
    S3CAS,
    _SHA256_HEX,
    _validate_digest,
)
from .ir import canonical_json


class GCError(Exception):
    """Raised when GC cannot safely compute a complete live set."""


@dataclass(frozen=True)
class Lease:
    bundle_hash: str
    signature_digest: str | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        _validate_digest(self.bundle_hash)
        if self.signature_digest is not None:
            _validate_digest(self.signature_digest)


@dataclass(frozen=True)
class GCResult:
    reachable: frozenset[str]
    collectable: frozenset[str]
    deleted: frozenset[str]
    dry_run: bool


class LeaseStore:
    """Persistent leases stored outside the sharded CAS blob tree."""

    def __init__(self, cas_root: str | Path) -> None:
        self.cas_root = Path(cas_root)
        self.leases_root = self.cas_root / "leases"
        self.leases_root.mkdir(parents=True, exist_ok=True)

    def acquire(self, lease: Lease) -> None:
        self.leases_root.mkdir(parents=True, exist_ok=True)
        path = self._path_for(lease.bundle_hash)
        payload = {
            "bundle_hash": lease.bundle_hash,
            "signature_digest": lease.signature_digest,
            "name": lease.name,
        }
        path.write_text(canonical_json(payload), encoding="utf-8")

    def release(self, bundle_hash: str) -> None:
        _validate_digest(bundle_hash)
        try:
            self._path_for(bundle_hash).unlink()
        except FileNotFoundError:
            pass

    def list_leases(self) -> list[Lease]:
        if not self.leases_root.exists():
            return []

        leases: list[Lease] = []
        for path in sorted(self.leases_root.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                leases.append(_lease_from_json(raw))
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
                raise GCError(f"lease file is unreadable or malformed: {path}") from e
        return sorted(leases, key=lambda lease: lease.bundle_hash)

    def _path_for(self, bundle_hash: str) -> Path:
        _validate_digest(bundle_hash)
        return self.leases_root / f"{bundle_hash}.json"


def acquire_lease(cas_root: str | Path, lease: Lease) -> None:
    LeaseStore(cas_root).acquire(lease)


def release_lease(cas_root: str | Path, bundle_hash: str) -> None:
    LeaseStore(cas_root).release(bundle_hash)


def reachable_closure(store: CASStore, lease: Lease) -> set[str]:
    """Return all CAS digests reachable from a bundle lease.

    The walk uses only the unsigned manifest blob and optional signature digest.
    If the manifest cannot be read and parsed as the expected object shape, the
    closure is incomputable and GC must fail closed.
    """

    reachable = {lease.bundle_hash}
    if lease.signature_digest is not None:
        reachable.add(lease.signature_digest)

    try:
        manifest_bytes = store.get(lease.bundle_hash)
    except CASError as e:
        raise GCError(f"cannot read leased bundle manifest: {lease.bundle_hash}") from e

    try:
        manifest_raw = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise GCError(f"leased bundle manifest is not valid UTF-8 JSON: {lease.bundle_hash}") from e
    if not isinstance(manifest_raw, dict):
        raise GCError(f"leased bundle manifest must be a JSON object: {lease.bundle_hash}")

    manifest: dict[object, object] = manifest_raw
    _add_digest_if_valid(reachable, manifest.get("artifactComponents"))
    _add_digest_if_valid(reachable, manifest.get("flow"))

    pures = manifest.get("pures")
    if not isinstance(pures, list):
        raise GCError(f"leased bundle manifest pures must be a list: {lease.bundle_hash}")
    for raw_pure in pures:
        if not isinstance(raw_pure, dict):
            raise GCError(f"leased bundle manifest pure must be an object: {lease.bundle_hash}")
        pure: dict[object, object] = raw_pure
        _add_digest_if_valid(reachable, pure.get("source"))
        _add_digest_if_valid(reachable, pure.get("envComponent"))

    return reachable


def gc(store: CASStore, lease_store: LeaseStore, *, dry_run: bool = True) -> GCResult:
    """Mark-sweep CAS objects protected by active leases.

    ``dry_run`` defaults to true. If any lease closure or object enumeration
    fails, this function raises ``GCError`` before deleting anything. ``S3CAS`` is
    intentionally not implemented here; use a future S3-specific lister/deleter
    that can honor pagination and prefixes.
    """

    reachable: set[str] = set()
    for lease in lease_store.list_leases():
        # Invariant: a single incomputable lease aborts the entire sweep. A
        # partial root set is never used to decide what can be deleted.
        reachable.update(reachable_closure(store, lease))

    all_objects = _enumerate_objects(store)
    collectable = all_objects - reachable
    if dry_run:
        return GCResult(
            reachable=frozenset(reachable),
            collectable=frozenset(collectable),
            deleted=frozenset(),
            dry_run=True,
        )

    deleted: set[str] = set()
    for digest in sorted(collectable):
        _delete_object(store, digest)
        deleted.add(digest)

    return GCResult(
        reachable=frozenset(reachable),
        collectable=frozenset(collectable),
        deleted=frozenset(deleted),
        dry_run=False,
    )


def _lease_from_json(raw: object) -> Lease:
    if not isinstance(raw, dict):
        raise ValueError("lease must be a JSON object")
    bundle_hash = raw.get("bundle_hash")
    signature_digest = raw.get("signature_digest")
    name = raw.get("name")
    if not isinstance(bundle_hash, str):
        raise ValueError("lease bundle_hash must be a string")
    if signature_digest is not None and not isinstance(signature_digest, str):
        raise ValueError("lease signature_digest must be a string or null")
    if name is not None and not isinstance(name, str):
        raise ValueError("lease name must be a string or null")
    return Lease(bundle_hash=bundle_hash, signature_digest=signature_digest, name=name)


def _add_digest_if_valid(out: set[str], value: object) -> None:
    if _is_digest(value):
        out.add(value)


def _is_digest(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and _SHA256_HEX.fullmatch(value) is not None


def _enumerate_objects(store: CASStore) -> set[str]:
    if isinstance(store, LocalDirCAS):
        return _enumerate_local_objects(store)
    if isinstance(store, S3CAS):
        raise GCError(
            "S3 CAS garbage collection is not implemented; add a prefix-aware "
            "list_objects_v2/delete_object implementation before collecting S3 blobs"
        )
    raise GCError(f"CAS store type is not enumerable for GC: {type(store).__name__}")


def _enumerate_local_objects(store: LocalDirCAS) -> set[str]:
    root = store.root
    objects: set[str] = set()
    if not root.exists():
        return objects

    for first_shard in root.iterdir():
        if not first_shard.is_dir() or not _is_shard(first_shard.name):
            continue
        for second_shard in first_shard.iterdir():
            if not second_shard.is_dir() or not _is_shard(second_shard.name):
                continue
            for path in second_shard.iterdir():
                if not path.is_file() or not _is_digest(path.name):
                    continue
                objects.add(path.name)
    return objects


def _is_shard(value: str) -> bool:
    return len(value) == 2 and all(char in "0123456789abcdef" for char in value)


def _delete_object(store: CASStore, digest: str) -> None:
    if not isinstance(store, LocalDirCAS):
        raise GCError(f"CAS store type does not support GC deletion: {type(store).__name__}")
    _delete_local_object(store, digest)


def _delete_local_object(store: LocalDirCAS, digest: str) -> None:
    _validate_digest(digest)
    path = store.root / digest[:2] / digest[2:4] / digest
    try:
        path.unlink()
    except FileNotFoundError:
        return

    for directory in (path.parent, path.parent.parent):
        try:
            directory.rmdir()
        except OSError:
            pass
