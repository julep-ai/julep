from typing import Literal

from pydantic import BaseModel, Field


ValidRole = Literal["assistant", "system", "user", "function_call"]


class ChatMLMessage(BaseModel):
    name: str | None = None
    role: ValidRole | None = None
    content: str | None = None
    continue_: bool | None = Field(default=None, alias="continue")


ChatML = list[ChatMLMessage]
