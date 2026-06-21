from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pytest

from composable_agents.cas import CASStore, LocalDirCAS
from composable_agents.gc import GCError, Lease, LeaseStore, gc, reachable_closure
from composable_agents.ir import canonical_json


@dataclass(frozen=True)
class _BundleFixture:
    bundle_hash: str
    signature_digest: str
    artifact_components: str
    flow: str
    source: str
    env_component: str
    env_hash: str

    @property
    def closure(self) -> set[str]:
        return {
            self.bundle_hash,
            self.signature_digest,
            self.artifact_components,
            self.flow,
            self.source,
            self.env_component,
        }


def _canonical_bytes(value: object) -> bytes:
    return canonical_json(value).encode("utf-8")


def _hex_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _make_bundle(store: CASStore) -> _BundleFixture:
    source_text = "def useful_pure(value: int) -> int:\n    return value + 1\n"
    source = store.put(source_text.encode("utf-8"))
    env_component = store.put(b"wasm env component bytes")
    flow = store.put(_canonical_bytes({"kind": "call", "pure": "useful_pure"}))
    artifact_components = store.put(
        _canonical_bytes(
            {
                "pureSourceHashes": {
                    "useful_pure": _hex_digest(source_text.encode("utf-8")),
                }
            }
        )
    )
    env_hash = _hex_digest(b"derived env hash, not a stored CAS blob")
    manifest = {
        "artifactHash": f"sha256:{artifact_components}",
        "artifactComponents": artifact_components,
        "flow": flow,
        "pures": [
            {
                "abi": "python-source/json-v1",
                "name": "useful_pure",
                "source": source,
                "sourceHash": _hex_digest(source_text.encode("utf-8")),
                "envHash": env_hash,
                "envComponent": env_component,
            }
        ],
        "signature": None,
    }
    bundle_hash = store.put(_canonical_bytes(manifest))
    signature_digest = store.put(
        _canonical_bytes(
            {
                "algo": "ed25519",
                "bundleHash": bundle_hash,
                "publicKey": "00" * 32,
                "sig": "11" * 64,
            }
        )
    )
    return _BundleFixture(
        bundle_hash=bundle_hash,
        signature_digest=signature_digest,
        artifact_components=artifact_components,
        flow=flow,
        source=source,
        env_component=env_component,
        env_hash=env_hash,
    )


def _lease(bundle: _BundleFixture) -> Lease:
    return Lease(
        bundle_hash=bundle.bundle_hash,
        signature_digest=bundle.signature_digest,
        name="test bundle",
    )


def _snapshot(store: LocalDirCAS, digests: set[str]) -> dict[str, bytes]:
    return {digest: store.get(digest) for digest in sorted(digests) if store.has(digest)}


def test_lease_pins_whole_bundle_closure(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    lease_store = LeaseStore(tmp_path)
    bundle = _make_bundle(store)
    lease_store.acquire(_lease(bundle))

    result = gc(store, lease_store, dry_run=False)

    assert result.deleted == frozenset()
    for digest in bundle.closure:
        assert store.has(digest)


def test_orphan_blob_collected_only_when_not_dry_run(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    lease_store = LeaseStore(tmp_path)
    orphan = store.put(b"orphan")

    dry = gc(store, lease_store, dry_run=True)
    assert dry.collectable == frozenset({orphan})
    assert dry.deleted == frozenset()
    assert store.has(orphan)

    collected = gc(store, lease_store, dry_run=False)
    assert collected.collectable == frozenset({orphan})
    assert collected.deleted == frozenset({orphan})
    assert not store.has(orphan)


def test_dry_run_never_deletes(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    lease_store = LeaseStore(tmp_path)
    orphan = store.put(b"dry run orphan")

    result = gc(store, lease_store)

    assert result.dry_run is True
    assert result.deleted == frozenset()
    assert result.collectable == frozenset({orphan})
    assert store.has(orphan)


def test_releasing_last_lease_makes_closure_collectable(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    lease_store = LeaseStore(tmp_path)
    bundle = _make_bundle(store)
    lease_store.acquire(_lease(bundle))

    assert gc(store, lease_store, dry_run=False).deleted == frozenset()

    lease_store.release(bundle.bundle_hash)
    result = gc(store, lease_store, dry_run=False)

    assert result.deleted == frozenset(bundle.closure)
    for digest in bundle.closure:
        assert not store.has(digest)


def test_closure_includes_env_components_and_signatures(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    bundle = _make_bundle(store)

    closure = reachable_closure(store, _lease(bundle))

    assert bundle.signature_digest in closure
    assert bundle.env_component in closure
    assert bundle.source in closure
    assert bundle.env_hash not in closure


def test_gc_is_idempotent(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    lease_store = LeaseStore(tmp_path)
    bundle = _make_bundle(store)
    lease_store.acquire(_lease(bundle))
    orphan = store.put(b"idempotent orphan")

    first = gc(store, lease_store, dry_run=False)
    surviving_before = _snapshot(store, bundle.closure)
    second = gc(store, lease_store, dry_run=False)
    surviving_after = _snapshot(store, bundle.closure)

    assert first.deleted == frozenset({orphan})
    assert second.collectable == frozenset()
    assert second.deleted == frozenset()
    assert surviving_after == surviving_before


def test_gc_fails_safe_when_closure_incomputable(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    lease_store = LeaseStore(tmp_path)
    missing_manifest = _hex_digest(b"absent manifest")
    orphan = store.put(b"would be collectable")
    lease_store.acquire(Lease(bundle_hash=missing_manifest))

    with pytest.raises(GCError):
        gc(store, lease_store, dry_run=False)

    assert store.has(orphan)


def test_lease_store_persists_across_instances(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    bundle = _make_bundle(store)
    LeaseStore(tmp_path).acquire(_lease(bundle))

    leases = LeaseStore(tmp_path).list_leases()

    assert leases == [_lease(bundle)]
