from typing import Any

from pydantic import ConfigDict, Field

from .base_models import BaseOutput


class AlgoliaSearchOutput(BaseOutput):
    """Output model for Algolia search"""

    model_config = ConfigDict(extra="allow")

    hits: list[Any] = Field(description="The search results")
    metadata: dict[str, Any] = Field(description="Additional metadata from the search")
