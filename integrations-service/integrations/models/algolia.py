from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AlgoliaSearchOutput(BaseModel):
    """Output model for Algolia search"""

    model_config = ConfigDict(extra="allow")

    hits: list[Any] = Field(description="The search results")
    metadata: dict[str, Any] = Field(description="Additional metadata from the search")
