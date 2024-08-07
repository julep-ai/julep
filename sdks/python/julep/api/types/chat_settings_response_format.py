# This file was auto-generated by Fern from our API Definition.

import datetime as dt
import typing

from ..core.datetime_utils import serialize_datetime
from .chat_settings_response_format_schema import ChatSettingsResponseFormatSchema
from .chat_settings_response_format_type import ChatSettingsResponseFormatType

try:
    import pydantic.v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore


class ChatSettingsResponseFormat(pydantic.BaseModel):
    """
    An object specifying the format that the model must output.

    Setting to `{ "type": "json_object" }` enables JSON mode, which guarantees the message the model generates is valid JSON.

    **Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly "stuck" request. Also note that the message content may be partially cut off if `finish_reason="length"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.
    """

    type: typing.Optional[ChatSettingsResponseFormatType] = pydantic.Field(
        description='Must be one of `"text"`, `"regex"` or `"json_object"`.'
    )
    pattern: typing.Optional[str] = pydantic.Field(
        description='Regular expression pattern to use if `type` is `"regex"`'
    )
    schema_: typing.Optional[ChatSettingsResponseFormatSchema] = pydantic.Field(
        alias="schema", description='JSON Schema to use if `type` is `"json_object"`'
    )

    def json(self, **kwargs: typing.Any) -> str:
        kwargs_with_defaults: typing.Any = {
            "by_alias": True,
            "exclude_unset": True,
            **kwargs,
        }
        return super().json(**kwargs_with_defaults)

    def dict(self, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]:
        kwargs_with_defaults: typing.Any = {
            "by_alias": True,
            "exclude_unset": True,
            **kwargs,
        }
        return super().dict(**kwargs_with_defaults)

    class Config:
        frozen = True
        smart_union = True
        allow_population_by_field_name = True
        json_encoders = {dt.datetime: serialize_datetime}
