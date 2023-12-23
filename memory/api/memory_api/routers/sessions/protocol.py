from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, UUID4
from memory_api.common.protocol.entries import Entry


class Target(str, Enum):
    user = "user"
    agent = "agent"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
    function_call = "function_call"


class ToolType(str, Enum):
    function = "function"
    webhook = "webhook"


class ResponseFormatType(str, Enum):
    text = ("text",)
    json_object = "json_object"


class ToolChoiceType(str, Enum):
    none = "none"
    auto = "auto"


class CreateSessionRequest(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="session_id")
    agent_id: UUID4
    user_id: UUID4
    situation: str


class UpdateSessionRequest(BaseModel):
    situation: str


class Session(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="session_id")
    agent_id: str
    user_id: str
    updated_at: float | None = None
    created_at: float | None = None
    situation: str
    summary: str | None = None
    metadata: dict = Field(default={})


class ChatParams(BaseModel):
    messages: list[Entry]


class ChatRequest(BaseModel):
    session_id: str
    params: ChatParams
    remember: bool = False
    recall: bool = False


class SessionsRequest(BaseModel):
    session_id: str


class ChatMessage(BaseModel):
    created_at: float | None = None
    role: MessageRole
    content: str
    name: str
    continue_: bool = Field(default=False, alias="continue")


class ResponseFormat(BaseModel):
    type_: ResponseFormatType = Field(default=ResponseFormatType.text, alias="type")


class FunctionDefinition(BaseModel):
    name: str
    parameters: dict
    description: str


class Tool(BaseModel):
    type_: ToolType = Field(default=ToolType.function, alias="type")
    definition: FunctionDefinition


class SessionsChatRequest(BaseModel):
    messages: list[ChatMessage]
    frequency_penalty: float | None = Field(default=0, ge=-1, le=1)
    length_penalty: float | None = Field(default=1, ge=0, le=2)
    logit_bias: dict | None = None
    max_tokens: int | None = None
    presence_penalty: float | None = Field(default=0, ge=-1, le=1)
    repetition_penalty: float | None = Field(default=1, ge=0, le=2)
    response_format: ResponseFormat | None = None
    seed: int | None = None
    stop: str | None = None
    stream: bool | None = Field(default=False)
    temperature: float | None = Field(default=1, ge=0, le=2)
    top_p: float | None = Field(default=1, ge=0, le=1)
    tools: list[Tool]
    tool_choice: ToolChoiceType | None = None


class Suggestion(BaseModel):
    message_id: UUID4
    target_id: UUID4
    content: str
    target: Target
    created_at: float | None = None
