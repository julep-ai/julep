from langchain_core.documents import Document
from pydantic import Field
from pydantic_core import Url

from .base_models import BaseArguments, BaseOutput


class HackerNewsFetchArguments(BaseArguments):
    url: Url = Field(..., description="The URL of the Hacker News thread to fetch")


class HackerNewsFetchOutput(BaseOutput):
    documents: list[Document] = Field(
        ..., description="The documents returned from the Hacker News search"
    )
