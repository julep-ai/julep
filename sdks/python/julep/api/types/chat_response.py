# This file was auto-generated by Fern from our API Definition.

import datetime as dt
import typing

from ..core.datetime_utils import serialize_datetime
from .chat_ml_message import ChatMlMessage
from .chat_response_finish_reason import ChatResponseFinishReason
from .completion_usage import CompletionUsage
from .doc_ids import DocIds

try:
    import pydantic.v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore


class ChatResponse(pydantic.BaseModel):
    """
    Represents a chat completion response returned by model, based on the provided input.
    """

    id: str = pydantic.Field(description="A unique identifier for the chat completion.")
    finish_reason: ChatResponseFinishReason = pydantic.Field(
        description="The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function."
    )
    response: typing.List[typing.List[ChatMlMessage]] = pydantic.Field(
        description="A list of chat completion messages produced as a response."
    )
    usage: CompletionUsage
    jobs: typing.Optional[typing.List[str]] = pydantic.Field(
        description="IDs (if any) of jobs created as part of this request"
    )
    doc_ids: DocIds

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
