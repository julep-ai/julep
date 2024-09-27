from pydantic import BaseModel, Field


class SpiderExecutionSetup(BaseModel):
    spider_api_key: str = Field(
        ..., description="The request for which to fetch data"
    ) 

class SpiderExecutionArguments(BaseModel):
    query: str = Field(
        ..., description="The url for which to fetch data"
    )
    mode: str = Field('scrape', description="The type of crawlers")
    params: dict = Field(None, description="The parameters for the Spider API")