from pydantic import BaseModel, Field


class WikipediaExecutionArguments(BaseModel):
    query: str = Field(..., description="The search query string")
    load_max_docs: int = Field(2, description="Maximum number of documents to load")
