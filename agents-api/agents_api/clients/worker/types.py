from typing import Callable, Literal, Optional, Protocol
from uuid import UUID
from pydantic import BaseModel
from agents_api.autogen.openapi_model import (
    ChatMLTextContentPart,
    ChatMLImageContentPart,
)


class PromptModule(Protocol):
    stop: list[str]
    temperature: float
    parser: Callable[[str], str]
    make_prompt: Callable[..., str]


class ChatML(BaseModel):
    role: Literal["system", "user", "assistant", "function_call"]
    content: str | dict | list[ChatMLTextContentPart] | list[ChatMLImageContentPart]

    name: Optional[str] = None
    entry_id: Optional[UUID] = None

    processed: bool = False
    parent_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    timestamp: Optional[float] = None
    token_count: Optional[int] = None


class BaseTask(BaseModel): ...


class BaseTaskArgs(BaseModel): ...


class MemoryManagementTaskArgs(BaseTaskArgs):
    session_id: UUID
    model: str
    dialog: list[ChatML]
    previous_memories: list[str] = []


class MemoryManagementTask(BaseTask):
    name: Literal["memory_management.v1"]
    args: MemoryManagementTaskArgs


class MemoryDensityTaskArgs(BaseTaskArgs):
    memory: str


class MemoryDensityTask(BaseTask):
    name: Literal["memory_density.v1"]
    args: MemoryDensityTaskArgs


class MemoryRatingTaskArgs(BaseTaskArgs):
    memory: str


class MemoryRatingTask(BaseTask):
    name: Literal["memory_rating.v1"]
    args: MemoryRatingTaskArgs


class DialogInsightsTaskArgs(BaseTaskArgs):
    dialog: list[ChatML]
    person1: str
    person2: str


class DialogInsightsTask(BaseTask):
    name: Literal["dialog_insights.v1"]
    args: DialogInsightsTaskArgs


class RelationshipSummaryTaskArgs(BaseTaskArgs):
    statements: list[str]
    person1: str
    person2: str


class RelationshipSummaryTask(BaseTask):
    name: Literal["relationship_summary.v1"]
    args: RelationshipSummaryTaskArgs


class SalientQuestionsTaskArgs(BaseTaskArgs):
    statements: list[str]
    num: int = 3


class SalientQuestionsTask(BaseTask):
    name: Literal["salient_questions.v1"]
    args: SalientQuestionsTaskArgs


CombinedTask = (
    MemoryManagementTask
    | MemoryDensityTask
    | MemoryRatingTask
    | DialogInsightsTask
    | RelationshipSummaryTask
    | SalientQuestionsTask
)
