"""Tests for the blob-durability contract (design note "The blob-durability
contract"). The store is pure (no Temporal); async methods are driven via
``asyncio.run`` inside sync test functions — the repo has no asyncio pytest
plugin (see tests/test_e2e_temporal.py for the pattern).
"""

from __future__ import annotations

import asyncio
import hashlib

import pytest

from julep.execution.blobstore import (
    HASH_ALGO,
    BlobImmutabilityError,
    BlobIntegrityError,
    BlobNotFound,
    BlobTenantError,
    InMemoryBlobStore,
    content_ref,
    parse_ref,
)


def test_hash_algo_is_sha256() -> None:
    assert HASH_ALGO == "sha256"


def test_content_ref_format() -> None:
    data = b"hello world"
    digest = hashlib.sha256(data).hexdigest()
    ref = content_ref("acme", data)
    assert ref == f"acme/sha256:{digest}"


def test_content_ref_rejects_empty_tenant() -> None:
    with pytest.raises(BlobTenantError):
        content_ref("", b"x")


def test_content_ref_rejects_tenant_with_slash() -> None:
    with pytest.raises(BlobTenantError):
        content_ref("ac/me", b"x")


def test_parse_ref_round_trip() -> None:
    ref = content_ref("acme", b"payload")
    tenant, digest = parse_ref(ref)
    assert tenant == "acme"
    assert digest == "sha256:" + hashlib.sha256(b"payload").hexdigest()
    # Reassembling from the parts yields the original ref.
    assert f"{tenant}/{digest}" == ref


@pytest.mark.parametrize(
    "bad",
    [
        "no-slash-or-colon",
        "acme/md5:deadbeef",  # wrong algo
        "acme/sha256",  # missing :hex
        "/sha256:abcd",  # empty tenant
        "acme/sha256:",  # empty hex
        "",
    ],
)
def test_parse_ref_malformed_raises(bad: str) -> None:
    with pytest.raises(BlobTenantError):
        parse_ref(bad)


def test_put_get_byte_round_trip() -> None:
    store = InMemoryBlobStore()
    data = b"the quick brown fox"

    async def go() -> bytes:
        ref = await store.put("acme", data)
        assert ref == content_ref("acme", data)
        return await store.get("acme", ref)

    assert asyncio.run(go()) == data


def test_identical_bytes_dedup() -> None:
    store = InMemoryBlobStore()
    data = b"dedup me"

    async def go() -> tuple[str, str]:
        ref1 = await store.put("acme", data)
        ref2 = await store.put("acme", data)
        return ref1, ref2

    ref1, ref2 = asyncio.run(go())
    assert ref1 == ref2
    # Dedup: only one backing entry for identical bytes.
    assert len(store._blobs) == 1


def test_immutability_violation_raises() -> None:
    store = InMemoryBlobStore()
    data = b"original"
    ref = asyncio.run(store.put("acme", data))
    # Forge a collision: same ref, different bytes, by poking the backing dict.
    store._blobs[ref] = b"tampered-different-length"

    async def go() -> None:
        await store.put("acme", data)

    with pytest.raises(BlobImmutabilityError):
        asyncio.run(go())


def test_integrity_violation_raises() -> None:
    store = InMemoryBlobStore()
    data = b"trustworthy"
    ref = asyncio.run(store.put("acme", data))
    # Corrupt the stored bytes via the test seam (the backing dict).
    store._blobs[ref] = b"corrupted"

    async def go() -> bytes:
        return await store.get("acme", ref)

    with pytest.raises(BlobIntegrityError):
        asyncio.run(go())


def test_tenant_mismatch_raises() -> None:
    store = InMemoryBlobStore()
    ref = asyncio.run(store.put("acme", b"secret"))

    async def go() -> bytes:
        # A different tenant must not read acme's blob by presenting acme's ref.
        return await store.get("other", ref)

    with pytest.raises(BlobTenantError):
        asyncio.run(go())


def test_missing_ref_raises_not_found() -> None:
    store = InMemoryBlobStore()
    absent = content_ref("acme", b"never-stored")

    async def go() -> bytes:
        return await store.get("acme", absent)

    with pytest.raises(BlobNotFound):
        asyncio.run(go())
