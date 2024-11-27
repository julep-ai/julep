from typing import List, Optional

from pydantic import BaseModel, Field

from .base_models import BaseOutput


class ArxivSearchResult(BaseModel):
    entry_id: Optional[str] = None
    title: Optional[str] = None
    updated: Optional[str] = None
    published: Optional[str] = None
    authors: Optional[List[str]] = None
    summary: Optional[str] = None
    comment: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    primary_category: Optional[str] = None
    categories: Optional[List[str]] = None
    links: Optional[List[str]] = None
    pdf_url: Optional[str] = None
    pdf_downloaded: Optional[dict] = None


class ArxivSearchOutput(BaseOutput):
    result: List[ArxivSearchResult] = Field(..., description="A list of search results")
