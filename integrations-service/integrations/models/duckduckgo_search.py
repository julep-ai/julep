from pydantic import BaseModel, Field


class DuckDuckGoSearchExecutionParams(BaseModel):
    query: str = Field(..., description="The search query string")
