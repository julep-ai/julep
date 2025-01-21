###
# NOTE: Working with temporal's codec is really really weird
# This is a workaround to use pydantic models with temporal
# The codec is used to serialize/deserialize the data
# But this code is quite brittle. Be careful when changing it

import dataclasses
import logging
import sys
import time
from typing import Any, Self

import larch.pickle as pickle
import temporalio.converter
from lz4.frame import compress, decompress
from pydantic import BaseModel
from temporalio import workflow
from temporalio.api.common.v1 import Payload
from temporalio.converter import (
    CompositePayloadConverter,
    DefaultPayloadConverter,
    EncodingPayloadConverter,
)

with workflow.unsafe.imports_passed_through():
    from ..clients import sync_s3
    from ..env import blob_store_bucket, debug, testing
    from ..exceptions import FailedDecodingSentinel, FailedEncodingSentinel


class RemoteObject(BaseModel):
    key: str
    bucket: str

    @classmethod
    def from_value(cls, x: Any) -> Self:
        sync_s3.setup()

        serialized = serialize(x)

        key = sync_s3.add_object_with_hash(serialized)
        return RemoteObject(key=key, bucket=blob_store_bucket)

    def load(self) -> Any:
        sync_s3.setup()

        fetched = sync_s3.get_object(self.key)
        return deserialize(fetched)


def serialize(x: Any) -> bytes:
    start_time = time.time()
    pickled = pickle.dumps(x, protocol=-1)
    compressed = compress(pickled)

    duration = time.time() - start_time
    if duration > 1:
        print(
            f"||| [SERIALIZE] Time taken: {duration}s // Object size: {sys.getsizeof(x) / 1000}kb"
        )

    return compressed


def deserialize(b: bytes) -> Any:
    start_time = time.time()
    decompressed = decompress(b)
    object = pickle.loads(decompressed)

    duration = time.time() - start_time
    if duration > 1:
        print(
            f"||| [DESERIALIZE] Time taken: {duration}s // Object size: {sys.getsizeof(b) / 1000}kb"
        )

    return object


def from_payload_data(data: bytes, type_hint: type | None = None) -> Any:
    decoded = deserialize(data)

    if isinstance(decoded, RemoteObject):
        decoded = decoded.load()

    if type_hint is None:
        return decoded

    decoded_type = type(decoded)

    if (
        type_hint != decoded_type
        and hasattr(type_hint, "model_construct")
        and hasattr(decoded, "model_dump")
    ):
        try:
            decoded = type_hint(**decoded.model_dump())
        except Exception as e:
            logging.warning(f"WARNING: Could not promote {decoded_type} to {type_hint}: {e}")

    return decoded


class PydanticEncodingPayloadConverter(EncodingPayloadConverter):
    encoding = "text/pickle+lz4"
    b_encoding = encoding.encode()

    def to_payload(self, value: Any) -> Payload | None:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}".encode()

        try:
            data = serialize(value)

            return Payload(
                metadata={
                    "encoding": self.b_encoding,
                    "python_version": python_version,
                },
                data=data,
            )

        except Exception as e:
            if debug or testing:
                raise e

            # TODO: In production, we don't want to crash the workflow
            #       But the sentinel object must be handled by the caller
            logging.warning(f"WARNING: Could not encode {value}: {e}")
            # Convert the value to bytes using str() representation if needed
            error_bytes = str(value).encode("utf-8")
            return FailedEncodingSentinel(payload_data=error_bytes)

    def from_payload(self, payload: Payload, type_hint: type | None = None) -> Any:
        current_python_version = f"{sys.version_info.major}.{sys.version_info.minor}".encode()

        # Check if this is a payload we can handle
        if (
            "encoding" not in payload.metadata
            or payload.metadata["encoding"] != self.b_encoding
            or "python_version" not in payload.metadata
            or payload.metadata["python_version"] != current_python_version
        ):
            # Return the payload data as-is if we can't handle it
            return payload.data

        try:
            return from_payload_data(payload.data, type_hint)
        except Exception as e:
            if debug or testing:
                raise e

            # TODO: In production, we don't want to crash the workflow
            #       But the sentinel object must be handled by the caller
            logging.warning(f"Failed to decode payload with our encoder: {e}")
            return FailedDecodingSentinel(payload_data=payload.data)


class PydanticPayloadConverter(CompositePayloadConverter):
    def __init__(self) -> None:
        # Just add ours as first before the defaults
        super().__init__(
            PydanticEncodingPayloadConverter(),
            *DefaultPayloadConverter.default_encoding_payload_converters,
        )


# Use the default data converter, but change the payload converter.
pydantic_data_converter: Any = dataclasses.replace(
    temporalio.converter.default(),
    payload_converter_class=PydanticPayloadConverter,
)
