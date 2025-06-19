from pydantic import BaseModel, Field

from .base_models import BaseOutput


class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str


class BraveSearchOutput(BaseOutput):
    result: list[SearchResult] = Field(..., description="A list of search results")
