from pydantic import BaseModel, ConfigDict, Field, field_validator

from agents_api.autogen.openapi_model import Preset, ResponseFormat, Tool


class Settings(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    model: str
    frequency_penalty: float | None = Field(default=0)
    length_penalty: float | None = Field(default=1.0)
    logit_bias: float | None = None
    max_tokens: int | None = Field(default=200)
    presence_penalty: float | None = Field(default=0)
    repetition_penalty: float | None = Field(default=1)
    response_format: ResponseFormat | None
    seed: int | None = Field(default=0)
    stop: list[str] | None = None
    stream: bool | None = Field(default=False)
    temperature: float | None = Field(default=0.7)
    top_p: float | None = Field(default=1)
    remember: bool | None = Field(default=True)
    recall: bool | None = Field(default=True)
    min_p: float | None = Field(default=0.01)
    preset: Preset | None = Field(default=None)
    tools: list[Tool] | None = Field(default=None)
    token_budget: int | None = Field(default=None)
    context_overflow: str | None = Field(default=None)

    @field_validator("max_tokens")
    def set_max_tokens(cls, max_tokens):
        return max_tokens if max_tokens is not None else 200

    @field_validator("stream")
    def set_stream(cls, stream):
        return stream or False
