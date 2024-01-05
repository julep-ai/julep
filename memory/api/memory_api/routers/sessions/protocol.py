from enum import Enum
from pydantic import BaseModel, Field
from memory_api.autogen.openapi_model import ResponseFormat


class Settings(BaseModel):
    model: str
    frequency_penalty: float | None = Field(default=0)
    length_penalty: float | None = Field(default=1.0)
    logit_bias: float | None = None
    max_tokens: int
    presence_penalty: float | None = Field(default=0)
    repetition_penalty: float | None = Field(default=1)
    response_format: ResponseFormat | None
    seed: int | None = Field(default=0)
    stop: list[str] | None = None
    stream: bool = Field(default=False)
    temperature: float | None = Field(default=0.7)
    top_p: float | None = Field(default=1)
