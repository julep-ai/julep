from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from julep import arr, deploy, pure, seq
from julep.artifact_store import LocalDirArtifactStore
from julep.execution.bundle_worker import make_context
from julep.execution.effects import WorkerContext
from julep.registry import Registry
from conftest import read_snapshot

SEED = "33" * 32


@pure("bundle.genericworker.tag.v1")
def _generic_worker_tag(value: dict[str, Any]) -> dict[str, Any]:
    return {"tag": value["name"].upper()}


def _public_key(seed: str) -> str:
    return (
        Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        .hex()
    )


def test_make_context_resolves_bundle_pures_and_returns_worker_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A generic worker resolves JULEP_BUNDLES at startup, registering bundle pures."""
    store = LocalDirArtifactStore(tmp_path)
    deployment = deploy(seq(arr("bundle.genericworker.tag.v1")), read_snapshot())
    rec = deployment.publish(store, signing_key=SEED)

    monkeypatch.setenv("JULEP_ARTIFACT_STORE_URL", f"file://{tmp_path}")
    monkeypatch.setenv("JULEP_BUNDLES", f"{rec['bundleHash']}:{rec['signatureDigest']}")
    monkeypatch.setenv("JULEP_BUNDLE_ALLOWED_SIGNERS", _public_key(SEED))

    fresh = Registry()
    context = make_context(registry=fresh)

    assert isinstance(context, WorkerContext)
    expected = deployment.artifact_components["pureSourceHashes"]
    assert (
        fresh.source_hash_of("bundle.genericworker.tag.v1")
        == expected["bundle.genericworker.tag.v1"]
    )
    # Startup resolution registers the bundle pure as the wasm tier end to end.
    assert fresh.pures["bundle.genericworker.tag.v1"].executor == "wasm"


def test_make_context_with_no_bundles_is_a_clean_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No JULEP_BUNDLES means a generic worker still starts with an empty context."""
    monkeypatch.delenv("JULEP_BUNDLES", raising=False)

    context = make_context(registry=Registry())

    assert isinstance(context, WorkerContext)
