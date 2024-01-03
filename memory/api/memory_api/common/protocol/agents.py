from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, UUID4, Field


class AgentDefaultSettings(BaseModel):
    temperature: float = 0.0
    top_p: float = 1.0
    repetition_penalty: float = 1.0
    length_penalty: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


class Tool(BaseModel):
    type_: str
    definition: str


ModelType = Literal["julep-ai/samantha-1", "julep-ai/samantha-1-turbo"]


class CreateAgentRequest(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="agent_id")
    name: str
    about: str
    model: ModelType = "julep-ai/samantha-1-turbo"
    default_settings: AgentDefaultSettings = Field(default_factory=AgentDefaultSettings)
    # instructions: list[str] | None = None
    # tools: list[Tool]


class UpdateAgentRequest(BaseModel):
    name: str
    about: str
    model: ModelType = "julep-ai/samantha-1-turbo"
    default_settings: AgentDefaultSettings = Field(default_factory=AgentDefaultSettings)
    # instructions: list[str] | None = None
    # tools: list[Tool]


class Agent(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="agent_id")
    name: str
    about: str
    model: ModelType = "julep-ai/samantha-1-turbo"
    default_settings: AgentDefaultSettings = Field(default_factory=AgentDefaultSettings)
    # instructions: list[str] | None = None
    # tools: list[Tool]
    created_at: float | None = None
    updated_at: float | None = None
