from langchain_core.documents import Document
from pydantic import Field

from .base_models import BaseOutput


class WikipediaSearchOutput(BaseOutput):
    documents: list[Document] = Field(
        ..., description="The documents returned from the Wikipedia search"
    )
