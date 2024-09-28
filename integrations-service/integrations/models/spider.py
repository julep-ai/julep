from langchain_core.documents import Document
from pydantic import Field

from .base_models import BaseArguments, BaseOutput, BaseSetup


class SpiderSetup(BaseSetup):
    spider_api_key: str = Field(..., description="The request for which to fetch data")


class SpiderArguments(BaseArguments):
    query: str = Field(..., description="The url for which to fetch data")
    mode: str = Field("scrape", description="The type of crawlers")
    params: dict = Field(None, description="The parameters for the Spider API")


class SpiderOutput(BaseOutput):
    documents: list[Document] = Field(
        ..., description="The documents returned from the spider"
    )
