from typing import Any

from pydantic import ConfigDict, Field

from .base_models import BaseOutput


class AlgoliaSearchOutput(BaseOutput):
    """Output model for Algolia search"""

    model_config = ConfigDict(extra="allow")

    hits: list[Any] | None = Field(description="The search results")
    metadata: dict[str, Any] | None = Field(description="Additional metadata from the search")
