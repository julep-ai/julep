import time
from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    name: str
    email: str
    about: str = Field(default="")
    metadata: dict = Field(default={})
    created_at: int
    updated_at: int = Field(default=time.time())
