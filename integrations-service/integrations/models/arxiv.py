from pydantic import BaseModel, Field

from .base_models import BaseOutput


class ArxivSearchResult(BaseModel):
    entry_id: str | None = None
    title: str | None = None
    updated: str | None = None
    published: str | None = None
    authors: list[str] | None = None
    summary: str | None = None
    comment: str | None = None
    journal_ref: str | None = None
    doi: str | None = None
    primary_category: str | None = None
    categories: list[str] | None = None
    links: list[str] | None = None
    pdf_url: str | None = None
    pdf_downloaded: dict | None = None


class ArxivSearchOutput(BaseOutput):
    result: list[ArxivSearchResult] = Field(..., description="A list of search results")
