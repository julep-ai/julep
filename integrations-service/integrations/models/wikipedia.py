from langchain_core.documents import Document
from pydantic import Field

from .base_models import (
    BaseArguments,
    BaseOutput,
)


class WikipediaSearchArguments(BaseArguments):
    query: str = Field(..., description="The search query string")
    load_max_docs: int = Field(2, description="Maximum number of documents to load")


class WikipediaSearchOutput(BaseOutput):
    documents: list[Document] = Field(
        ..., description="The documents returned from the Wikipedia search"
    )
