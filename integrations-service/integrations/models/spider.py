from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .base_models import BaseOutput


class SpiderResponse(BaseModel):
    content: Optional[str | list[str]] = None
    error: Optional[str] = None
    status: Optional[int] = None
    costs: Optional[dict[Any, Any]] = None
    url: Optional[str] = None


class SpiderOutput(BaseOutput):
    result: List[SpiderResponse] = Field(
        ..., description="The responses from the spider"
    )
