"""Claim-check Payload Codec (design note "Mechanism: the Payload Codec is the size fix").

Oversized payloads are offloaded to the content-addressed BlobStore and replaced
by a tiny ``{"_ref", "_codec"}`` envelope. The size gate uses the payload's full
serialized size (data plus metadata), since Temporal enforces its limits on the
encoded payload as a whole. ``decode`` restores byte-identical originals, and
integrity errors from the blob store propagate.
"""

from __future__ import annotations

import json
from typing import Sequence

from temporalio.api.common.v1 import Payload
from temporalio.converter import PayloadCodec

from .blobstore import BlobStore

REMOTE_ENCODING = b"binary/remote-codec/ext-1"


class ClaimCheckCodec(PayloadCodec):
    def __init__(
        self,
        blob_store: BlobStore,
        *,
        tenant: str,
        threshold_bytes: int = 131072,
    ) -> None:
        self._blob_store = blob_store
        self._tenant = tenant
        self._threshold_bytes = threshold_bytes

    async def encode(self, payloads: Sequence[Payload]) -> list[Payload]:
        encoded: list[Payload] = []

        for payload in payloads:
            if payload.ByteSize() <= self._threshold_bytes:
                encoded.append(payload)
                continue

            raw = payload.SerializeToString()
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
                decoded.append(Payload.FromString(raw))
                continue

            decoded.append(payload)

        return decoded
