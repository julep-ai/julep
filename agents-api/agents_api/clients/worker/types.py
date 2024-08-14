from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from agents_api.autogen.openapi_model import (
    InputChatMLMessage,
)


class MemoryManagementTaskArgs(BaseModel):
    session_id: UUID
    model: str
    dialog: list[InputChatMLMessage]
    previous_memories: list[str] = []


class MemoryManagementTask(BaseModel):
    name: Literal["memory_management.v1"]
    args: MemoryManagementTaskArgs


class MemoryDensityTaskArgs(BaseModel):
    memory: str


class MemoryDensityTask(BaseModel):
    name: Literal["memory_density.v1"]
    args: MemoryDensityTaskArgs


class MemoryRatingTaskArgs(BaseModel):
    memory: str


class MemoryRatingTask(BaseModel):
    name: Literal["memory_rating.v1"]
    args: MemoryRatingTaskArgs


CombinedTask = MemoryManagementTask | MemoryDensityTask | MemoryRatingTask
