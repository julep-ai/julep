from typing import List, Optional

from langchain_core.documents import Document
from pydantic import Field
from pydantic_core import Url

from .base_models import (
    BaseArguments,
    BaseOutput,
    BaseSetup,
)


class BrowserBaseSetup(BaseSetup):
    api_key: str = Field(..., description="The api key for BrowserBase")
    project_id: str = Field(..., description="The project id for BrowserBase")
    session_id: Optional[str] = Field(
        None, description="The session id for BrowserBase"
    )


class BrowserBaseLoadArguments(BaseArguments):
    urls: List[Url] = Field(..., description="The urls for loading with BrowserBase")


class BrowserBaseLoadOutput(BaseOutput):
    documents: List[Document] = Field(
        ..., description="The documents loaded from the urls"
    )
