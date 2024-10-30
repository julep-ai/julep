from typing import List
from pydantic import Field, BaseModel

from .base_models import BaseOutput


class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str

class BraveSearchOutput(BaseOutput):
    result: List[SearchResult] = Field(..., description="A list of search results")