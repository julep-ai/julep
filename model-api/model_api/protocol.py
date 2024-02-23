from enum import Enum
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
from vllm.sampling_params import LogitsProcessor, SamplingParams
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


class SamplingParams(SamplingParams):
    _properties = [
        "n",
        "best_of",
        "presence_penalty",
        "frequency_penalty",
        "repetition_penalty",
        "temperature",
        "top_p",
        "top_k",
        "min_p",
        "use_beam_search",
        "length_penalty",
        "early_stopping",
        "stop",
        "stop_token_ids",
        "include_stop_str_in_output",
        "ignore_eos",
        "max_tokens",
        "logprobs",
        "prompt_logprobs",
        "skip_special_tokens",
        "spaces_between_special_tokens",
        "logits_processors",
    ]

    def __init__(
        self,
        n: int = 1,
        best_of: int | None = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.01,  # Custom
        repetition_penalty: float = 1.0,
        temperature: float = 0.0,  # Custom
        top_p: float = 0.99,  # Custom
        top_k: int = -1,
        min_p: float = 0.01,  # Custom
        use_beam_search: bool = False,
        length_penalty: float = 1.0,
        early_stopping: bool | str = False,
        stop: str | list[str] | None = None,
        stop_token_ids: list[int] | None = None,
        include_stop_str_in_output: bool = False,
        ignore_eos: bool = False,
        max_tokens: int | None = DEFAULT_MAX_TOKENS,  # Custom
        logprobs: int | None = None,
        prompt_logprobs: int | None = None,
        skip_special_tokens: bool = True,
        spaces_between_special_tokens: bool = False,  # Custom
        logits_processors: list[LogitsProcessor] | None = None,
    ) -> None:
        super().__init__(
            n=n,
            best_of=best_of,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            repetition_penalty=repetition_penalty,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            min_p=min_p,
            use_beam_search=use_beam_search,
            length_penalty=length_penalty,
            early_stopping=early_stopping,
            stop=stop,
            stop_token_ids=stop_token_ids,
            include_stop_str_in_output=include_stop_str_in_output,
            ignore_eos=ignore_eos,
            max_tokens=max_tokens,
            logprobs=logprobs,
            prompt_logprobs=prompt_logprobs,
            skip_special_tokens=skip_special_tokens,
            spaces_between_special_tokens=spaces_between_special_tokens,
            logits_processors=logits_processors,
        )

    def __eq__(self, other):
        for p in self._properties:
            if getattr(self, p) != getattr(other, p):
                return False

        return True


class ChatCompletionRequest(ChatCompletionRequest):
    model_config = ConfigDict(extra="forbid")

    functions: list[FunctionDef] | None = None
    function_call: RequestFunctionCall | None = None
    tools: list[Tool] | None = None
    tool_choice: ToolChoice | None = None
    response_format: ResponseFormat | None = None
    messages: ChatML

    spaces_between_special_tokens: bool | None = False  # Custom
    max_tokens: int | None = DEFAULT_MAX_TOKENS  # Custom
    temperature: float | None = 0.0  # Custom
    frequency_penalty: float | None = 0.01  # Custom
    top_p: float | None = 0.99  # Custom
    min_p: float | None = 0.01  # Custom

    def to_sampling_params(self) -> SamplingParams:
        echo_without_generation = self.echo and self.max_tokens == 0

        if self.logit_bias is not None:
            raise ValueError("logit_bias is not supported currently.")

        return SamplingParams(
            n=self.n,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            repetition_penalty=self.repetition_penalty,
            temperature=self.temperature,
            top_p=self.top_p,
            min_p=self.min_p,
            stop=self.stop,
            stop_token_ids=self.stop_token_ids,
            max_tokens=(
                (self.max_tokens or DEFAULT_MAX_TOKENS)
                if not echo_without_generation
                else 1
            ),
            best_of=self.best_of,
            top_k=self.top_k,
            ignore_eos=self.ignore_eos,
            use_beam_search=self.use_beam_search,
            skip_special_tokens=self.skip_special_tokens,
            spaces_between_special_tokens=self.spaces_between_special_tokens,
            include_stop_str_in_output=self.include_stop_str_in_output,
            length_penalty=self.length_penalty,
        )


class CompletionRequest(CompletionRequest):
    model_config = ConfigDict(extra="forbid")

    spaces_between_special_tokens: bool | None = False  # Custom
    max_tokens: int | None = DEFAULT_MAX_TOKENS  # Custom
    temperature: float | None = 0.0  # Custom
    frequency_penalty: float | None = 0.01  # Custom
    top_p: float | None = 0.99  # Custom
    min_p: float | None = 0.01  # Custom

    def to_sampling_params(self) -> SamplingParams:
        echo_without_generation = self.echo and self.max_tokens == 0

        if self.logit_bias is not None:
            raise ValueError("logit_bias is not supported currently.")

        return SamplingParams(
            n=self.n,
            best_of=self.best_of,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            repetition_penalty=self.repetition_penalty,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            min_p=self.min_p,
            stop=self.stop,
            stop_token_ids=self.stop_token_ids,
            ignore_eos=self.ignore_eos,
            max_tokens=(
                (self.max_tokens or DEFAULT_MAX_TOKENS)
                if not echo_without_generation
                else 1
            ),
            logprobs=self.logprobs,
            use_beam_search=self.use_beam_search,
            prompt_logprobs=self.logprobs,
            skip_special_tokens=self.skip_special_tokens,
            spaces_between_special_tokens=self.spaces_between_special_tokens,
            include_stop_str_in_output=self.include_stop_str_in_output,
            length_penalty=self.length_penalty,
        )


class ChatCompletionResponse(ChatCompletionResponse):
    choices: list[ChatCompletionResponseChoice]
