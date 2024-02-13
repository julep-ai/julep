from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


ValidRole = Literal["assistant", "system", "user", "function_call"]


class ChatMLMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    role: ValidRole | None = None
    content: str | None = None
    continue_: bool | None = Field(default=None, alias="continue")
    function_call: str | None = None


ChatML = list[ChatMLMessage]
