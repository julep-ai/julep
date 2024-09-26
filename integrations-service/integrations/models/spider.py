from pydantic import BaseModel, Field


class SpiderExecutionSetup(BaseModel):
    spider_api_key: str = Field(
        ..., description="The request for which to fetch data"
    )
    

class SpiderExecutionArguments(BaseModel):
    query: str = Field(
        ..., description="The query for which to fetch data"
    )
    metadata: bool = Field(True, description="Whether to include metadata in the response")
    limit: int = Field(50, description="The maximum number of items to return")
    base_url: str = Field('https://api.spider.cloud/crawl', description="The base URL for the Spider API")
    return_format: str = Field('markdown', description="The format in which to return the data")
    request: str = Field('smart', description="The request method to use when fetching data")