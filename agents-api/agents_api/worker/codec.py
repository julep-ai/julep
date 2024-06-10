import dataclasses
import json
from typing import Any, Optional, Type

from pydantic import BaseModel
import temporalio.converter
from temporalio.api.common.v1 import Payload
from temporalio.converter import (
    CompositePayloadConverter,
    DefaultPayloadConverter,
    EncodingPayloadConverter,
)

model_class_map = {
    subclass.__module__ + "." + subclass.__name__: subclass
    for subclass in BaseModel.__subclasses__()
}

class PydanticEncodingPayloadConverter(EncodingPayloadConverter):
    @property
    def encoding(self) -> str:
        return "text/pydantic-json"

    def to_payload(self, value: Any) -> Optional[Payload]:
        data = value.model_dump_json().encode()

        return Payload(
            metadata={
                "encoding": self.encoding.encode(),
                "model_name": value.__class__.__name__.encode(),
                "model_module": value.__class__.__module__.encode(),
            },
            data=data,
        )

    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        model_name = payload.metadata["model_name"].decode()
        model_module = payload.metadata["model_module"].decode()
        model_class = model_class_map[model_module + "." + model_name]

        data = json.loads(payload.data.decode())

        return model_class(**data)


class PydanticPayloadConverter(CompositePayloadConverter):
    def __init__(self) -> None:
        # Just add ours as first before the defaults
        super().__init__(
            PydanticEncodingPayloadConverter(),
            *DefaultPayloadConverter.default_encoding_payload_converters
        )


# Use the default data converter, but change the payload converter.
pydantic_data_converter = dataclasses.replace(
    temporalio.converter.default(),
    payload_converter_class=PydanticPayloadConverter,
)