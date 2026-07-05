"""Tests for the claim-check Payload Codec (design note "Mechanism: the Payload
Codec is the size fix").

The codec is Temporal-bound (imports ``temporalio`` at module top), so the whole
module is skipped when Temporal is not installed. Async methods are driven via
``asyncio.run`` inside sync test functions — the repo has no asyncio pytest
plugin (see tests/test_e2e_temporal.py for the pattern). Realistic payloads are
built with Temporal's :class:`DefaultPayloadConverter`.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from julep import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.api.common.v1 import Payload
    from temporalio.converter import DefaultPayloadConverter

    from julep.execution.blobstore import (
        BlobIntegrityError,
        InMemoryBlobStore,
    )
    from julep.execution.codec import REMOTE_ENCODING, ClaimCheckCodec


THRESHOLD = 131072


def test_small_payload_passes_through_unchanged() -> None:
    store = InMemoryBlobStore()
    codec = ClaimCheckCodec(store, tenant="acme")
    [payload] = DefaultPayloadConverter().to_payloads([{"n": 1}])
    original_bytes = payload.SerializeToString()

    async def go() -> list[Payload]:
        return await codec.encode([payload])

    [encoded] = asyncio.run(go())
    # Same payload bytes, no remote marker, nothing offloaded.
    assert encoded.SerializeToString() == original_bytes
    assert encoded.metadata.get("encoding") != REMOTE_ENCODING
    assert len(store._blobs) == 0


def test_large_payload_is_offloaded() -> None:
    store = InMemoryBlobStore()
    codec = ClaimCheckCodec(store, tenant="acme")
    [payload] = DefaultPayloadConverter().to_payloads([{"blob": "x" * 200000}])
    assert payload.ByteSize() > THRESHOLD, "fixture must exceed the threshold"

    async def go() -> list[Payload]:
        return await codec.encode([payload])

    [encoded] = asyncio.run(go())
    # The encoded payload is a tiny pointer carrying the remote marker.
    assert encoded.metadata["encoding"] == REMOTE_ENCODING
    assert len(encoded.data) < THRESHOLD
    envelope = json.loads(encoded.data)
    assert envelope["_codec"] == "ext/1"
    assert "_ref" in envelope
    # Exactly one blob stored.
    assert len(store._blobs) == 1


def test_threshold_boundary_uses_full_serialized_size() -> None:
    """The gate is on the whole serialized payload (metadata included), since
    Temporal's limit applies to the full payload — not just ``payload.data``."""
    [payload] = DefaultPayloadConverter().to_payloads([{"boundary": "b" * 100}])
    full_size = payload.ByteSize()
    assert full_size > len(payload.data), "metadata must contribute to the size"
    original_bytes = payload.SerializeToString()

    # threshold == ByteSize(): passes through unchanged, nothing offloaded.
    store_at = InMemoryBlobStore()
    codec_at = ClaimCheckCodec(store_at, tenant="acme", threshold_bytes=full_size)

    async def encode_at() -> list[Payload]:
        return await codec_at.encode([payload])

    [encoded_at] = asyncio.run(encode_at())
    assert encoded_at.SerializeToString() == original_bytes
    assert encoded_at.metadata.get("encoding") != REMOTE_ENCODING
    assert len(store_at._blobs) == 0

    # threshold == ByteSize() - 1: offloaded (one blob, envelope marker present).
    store_below = InMemoryBlobStore()
    codec_below = ClaimCheckCodec(
        store_below, tenant="acme", threshold_bytes=full_size - 1
    )

    async def encode_below() -> list[Payload]:
        return await codec_below.encode([payload])

    [encoded_below] = asyncio.run(encode_below())
    assert encoded_below.metadata["encoding"] == REMOTE_ENCODING
    assert json.loads(encoded_below.data)["_codec"] == "ext/1"
    assert "_ref" in json.loads(encoded_below.data)
    assert len(store_below._blobs) == 1


def test_round_trip_small_is_byte_identical() -> None:
    store = InMemoryBlobStore()
    codec = ClaimCheckCodec(store, tenant="acme")
    value = {"hello": "world", "n": 42}
    [payload] = DefaultPayloadConverter().to_payloads([value])

    async def go() -> list[Payload]:
        return await codec.decode(await codec.encode([payload]))

    [restored] = asyncio.run(go())
    assert restored.SerializeToString() == payload.SerializeToString()
    assert DefaultPayloadConverter().from_payloads([restored]) == [value]


def test_round_trip_large_is_byte_identical() -> None:
    store = InMemoryBlobStore()
    codec = ClaimCheckCodec(store, tenant="acme")
    value = {"blob": "y" * 200000, "tag": "big"}
    [payload] = DefaultPayloadConverter().to_payloads([value])
    assert payload.ByteSize() > THRESHOLD

    async def go() -> list[Payload]:
        return await codec.decode(await codec.encode([payload]))

    [restored] = asyncio.run(go())
    # decode(encode(x)) == x, byte for byte, including metadata.
    assert restored.SerializeToString() == payload.SerializeToString()
    assert DefaultPayloadConverter().from_payloads([restored]) == [value]


def test_decode_propagates_blob_integrity_error() -> None:
    store = InMemoryBlobStore()
    codec = ClaimCheckCodec(store, tenant="acme")
    [payload] = DefaultPayloadConverter().to_payloads([{"blob": "z" * 200000}])

    async def go() -> list[Payload]:
        [encoded] = await codec.encode([payload])
        # Corrupt the one stored blob via the test seam (the backing dict).
        [(ref, _)] = list(store._blobs.items())
        store._blobs[ref] = b"corrupted-bytes"
        return await codec.decode([encoded])

    with pytest.raises(BlobIntegrityError):
        asyncio.run(go())
