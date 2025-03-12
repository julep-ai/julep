from typing import Any

from pydantic import Field

from .base_models import BaseModel, BaseOutput


class UnstructuredResponse(BaseModel):
    content_type: str
    status_code: int
    csv_elements: str | None = None
    content: list[dict[str, Any]] | None = None


class UnstructuredParseOutput(BaseOutput):
    result: list[UnstructuredResponse] = Field(
        ..., description="The responses from the unstructured parse"
    )
