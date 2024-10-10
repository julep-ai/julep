from pydantic import BaseModel, Field


class DuckDuckGoSearchExecutionArguments(BaseModel):
    query: str = Field(..., description="The search query string")
