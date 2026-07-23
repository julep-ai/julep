"""T9 — public exports on the ``julep.execution`` package.

The pure blob/session symbols (no ``temporalio`` dependency) are importable and
listed in ``__all__`` unconditionally. The Temporal-gated durable-session
symbols resolve lazily through ``__getattr__`` (mirroring the existing pattern)
and only when Temporal is installed.
"""

from __future__ import annotations

import pytest

import julep.execution as ex

PURE_SYMBOLS = [
    "BlobStore",
    "InMemoryBlobStore",
    "LocalDirBlobStore",
    "blob_store_from_url",
    "content_ref",
    "SessionStore",
    "InMemorySessionStore",
    "Cursor",
]

TEMPORAL_GATED_SYMBOLS = [
    "ClaimCheckCodec",
    "claim_check_converter",
    "loadState",
    "commitState",
    "putBlob",
    "LoadStateInput",
    "CommitStateInput",
    "PutBlobInput",
]


def test_pure_symbols_in_all_unconditionally() -> None:
    for name in PURE_SYMBOLS:
        assert name in ex.__all__, name


def test_pure_symbols_importable() -> None:
    for name in PURE_SYMBOLS:
        assert getattr(ex, name) is not None, name


def test_pure_symbols_resolve_to_real_objects() -> None:
    from julep.execution.blobstore import (
        BlobStore,
        InMemoryBlobStore,
        LocalDirBlobStore,
        blob_store_from_url,
        content_ref,
    )
    from julep.execution.session_store import (
        Cursor,
        InMemorySessionStore,
        SessionStore,
    )

    assert ex.BlobStore is BlobStore
    assert ex.InMemoryBlobStore is InMemoryBlobStore
    assert ex.LocalDirBlobStore is LocalDirBlobStore
    assert ex.blob_store_from_url is blob_store_from_url
    assert ex.content_ref is content_ref
    assert ex.SessionStore is SessionStore
    assert ex.InMemorySessionStore is InMemorySessionStore
    assert ex.Cursor is Cursor


@pytest.mark.skipif(not ex.HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_gated_symbols_listed_when_temporal_present() -> None:
    assert ex.HAVE_TEMPORAL is True
    for name in TEMPORAL_GATED_SYMBOLS:
        assert name in ex.__all__, name


@pytest.mark.skipif(not ex.HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_gated_symbols_lazy_resolve() -> None:
    assert ex.HAVE_TEMPORAL is True

    from julep.execution.activities import (
        CommitStateInput,
        LoadStateInput,
        PutBlobInput,
        commitState,
        loadState,
        putBlob,
    )
    from julep.execution.codec import ClaimCheckCodec
    from julep.execution.worker import claim_check_converter

    assert ex.ClaimCheckCodec is ClaimCheckCodec
    assert ex.claim_check_converter is claim_check_converter
    assert ex.loadState is loadState
    assert ex.commitState is commitState
    assert ex.putBlob is putBlob
    assert ex.LoadStateInput is LoadStateInput
    assert ex.CommitStateInput is CommitStateInput
    assert ex.PutBlobInput is PutBlobInput


def test_temporal_gated_attr_modules_wired() -> None:
    expected = {
        "ClaimCheckCodec": ".codec",
        "claim_check_converter": ".worker",
        "loadState": ".activities",
        "commitState": ".activities",
        "putBlob": ".activities",
        "LoadStateInput": ".activities",
        "CommitStateInput": ".activities",
        "PutBlobInput": ".activities",
    }
    for name, module in expected.items():
        assert name in ex._TEMPORAL_EXPORTS, name
        assert ex._TEMPORAL_ATTR_MODULES[name] == module, name
