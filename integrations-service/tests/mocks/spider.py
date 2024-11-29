"""Mock implementation of web spider client"""

from typing import List
from langchain_core.documents import Document
from pydantic import AnyUrl


class MockSpiderClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def crawl(self, url: AnyUrl, mode: str = "scrape") -> List[Document]:
        """Mock crawl that returns fixed documents"""
        return [
            Document(
                page_content="Mock crawled content 1", metadata={"source": str(url)}
            ),
            Document(
                page_content="Mock crawled content 2", metadata={"source": str(url)}
            ),
        ]


class MockSpiderException(Exception):
    """Mock exception for spider errors"""

    pass
