from uuid import uuid4
from pydantic import BaseModel, Field, UUID4


class UserInformation(BaseModel):
    title: str
    content: str


class BaseUser(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="user_id")
    name: str | None = Field(default="User")
    about: str | None = None
    additional_information: list[UserInformation] | None = None


class CreateUserRequest(BaseUser):
    pass


class UpdateUserRequest(BaseModel):
    about: str
    additional_information: list[UserInformation] | None = None


class User(BaseUser):
    metadata: dict = Field(default={})
    created_at: float | None = None
    updated_at: float | None = None


class UserRequest(BaseModel):
    user_id: str | None = None
    email: str | None = None
