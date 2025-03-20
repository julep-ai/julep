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
from pydantic import BaseModel, ConfigDict
from temporalio import workflow
from temporalio.api.common.v1 import Payload
from temporalio.converter import (
    CompositePayloadConverter,
    DefaultPayloadConverter,
    EncodingPayloadConverter,
)

with workflow.unsafe.imports_passed_through():
    from ..clients import sync_s3
    from ..common.utils.memory import total_size
    from ..env import blob_store_bucket, debug, testing
    from ..exceptions import FailedDecodingSentinel, FailedEncodingSentinel


class RemoteObject(BaseModel):
    key: str
    bucket: str
    model_config = ConfigDict(frozen=True)

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
    """
    Serialize an object using pickle and compress with lz4.

    Args:
        x: The object to serialize

    Returns:
        Compressed serialized bytes

    Raises:
        Exception: If serialization fails
    """
    start_time = time.time()

    try:
        # First pickle the object
        pickled = pickle.dumps(x, protocol=-1)

        # Then compress the pickled data
        compressed = compress(pickled)

        # Log timing for large objects
        duration = time.time() - start_time
        if duration > 1:
            # Use pickled size as a more accurate measure of the object's true size
            original_size = len(pickled) / 1000
            compressed_size = len(compressed) / 1000

            # Safely calculate compression ratio to avoid division by zero
            if len(compressed) > 0:
                compression_ratio = f"{len(pickled) / len(compressed):.2f}x"
            else:
                compression_ratio = "N/A"

            # Use proper logger instead of print statements
            logging.info(
                f"||| [SERIALIZE] Time: {duration:.2f}s | Original: {original_size:.2f}kb | "
                f"Compressed: {compressed_size:.2f}kb | Ratio: {compression_ratio}"
            )

        return compressed
    except Exception as e:
        logging.error(
            f"||| [SERIALIZE ERROR] Failed to serialize object of type {type(x).__name__}: {e!s}"
        )
        raise


def deserialize(b: bytes) -> Any:
    """
    Deserialize a compressed pickle object.

    Args:
        b: Compressed serialized bytes

    Returns:
        The deserialized object

    Raises:
        Exception: If deserialization fails
    """
    start_time = time.time()

    try:
        # First decompress the data
        decompressed = decompress(b)

        # Then unpickle to get the original object
        obj = pickle.loads(decompressed)

        # Log timing for large objects
        duration = time.time() - start_time
        if duration > 1:
            compressed_size = len(b) / 1000
            decompressed_size = len(decompressed) / 1000
            obj_size = total_size(obj) / 1000

            logging.info(
                f"||| [DESERIALIZE] Time: {duration:.2f}s | Compressed: {compressed_size:.2f}kb | "
                f"Decompressed: {decompressed_size:.2f}kb | Object: {obj_size:.2f}kb | Type: {type(obj).__name__}"
            )

        return obj
    except Exception as e:
        logging.error(f"||| [DESERIALIZE ERROR] Failed to deserialize: {e!s}")
        raise


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
            # In debug/testing mode, we want to see the full error
            if debug or testing:
                raise e

            # Create a more detailed log message with payload metadata
            payload_size = len(payload.data) if payload.data else 0
            metadata_str = ", ".join(f"{k}={v}" for k, v in payload.metadata.items())

            logging.warning(
                f"Failed to decode payload: {e!s}\n"
                f"Payload size: {payload_size} bytes\n"
                f"Metadata: {metadata_str}\n"
                f"Type hint: {type_hint.__name__ if type_hint else 'None'}"
            )

            # Return sentinel object that must be handled by the caller
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
