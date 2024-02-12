from typing import Optional, Literal

from pydantic import BaseModel, Field


ValidRole = Literal["assistant", "system", "user", "function_call"]


class ChatMLMessage(BaseModel):
    name: Optional[str] = None
    role: Optional[ValidRole] = None
    content: Optional[str] = None
    continue_: Optional[bool] = Field(default=None, alias="continue")


ChatML = list[ChatMLMessage]
