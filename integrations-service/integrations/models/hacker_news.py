from pydantic import BaseModel, Field


class HackerNewsExecutionArguments(BaseModel):
    url: str = Field(..., description="The URL of the Hacker News thread to fetch")
