from uuid import uuid4
from pydantic import BaseModel, UUID4, Field


class Tool(BaseModel):
    type_: str
    definition: str


class CreateAgentRequest(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="character_id")
    name: str
    about: str
    # instructions: list[str] | None = None
    # tools: list[Tool]


class UpdateAgentRequest(BaseModel):
    about: str
    # instructions: list[str] | None = None
    # tools: list[Tool]


class Agent(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="character_id")
    name: str
    about: str
    # instructions: list[str] | None = None
    # tools: list[Tool]
    metadata: dict = Field(default={})
    created_at: float | None = None
    updated_at: float | None = None
