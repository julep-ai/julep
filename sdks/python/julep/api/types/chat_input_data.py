# This file was auto-generated by Fern from our API Definition.

import datetime as dt
import typing

from ..core.datetime_utils import serialize_datetime
from .chat_input_data_tool_choice import ChatInputDataToolChoice
from .input_chat_ml_message import InputChatMlMessage
from .tool import Tool

try:
    import pydantic.v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore


class ChatInputData(pydantic.BaseModel):
    messages: typing.List[InputChatMlMessage] = pydantic.Field(
        description="A list of new input messages comprising the conversation so far."
    )
    tools: typing.Optional[typing.List[Tool]] = pydantic.Field(
        description="(Advanced) List of tools that are provided in addition to agent's default set of tools. Functions of same name in agent set are overriden"
    )
    tool_choice: typing.Optional[ChatInputDataToolChoice] = pydantic.Field(
        description="Can be one of existing tools given to the agent earlier or the ones included in the request"
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
        json_encoders = {dt.datetime: serialize_datetime}
