from uuid import uuid4
from pydantic import BaseModel, Field, UUID4


class User(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="user_id")
    name: str
    email: str
    about: str = Field(default="")
    metadata: dict = Field(default={})
    created_at: float | None = None
    updated_at: float | None = None


class UserRequest(BaseModel):
    user_id: str | None = None
    email: str | None = None
