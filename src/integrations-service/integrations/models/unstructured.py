from typing import Any

from .base_models import BaseOutput


class UnstructuredParseOutput(BaseOutput):
    content_type: str
    status_code: int
    csv_elements: str | None = None
    content: list[dict[str, Any]] | None = None
