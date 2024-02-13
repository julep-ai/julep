from typing import Literal, Optional, Union, List, Dict, Any, TypeAlias
from pydantic import BaseModel, Field
from vllm.entrypoints.openai.protocol import (
    CompletionRequest,
    ChatCompletionRequest,
    ChatCompletionResponseChoice,
    ChatCompletionResponseStreamChoice,
    ChatCompletionStreamResponse,
    ChatMessage,
    DeltaMessage,
)


class FunctionCall(BaseModel):
    name: str


RequestFunctionCall: TypeAlias = Literal["none", "auto"] | FunctionCall


DEFAULT_MAX_TOKENS = 4000


class ChatMessage(ChatMessage):
    name: str | None = None
    function_call: str | None = None


class DeltaMessage(DeltaMessage):
    name: str | None = None
    function_call: str | None = None


class ChatCompletionResponseChoice(ChatCompletionResponseChoice):
    message: ChatMessage


class ChatCompletionResponseStreamChoice(ChatCompletionResponseStreamChoice):
    delta: DeltaMessage


class ChatCompletionStreamResponse(ChatCompletionStreamResponse):
    choices: list[ChatCompletionResponseStreamChoice]


class ResponseFormat(BaseModel):
    type_: str = Field(..., alias="type")


class FunctionParameters(BaseModel):
    class Config:
        extra = "allow"


class FunctionDef(BaseModel):
    description: str | None = None
    name: str
    parameters: FunctionParameters


class ChatCompletionRequest(ChatCompletionRequest):
    functions: list[FunctionDef] | None = None
    function_call: RequestFunctionCall | None = None
    response_format: ResponseFormat | None = None
    max_tokens: int | None = DEFAULT_MAX_TOKENS
    spaces_between_special_tokens: Optional[bool] = False
    messages: Union[str, List[Dict[str, Any]]]
    temperature: Optional[float] = 0.0

    class Config:
        extra = "forbid"


class CompletionRequest(CompletionRequest):
    spaces_between_special_tokens: Optional[bool] = False
    temperature: Optional[float] = 0.0

    class Config:
        extra = "forbid"
