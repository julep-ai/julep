from typing import Any

from pydantic import BaseModel, Field

from .base_models import BaseOutput


class SpiderResponse(BaseModel):
    content: str | None = None
    error: str | None = None
    status: int | None = None
    costs: dict[Any, Any] | None = None
    url: str | None = None


class SpiderOutput(BaseOutput):
    result: list[SpiderResponse] = Field(..., description="The responses from the spider")
