from typing import Any, Callable, Literal, Optional, Protocol, TypedDict
from uuid import UUID

from pydantic import BaseModel


class PromptModule(Protocol):
    stop: list[str]
    temperature: float
    parser: Callable[[str], str]
    make_prompt: Callable[..., str]


class ChatML(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

    name: Optional[str] = None
    entry_id: Optional[UUID] = None

    processed: bool = False
    parent_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    timestamp: Optional[float] = None
    token_count: Optional[int] = None


class BaseTask(BaseModel):
    ...


class BaseTaskArgs(BaseModel):
    ...


class AddPrinciplesTaskArgs(BaseTaskArgs):
    scores: dict[str, Any]
    full: bool = False
    name: Optional[str] = None
    user_id: Optional[UUID] = None
    character_id: Optional[UUID] = None


class AddPrinciplesTask(BaseTask):
    name: Literal["add_principles.v1"]
    args: AddPrinciplesTaskArgs


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


class CombinedTask(TypedDict):
    name: str
    args: dict[Any, Any]
