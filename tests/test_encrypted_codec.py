from __future__ import annotations

import asyncio
import base64

import pytest

pytest.importorskip("temporalio")
pytest.importorskip("cryptography")

from temporalio.api.common.v1 import Payload
from temporalio.api.failure.v1 import Failure
from temporalio.converter import DefaultPayloadConverter

from julep.execution.codec import (
    AES_GCM_ENCODING,
    AES_GCM_KEY_ID,
    AesGcmPayloadCodec,
    ClaimCheckCodec,
    PayloadCodecChain,
    PayloadEncryptionError,
    data_converter_uses_aes_gcm,
    parse_aes_gcm_keyring,
)
from julep.execution.blobstore import InMemoryBlobStore
from julep.execution.worker import encrypted_payload_converter


def _payload(value):
    return DefaultPayloadConverter().to_payloads([value])[0]


def test_aes_gcm_round_trip_encrypts_data_and_metadata() -> None:
    codec = AesGcmPayloadCodec({"k1": b"a" * 32}, active_key_id="k1")
    original = _payload({"secret": "summary text"})

    async def go():
        encoded = await codec.encode([original])
        return encoded[0], (await codec.decode(encoded))[0]

    encrypted, restored = asyncio.run(go())
    assert encrypted.metadata["encoding"] == AES_GCM_ENCODING
    assert encrypted.metadata[AES_GCM_KEY_ID] == b"k1"
    assert b"summary text" not in encrypted.data
    assert restored.SerializeToString() == original.SerializeToString()


def test_key_rotation_decodes_old_payload_and_encodes_with_new_key() -> None:
    old = AesGcmPayloadCodec({"old": b"o" * 32}, active_key_id="old")
    rotated = AesGcmPayloadCodec(
        {"old": b"o" * 32, "new": b"n" * 32}, active_key_id="new"
    )
    original = _payload({"generation": 7})

    async def go():
        old_payload = (await old.encode([original]))[0]
        restored = (await rotated.decode([old_payload]))[0]
        new_payload = (await rotated.encode([original]))[0]
        return restored, new_payload

    restored, new_payload = asyncio.run(go())
    assert restored.SerializeToString() == original.SerializeToString()
    assert new_payload.metadata[AES_GCM_KEY_ID] == b"new"


def test_tamper_and_unknown_key_fail_closed() -> None:
    codec = AesGcmPayloadCodec({"k1": b"a" * 32}, active_key_id="k1")

    async def encoded():
        return (await codec.encode([_payload("secret")]))[0]

    tampered = asyncio.run(encoded())
    tampered.data = tampered.data[:-1] + bytes([tampered.data[-1] ^ 1])
    with pytest.raises(PayloadEncryptionError, match="authentication failed"):
        asyncio.run(codec.decode([tampered]))

    unavailable = asyncio.run(encoded())
    unavailable.metadata[AES_GCM_KEY_ID] = b"retired"
    with pytest.raises(PayloadEncryptionError, match="unavailable key"):
        asyncio.run(codec.decode([unavailable]))


def test_plaintext_payload_is_rejected() -> None:
    codec = AesGcmPayloadCodec({"k1": b"a" * 32}, active_key_id="k1")

    with pytest.raises(PayloadEncryptionError, match="not encrypted"):
        asyncio.run(codec.decode([_payload("plaintext")]))


def test_failure_messages_and_stacks_are_encrypted() -> None:
    converter = encrypted_payload_converter({"k1": b"a" * 32}, active_key_id="k1")
    failure = Failure()

    async def go():
        await converter.encode_failure(ValueError("secret memory text"), failure)
        encrypted = failure.SerializeToString()
        decoded = await converter.decode_failure(failure)
        return encrypted, decoded

    encrypted, decoded = asyncio.run(go())

    assert b"secret memory text" not in encrypted
    assert "secret memory text" in str(decoded)


def test_claim_checked_payload_encrypts_blob_and_wire_pointer() -> None:
    store = InMemoryBlobStore()
    secret = b"run-secret-that-must-not-leak"
    encoded_secret = base64.b64encode(secret)
    original = _payload(
        {
            "secrets": {"API_KEY": secret.decode()},
            "padding": "x" * 1024,
        }
    )
    converter = encrypted_payload_converter(
        {"k1": b"a" * 32},
        active_key_id="k1",
        blob_store=store,
        tenant="acme",
        threshold_bytes=1,
    )
    codec = converter.payload_codec
    assert codec is not None

    async def go():
        [wire_payload] = await codec.encode([original])
        [restored] = await codec.decode([wire_payload])
        return wire_payload, restored

    wire_payload, restored = asyncio.run(go())
    [(ref, blob_bytes)] = store._blobs.items()
    stored_payload = Payload.FromString(blob_bytes)
    wire_bytes = wire_payload.SerializeToString()

    assert ref.startswith("acme/sha256:")
    assert stored_payload.metadata["encoding"] == AES_GCM_ENCODING
    assert wire_payload.metadata["encoding"] == AES_GCM_ENCODING
    assert secret not in blob_bytes
    assert encoded_secret not in blob_bytes
    assert secret not in wire_bytes
    assert encoded_secret not in wire_bytes
    assert ref.encode() not in wire_bytes
    assert restored.SerializeToString() == original.SerializeToString()
    assert data_converter_uses_aes_gcm(converter)


def test_encrypted_claim_check_decodes_legacy_plaintext_blob() -> None:
    store = InMemoryBlobStore()
    keyring = {"k1": b"a" * 32}
    original = _payload({"secret": "legacy-run-secret", "padding": "x" * 1024})
    legacy_encryption = AesGcmPayloadCodec(keyring, active_key_id="k1")
    legacy_codec = PayloadCodecChain(
        [
            ClaimCheckCodec(store, tenant="acme", threshold_bytes=1),
            legacy_encryption,
        ]
    )
    current_converter = encrypted_payload_converter(
        keyring,
        active_key_id="k1",
        blob_store=store,
        tenant="acme",
        threshold_bytes=1,
    )
    current_codec = current_converter.payload_codec
    assert current_codec is not None

    async def go():
        legacy_wire = await legacy_codec.encode([original])
        return (await current_codec.decode(legacy_wire))[0]

    restored = asyncio.run(go())
    assert restored.SerializeToString() == original.SerializeToString()


def test_keyring_parser_requires_named_256_bit_hex_keys() -> None:
    assert parse_aes_gcm_keyring("old=" + "00" * 32 + ",new=" + "11" * 32) == {
        "old": "00" * 32,
        "new": "11" * 32,
    }
    with pytest.raises(PayloadEncryptionError):
        parse_aes_gcm_keyring("bad=1234")


@pytest.mark.parametrize("key_id", ["v1,bad", "v1=bad", " spaced "])
def test_codec_rejects_unsafe_key_ids(key_id: str) -> None:
    with pytest.raises(PayloadEncryptionError, match="key IDs must contain only"):
        AesGcmPayloadCodec({key_id: b"a" * 32}, active_key_id=key_id)
