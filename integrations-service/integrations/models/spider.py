from langchain_core.documents import Document
from pydantic import Field

from .base_models import BaseOutput


class SpiderFetchOutput(BaseOutput):
    documents: list[Document] = Field(
        ..., description="The documents returned from the spider"
    )
