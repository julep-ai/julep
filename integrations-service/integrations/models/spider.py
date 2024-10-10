from langchain_core.documents import Document
from pydantic import Field
from pydantic_core import Url

from .base_models import BaseArguments, BaseOutput, BaseSetup


class SpiderSetup(BaseSetup):
    spider_api_key: str = Field(..., description="The request for which to fetch data")


class SpiderFetchArguments(BaseArguments):
    url: Url = Field(..., description="The url for which to fetch data")
    mode: str = Field("scrape", description="The type of crawlers")
    params: dict | None = Field(None, description="The parameters for the Spider API")


class SpiderFetchOutput(BaseOutput):
    documents: list[Document] = Field(
        ..., description="The documents returned from the spider"
    )
