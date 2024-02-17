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
from vllm.sampling_params import SamplingParams
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
    finish_reason: Literal[
        "stop", "length", "function_call", "tool_calls"
    ] | None = None


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

    def to_sampling_params(self) -> SamplingParams:
        return SamplingParams(
            n=self.n or 1,
            presence_penalty=self.presence_penalty or 0.0,
            frequency_penalty=self.frequency_penalty or 0.01,
            repetition_penalty=self.repetition_penalty or 1.0,
            temperature=self.temperature or 0.0,
            top_p=self.top_p or 0.98,
            min_p=self.min_p or 0.02,
            stop=self.stop,
            stop_token_ids=self.stop_token_ids,
            max_tokens=self.max_tokens or DEFAULT_MAX_TOKENS,
            best_of=self.best_of,
            top_k=self.top_k or -1,
            ignore_eos=self.ignore_eos or False,
            use_beam_search=self.use_beam_search or False,
            skip_special_tokens=self.skip_special_tokens or True,
            spaces_between_special_tokens=self.spaces_between_special_tokens or False,
            include_stop_str_in_output=self.include_stop_str_in_output or False,
            length_penalty=self.length_penalty or 1.0,
        )


class CompletionRequest(CompletionRequest):
    model_config = ConfigDict(extra="forbid")

    spaces_between_special_tokens: bool | None = False
    temperature: float | None = 0.0

    def to_sampling_params(self) -> SamplingParams:
        echo_without_generation = self.echo and self.max_tokens == 0

        return SamplingParams(
            n=self.n or 1,
            best_of=self.best_of,
            presence_penalty=self.presence_penalty or 0.0,
            frequency_penalty=self.frequency_penalty or 0.0,
            repetition_penalty=self.repetition_penalty or 1.0,
            temperature=self.temperature or 0.0,
            top_p=self.top_p or 1.0,
            top_k=self.top_k or -1,
            min_p=self.min_p or 0.0,
            stop=self.stop,
            stop_token_ids=self.stop_token_ids,
            ignore_eos=self.ignore_eos or False,
            max_tokens=(
                (self.max_tokens or DEFAULT_MAX_TOKENS)
                if not echo_without_generation
                else 1
            ),
            logprobs=self.logprobs,
            use_beam_search=self.use_beam_search or False,
            prompt_logprobs=self.logprobs if self.echo else None,
            skip_special_tokens=self.skip_special_tokens or True,
            spaces_between_special_tokens=self.spaces_between_special_tokens or False,
            include_stop_str_in_output=self.include_stop_str_in_output or False,
            length_penalty=self.length_penalty or 1.0,
        )


class ChatCompletionResponse(ChatCompletionResponse):
    choices: list[ChatCompletionResponseChoice]
