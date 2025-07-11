# generated by datamodel-codegen:
#   filename:  openapi-1.0.0.yaml

from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool

from .Common import LogitBias
from .Docs import DocReference
from .Tools import (
    ChosenBash20241022,
    ChosenComputer20241022,
    ChosenFunctionCall,
    ChosenTextEditor20241022,
    CreateToolRequest,
    NamedToolChoice,
)


class BaseChatOutput(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    index: int
    finish_reason: Literal["stop", "length", "content_filter", "tool_calls"] = "stop"
    """
    The reason the model stopped generating tokens
    """
    logprobs: LogProbResponse | None = None
    """
    The log probabilities of tokens
    """
    tool_calls: (
        list[
            ChosenFunctionCall
            | ChosenComputer20241022
            | ChosenTextEditor20241022
            | ChosenBash20241022
        ]
        | None
    ) = None
    """
    The tool calls generated by the model
    """


class BaseChatResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    usage: CompletionUsage | None = None
    """
    Usage statistics for the completion request
    """
    jobs: Annotated[list[UUID], Field(json_schema_extra={"readOnly": True})] = []
    """
    Background job IDs that may have been spawned from this interaction.
    """
    docs: Annotated[list[DocReference], Field(json_schema_extra={"readOnly": True})] = (
        []
    )
    """
    Documents referenced for this request (for citation purposes).
    """
    created_at: Annotated[AwareDatetime, Field(json_schema_extra={"readOnly": True})]
    """
    When this resource was created as UTC date-time
    """
    id: Annotated[UUID, Field(json_schema_extra={"readOnly": True})]


class BaseTokenLogProb(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    token: str
    logprob: float
    """
    The log probability of the token
    """
    bytes: list[int] | None = None


class ChatInputData(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    messages: Annotated[list[Message], Field(min_length=1)]
    """
    A list of new input messages comprising the conversation so far.
    """
    tools: list[CreateToolRequest] | None = None
    """
    (Advanced) List of tools that are provided in addition to agent's default set of tools.
    """
    tool_choice: Literal["auto", "none"] | NamedToolChoice | None = None
    """
    Can be one of existing tools given to the agent earlier or the ones provided in this request.
    """


class ChatOutputChunk(BaseChatOutput):
    """
    Streaming chat completion output
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    delta: Delta
    """
    The message generated by the model
    """


class ChunkChatResponse(BaseChatResponse):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    choices: list[ChatOutputChunk]
    """
    The deltas generated by the model
    """


class CompletionUsage(BaseModel):
    """
    Usage statistics for the completion request
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    completion_tokens: Annotated[
        int | None, Field(json_schema_extra={"readOnly": True})
    ] = None
    """
    Number of tokens in the generated completion
    """
    prompt_tokens: Annotated[
        int | None, Field(json_schema_extra={"readOnly": True})
    ] = None
    """
    Number of tokens in the prompt
    """
    total_tokens: Annotated[int | None, Field(json_schema_extra={"readOnly": True})] = (
        None
    )
    """
    Total number of tokens used in the request (prompt + completion)
    """


class Content(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    text: str
    type: Literal["text"] = "text"
    """
    The type (fixed to 'text')
    """


class ContentItem(Content):
    pass


class ContentItemModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    type: Literal["image"] = "image"
    source: Source


class ContentItemModel1(Content):
    pass


class ContentItemModel2(ContentItemModel):
    pass


class ContentItemModel3(Content):
    pass


class ContentItemModel4(ContentItemModel):
    pass


class ContentItemModel5(Content):
    pass


class ContentItemModel6(ContentItemModel):
    pass


class ContentModel(BaseModel):
    """
    Anthropic image content part
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    tool_use_id: str
    type: Literal["tool_result"] = "tool_result"
    content: list[ContentItem] | list[ContentItemModel]


class ContentModel1(Content):
    pass


class ContentModel2(BaseModel):
    """
    Anthropic image content part
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    tool_use_id: str
    type: Literal["tool_result"] = "tool_result"
    content: list[ContentItemModel1] | list[ContentItemModel2]


class ContentModel3(Content):
    pass


class ContentModel4(BaseModel):
    """
    Anthropic image content part
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    tool_use_id: str
    type: Literal["tool_result"] = "tool_result"
    content: list[ContentItemModel3] | list[ContentItemModel4]


class ContentModel5(Content):
    pass


class ContentModel6(BaseModel):
    """
    Anthropic image content part
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    tool_use_id: str
    type: Literal["tool_result"] = "tool_result"
    content: list[ContentItemModel5] | list[ContentItemModel6]


class ContentModel7(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    image_url: ImageUrl
    """
    The image URL
    """
    type: Literal["image_url"] = "image_url"
    """
    The type (fixed to 'image_url')
    """


class Delta(BaseModel):
    """
    The message generated by the model
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    role: Literal["user", "assistant", "system", "tool"]
    """
    The role of the message
    """
    tool_call_id: str | None = None
    content: Annotated[
        str | list[str] | list[ContentModel1 | ContentModel7 | ContentModel2] | None,
        Field(...),
    ] = None
    """
    The content parts of the message
    """
    name: str | None = None
    """
    Name
    """
    tool_calls: (
        list[
            ChosenFunctionCall
            | ChosenComputer20241022
            | ChosenTextEditor20241022
            | ChosenBash20241022
        ]
        | None
    ) = []
    """
    Tool calls generated by the model.
    """


class ImageUrl(BaseModel):
    """
    The image URL
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    url: str
    """
    Image URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`)
    """
    detail: Literal["low", "high", "auto"] = "auto"
    """
    The detail level of the image
    """


class LogProbResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    content: Annotated[list[TokenLogProb] | None, Field(...)]
    """
    The log probabilities of the tokens
    """


class Message(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    role: Literal["user", "assistant", "system", "tool"]
    """
    The role of the message
    """
    tool_call_id: str | None = None
    content: Annotated[
        str | list[str] | list[Content | ContentModel7 | ContentModel] | None,
        Field(...),
    ] = None
    """
    The content parts of the message
    """
    name: str | None = None
    """
    Name
    """
    tool_calls: (
        list[
            ChosenFunctionCall
            | ChosenComputer20241022
            | ChosenTextEditor20241022
            | ChosenBash20241022
        ]
        | None
    ) = []
    """
    Tool calls generated by the model.
    """


class MessageChatResponse(BaseChatResponse):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    choices: list[SingleChatOutput | MultipleChatOutput]
    """
    The deltas generated by the model
    """


class MessageModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    role: Literal["user", "assistant", "system", "tool"]
    """
    The role of the message
    """
    tool_call_id: str | None = None
    content: Annotated[
        str | list[str] | list[ContentModel3 | ContentModel7 | ContentModel4] | None,
        Field(...),
    ] = None
    """
    The content parts of the message
    """
    name: str | None = None
    """
    Name
    """
    tool_calls: (
        list[
            ChosenFunctionCall
            | ChosenComputer20241022
            | ChosenTextEditor20241022
            | ChosenBash20241022
        ]
        | None
    ) = []
    """
    Tool calls generated by the model.
    """
    created_at: Annotated[
        AwareDatetime | None, Field(json_schema_extra={"readOnly": True})
    ] = None
    """
    When this resource was created as UTC date-time
    """
    id: Annotated[UUID | None, Field(json_schema_extra={"readOnly": True})] = None


class MultipleChatOutput(BaseChatOutput):
    """
    The output returned by the model. Note that, depending on the model provider, they might return more than one message.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    messages: Annotated[
        list[MessageModel], Field(json_schema_extra={"readOnly": True}, min_length=1)
    ]


class RenderResponse(ChatInputData):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    docs: Annotated[list[DocReference], Field(json_schema_extra={"readOnly": True})] = (
        []
    )
    """
    Documents referenced for this request (for citation purposes).
    """


class SchemaCompletionResponseFormat(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    type: Literal["json_schema"] = "json_schema"
    """
    The format of the response
    """
    json_schema: dict[str, Any]
    """
    The schema of the response
    """


class SimpleCompletionResponseFormat(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    type: Literal["text", "json_object"] = "text"
    """
    The format of the response
    """


class SingleChatOutput(BaseChatOutput):
    """
    The output returned by the model. Note that, depending on the model provider, they might return more than one message.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    message: MessageModel


class Source(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    type: Literal["base64"] = "base64"
    media_type: str
    data: str


class TokenLogProb(BaseTokenLogProb):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    top_logprobs: Annotated[
        list[BaseTokenLogProb],
        Field(json_schema_extra={"readOnly": True}, min_length=1),
    ]
    """
    The log probabilities of the tokens
    """


class ChatInput(ChatInputData):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    remember: Annotated[StrictBool, Field(json_schema_extra={"readOnly": True})] = False
    """
    DISABLED: Whether this interaction should form new memories or not (will be enabled in a future release)
    """
    recall: StrictBool = True
    """
    Whether previous memories and docs should be recalled or not
    """
    save: StrictBool = True
    """
    Whether this interaction should be stored in the session history or not
    """
    model: Annotated[
        str | None,
        Field(
            max_length=120,
            pattern="^[\\p{L}\\p{Nl}\\p{Pattern_Syntax}\\p{Pattern_White_Space}]+[\\p{ID_Start}\\p{Mn}\\p{Mc}\\p{Nd}\\p{Pc}\\p{Pattern_Syntax}\\p{Pattern_White_Space}]*$",
        ),
    ] = None
    """
    Identifier of the model to be used
    """
    stream: StrictBool = False
    """
    Indicates if the server should stream the response as it's generated
    """
    stop: Annotated[list[str], Field(max_length=4)] = []
    """
    Up to 4 sequences where the API will stop generating further tokens.
    """
    seed: Annotated[int | None, Field(ge=-1, le=1000)] = None
    """
    If specified, the system will make a best effort to sample deterministically for that particular seed value
    """
    max_tokens: Annotated[int | None, Field(ge=1)] = None
    """
    The maximum number of tokens to generate in the chat completion
    """
    logit_bias: dict[str, LogitBias] | None = None
    """
    Modify the likelihood of specified tokens appearing in the completion
    """
    response_format: (
        SimpleCompletionResponseFormat | SchemaCompletionResponseFormat | None
    ) = None
    """
    Response format (set to `json_object` to restrict output to JSON)
    """
    agent: UUID | None = None
    """
    Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions)
    """
    repetition_penalty: Annotated[float | None, Field(ge=0.0, le=2.0)] = None
    """
    Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    """
    length_penalty: Annotated[float | None, Field(ge=0.0, le=2.0)] = None
    """
    Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated.
    """
    min_p: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    """
    Minimum probability compared to leading token to be considered
    """
    frequency_penalty: Annotated[float | None, Field(ge=-2.0, le=2.0)] = None
    """
    Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    """
    presence_penalty: Annotated[float | None, Field(ge=-2.0, le=2.0)] = None
    """
    Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    """
    temperature: Annotated[float | None, Field(ge=0.0, le=5.0)] = None
    """
    What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
    """
    top_p: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    """
    Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.
    """
    metadata: dict[str, Any] | None = None
    auto_run_tools: StrictBool = False
    """
    Whether to automatically run tools and send the results back to the model (requires tools or agents with tools).
    """
    recall_tools: StrictBool = True
    """
    Whether to include tool requests and responses when recalling messages.
    """
