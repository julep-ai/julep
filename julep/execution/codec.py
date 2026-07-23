"""Temporal payload codecs for claim checks and application encryption.

Oversized payloads are offloaded to the content-addressed BlobStore and replaced
by a tiny ``{"_ref", "_codec"}`` envelope. The size gate uses the payload's full
serialized size (data plus metadata), since Temporal enforces its limits on the
encoded payload as a whole. ``decode`` restores byte-identical originals, and
integrity errors from the blob store propagate.

``AesGcmPayloadCodec`` wraps every payload in an authenticated AES-256-GCM
envelope.  The key ID stays in clear metadata so workers can decode histories
written before a key rotation; payload metadata and data are both encrypted.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence

from temporalio.api.common.v1 import Payload
from temporalio.converter import PayloadCodec

from .._payload_encryption import (
    PayloadEncryptionError,
    decode_aes_gcm_key,
    parse_aes_gcm_keyring,
)
from .blobstore import BlobStore

REMOTE_ENCODING = b"binary/remote-codec/ext-1"
AES_GCM_ENCODING = b"binary/encrypted+aes-256-gcm/v1"
AES_GCM_KEY_ID = "encryption-key-id"


class AesGcmPayloadCodec(PayloadCodec):
    """Encrypt every payload with an active key and decode by envelope key ID."""

    def __init__(self, keys: Mapping[str, bytes | str], *, active_key_id: str) -> None:
        if not active_key_id:
            raise PayloadEncryptionError("active_key_id must be non-empty")
        materialized = {
            key_id: decode_aes_gcm_key(key_id, value)
            for key_id, value in keys.items()
        }
        if active_key_id not in materialized:
            raise PayloadEncryptionError(
                f"active key ID {active_key_id!r} is not present in the keyring"
            )
        self._keys = materialized
        self._active_key_id = active_key_id

    async def encode(self, payloads: Sequence[Payload]) -> list[Payload]:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "AES-GCM payload encryption requires cryptography; install "
                "pip install 'julep[store]'"
            ) from exc

        key_id = self._active_key_id
        aad = _encryption_aad(key_id)
        aes = AESGCM(self._keys[key_id])
        encrypted: list[Payload] = []
        for payload in payloads:
            nonce = os.urandom(12)
            ciphertext = aes.encrypt(nonce, payload.SerializeToString(), aad)
            encrypted.append(
                Payload(
                    metadata={
                        "encoding": AES_GCM_ENCODING,
                        AES_GCM_KEY_ID: key_id.encode("utf-8"),
                    },
                    data=nonce + ciphertext,
                )
            )
        return encrypted

    async def decode(self, payloads: Sequence[Payload]) -> list[Payload]:
        try:
            from cryptography.exceptions import InvalidTag
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "AES-GCM payload encryption requires cryptography; install "
                "pip install 'julep[store]'"
            ) from exc

        decoded: list[Payload] = []
        for payload in payloads:
            if payload.metadata.get("encoding") != AES_GCM_ENCODING:
                raise PayloadEncryptionError(
                    "payload is not encrypted with the required AES-256-GCM codec"
                )
            key_id_bytes = payload.metadata.get(AES_GCM_KEY_ID)
            if key_id_bytes is None:
                raise PayloadEncryptionError("encrypted payload is missing its key ID")
            try:
                key_id = key_id_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise PayloadEncryptionError("encrypted payload has an invalid key ID") from exc
            key = self._keys.get(key_id)
            if key is None:
                raise PayloadEncryptionError(
                    f"encrypted payload references unavailable key ID {key_id!r}"
                )
            if len(payload.data) < 13:
                raise PayloadEncryptionError("encrypted payload is truncated")
            nonce, ciphertext = payload.data[:12], payload.data[12:]
            try:
                raw = AESGCM(key).decrypt(nonce, ciphertext, _encryption_aad(key_id))
            except InvalidTag as exc:
                raise PayloadEncryptionError(
                    f"encrypted payload authentication failed for key ID {key_id!r}"
                ) from exc
            try:
                decoded.append(Payload.FromString(raw))
            except Exception as exc:
                raise PayloadEncryptionError("decrypted payload is malformed") from exc
        return decoded


class PayloadCodecChain(PayloadCodec):
    """Compose codecs in encode order and reverse that order while decoding."""

    def __init__(self, codecs: Sequence[PayloadCodec]) -> None:
        if not codecs:
            raise ValueError("PayloadCodecChain requires at least one codec")
        self._codecs = tuple(codecs)

    async def encode(self, payloads: Sequence[Payload]) -> list[Payload]:
        encoded = list(payloads)
        for codec in self._codecs:
            encoded = await codec.encode(encoded)
        return encoded

    async def decode(self, payloads: Sequence[Payload]) -> list[Payload]:
        decoded = list(payloads)
        for codec in reversed(self._codecs):
            decoded = await codec.decode(decoded)
        return decoded


class ClaimCheckCodec(PayloadCodec):
    def __init__(
        self,
        blob_store: BlobStore,
        *,
        tenant: str,
        threshold_bytes: int = 131072,
        blob_encryption_codec: AesGcmPayloadCodec | None = None,
    ) -> None:
        self._blob_store = blob_store
        self._tenant = tenant
        self._threshold_bytes = threshold_bytes
        self._blob_encryption_codec = blob_encryption_codec

    async def encode(self, payloads: Sequence[Payload]) -> list[Payload]:
        encoded: list[Payload] = []

        for payload in payloads:
            if payload.ByteSize() <= self._threshold_bytes:
                encoded.append(payload)
                continue

            stored_payload = payload
            if self._blob_encryption_codec is not None:
                [stored_payload] = await self._blob_encryption_codec.encode([payload])
            raw = stored_payload.SerializeToString()
            ref = await self._blob_store.put(self._tenant, raw)
            encoded.append(
                Payload(
                    metadata={"encoding": REMOTE_ENCODING},
                    data=json.dumps({"_ref": ref, "_codec": "ext/1"}).encode(),
                )
            )

        return encoded

    async def decode(self, payloads: Sequence[Payload]) -> list[Payload]:
        decoded: list[Payload] = []

        for payload in payloads:
            if payload.metadata.get("encoding") == REMOTE_ENCODING:
                env = json.loads(payload.data)
                raw = await self._blob_store.get(self._tenant, env["_ref"])
                stored_payload = Payload.FromString(raw)
                if (
                    self._blob_encryption_codec is not None
                    and stored_payload.metadata.get("encoding") == AES_GCM_ENCODING
                ):
                    [stored_payload] = await self._blob_encryption_codec.decode(
                        [stored_payload]
                    )
                decoded.append(stored_payload)
                continue

            decoded.append(payload)

        return decoded


def _encryption_aad(key_id: str) -> bytes:
    return AES_GCM_ENCODING + b"\0" + key_id.encode("utf-8")


def data_converter_uses_aes_gcm(data_converter: object) -> bool:
    """Return whether a Temporal DataConverter includes Julep AES-GCM."""

    codec = getattr(data_converter, "payload_codec", None)
    if isinstance(codec, AesGcmPayloadCodec):
        return True
    if isinstance(codec, PayloadCodecChain):
        return any(isinstance(item, AesGcmPayloadCodec) for item in codec._codecs)
    return False


__all__ = [
    "AES_GCM_ENCODING",
    "AES_GCM_KEY_ID",
    "AesGcmPayloadCodec",
    "ClaimCheckCodec",
    "PayloadCodecChain",
    "PayloadEncryptionError",
    "REMOTE_ENCODING",
    "data_converter_uses_aes_gcm",
    "parse_aes_gcm_keyring",
]
