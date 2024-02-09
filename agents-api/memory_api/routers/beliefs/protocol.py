from uuid import uuid4
from pydantic import BaseModel, UUID4, Field


class UpsertBeliefRequest(BaseModel):
    belief_id: UUID4 = Field(default_factory=uuid4)
    character_id: UUID4
    belief: str
    embedding: list[float]


class IndexRequest(BaseModel):
    character_id: UUID4
    vector: list[float]


class Belief(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="belief_id")
    referrent_is_user: bool
    referrent_id: UUID4
    subject_is_user: bool | None = None
    subject_id: UUID4 | None = None
    belief: str
    valence: float
    sentiment: str = Field(default="neutral")
    source_episode: UUID4 | None = None
    parent_belief: UUID4 | None = None
    processed: bool = Field(default=False)
    created_at: float | None = None
    embedding: list[float]
    fact_embedding: list[float] | None = None
