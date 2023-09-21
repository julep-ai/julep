import time
from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    name: str
    email: str
    about: str = Field(default="")
    metadata: dict = Field(default={})
    created_at: float
    updated_at: float


class UserRequest(BaseModel):
    user_id: str | None
    email: str | None
