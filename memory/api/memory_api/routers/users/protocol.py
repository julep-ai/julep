from uuid import uuid4
from pydantic import BaseModel, Field, UUID4


class UserInformation(BaseModel):
    title: str
    content: str


class BaseUser(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="user_id")
    name: str | None = Field(default="User")
    about: str | None = None


class CreateUserRequest(BaseUser):
    additional_information: list[UserInformation] | None = None


class UpdateUserRequest(BaseUser):
    pass


class User(BaseUser):
    created_at: float | None = None
    updated_at: float | None = None
