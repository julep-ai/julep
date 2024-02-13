from enum import Enum
from uuid import UUID
from typing import Literal, TypeAlias, Union
from pydantic import BaseModel, Field, ConfigDict
from vllm.entrypoints.openai.protocol import (
    CompletionRequest,
    ChatCompletionRequest,
    ChatCompletionResponseChoice,
    ChatCompletionResponseStreamChoice,
    ChatCompletionStreamResponse,
    ChatCompletionResponse,
    ChatMessage,
    DeltaMessage,
)
from .conversion.datatypes import ChatML


DEFAULT_MAX_TOKENS = 4000


class FunctionCall(BaseModel):
    name: str


RequestFunctionCall: TypeAlias = Union[Literal["none", "auto"], FunctionCall]


class ToolCall(BaseModel):
    id: str
    type: Literal["function"]
    function: str


class ChatMessage(ChatMessage):
    name: str | None = None
    function_call: str | None = None
    tool_calls: list[ToolCall] | None = None
    content: str | None = None


class DeltaMessage(DeltaMessage):
    name: str | None = None
    function_call: str | None = None
    tool_calls: list[ToolCall] | None = None


class ChatCompletionResponseChoice(ChatCompletionResponseChoice):
    message: ChatMessage
    finish_reason: Literal["stop", "length", "function_call", "tool_calls"] | None = (
        None
    )


class ChatCompletionResponseStreamChoice(ChatCompletionResponseStreamChoice):
    delta: DeltaMessage


class ChatCompletionStreamResponse(ChatCompletionStreamResponse):
    choices: list[ChatCompletionResponseStreamChoice]


class ResponseFormat(BaseModel):
    type_: str = Field(..., alias="type")


class FunctionParameters(BaseModel):
    model_config = ConfigDict(extra="allow")


class FunctionDef(BaseModel):
    name: str
    description: str | None = None
    parameters: FunctionParameters


class ToolType(Enum):
    function = "function"


class NamedToolChoice(BaseModel):
    type: ToolType
    function: FunctionCall


ToolChoice: TypeAlias = Union[Literal["none", "auto"], NamedToolChoice]


class Type(Enum):
    function = "function"
    webhook = "webhook"


class Tool(BaseModel):
    type: Type
    function: FunctionDef
    id: str


class ChatCompletionRequest(ChatCompletionRequest):
    model_config = ConfigDict(extra="forbid")

    functions: list[FunctionDef] | None = None
    function_call: RequestFunctionCall | None = None
    tools: list[Tool] | None = None
    tool_choice: ToolChoice | None = None
    response_format: ResponseFormat | None = None
    max_tokens: int | None = DEFAULT_MAX_TOKENS
    spaces_between_special_tokens: bool | None = False
    messages: ChatML
    temperature: float | None = 0.0


class CompletionRequest(CompletionRequest):
    model_config = ConfigDict(extra="forbid")

    spaces_between_special_tokens: bool | None = False
    temperature: float | None = 0.0


class ChatCompletionResponse(ChatCompletionResponse):
    choices: list[ChatCompletionResponseChoice]
