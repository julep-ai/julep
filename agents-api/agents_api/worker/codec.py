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

# Use this instead of the default pydantic model
import agents_api.common.protocol.tasks as tasks
import agents_api.autogen.openapi_model as openapi_model

model_class_map = {
    subclass.__module__ + "." + subclass.__name__: subclass
    for subclass in {**tasks.__dict__, **openapi_model.__dict__}.values()
    if isinstance(subclass, type) and issubclass(subclass, BaseModel)
}

model_class_map["builtins.dict"] = dict


class PydanticEncodingPayloadConverter(EncodingPayloadConverter):
    @property
    def encoding(self) -> str:
        return "text/pydantic-json"

    def to_payload(self, value: Any) -> Optional[Payload]:
        data: str = (
            value.model_dump_json()
            if hasattr(value, "model_dump_json")
            else json.dumps(value)
        )

        return Payload(
            metadata={
                "encoding": self.encoding.encode(),
                "model_name": value.__class__.__name__.encode(),
                "model_module": value.__class__.__module__.encode(),
            },
            data=data.encode(),
        )

    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        data = json.loads(payload.data.decode())

        if not isinstance(data, dict):
            return data

        # Otherwise, we have a model
        model_name = payload.metadata["model_name"].decode()
        model_module = payload.metadata["model_module"].decode()
        model_class = model_class_map[model_module + "." + model_name]

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
