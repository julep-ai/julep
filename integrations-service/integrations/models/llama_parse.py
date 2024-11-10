from llama_index.core.schema import Document
from pydantic import Field

from .base_models import BaseOutput


class LlamaParseFetchOutput(BaseOutput):
    documents: list[Document] = Field(
        ..., description="The documents returned from the spider"
    )
