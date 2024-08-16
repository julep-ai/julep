from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from ..autogen.openapi_model import InputChatMLMessage


class MemoryManagementTaskArgs(BaseModel):
    session_id: UUID
    model: str
    dialog: list[InputChatMLMessage]
    previous_memories: list[str] = []


class MemoryManagementTask(BaseModel):
    name: Literal["memory_management.v1"]
    args: MemoryManagementTaskArgs


class MemoryRatingTaskArgs(BaseModel):
    memory: str


class MemoryRatingTask(BaseModel):
    name: Literal["memory_rating.v1"]
    args: MemoryRatingTaskArgs


class EmbedDocsPayload(BaseModel):
    developer_id: UUID
    doc_id: UUID
    content: list[str]
    embed_instruction: str | None
    title: str | None = None
    include_title: bool = False  # Need to be a separate parameter for the activity
