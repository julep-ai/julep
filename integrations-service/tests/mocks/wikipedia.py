"""Mock implementation of Wikipedia API client"""

from typing import List
from langchain_core.documents import Document


class MockWikipediaClient:
    def __init__(self, query: str, load_max_docs: int = 2):
        """Mock Wikipedia search that returns fixed documents"""
        self.result = [
            Document(
                page_content=f"Mock Wikipedia content about {query}",
                metadata={"source": f"wikipedia/{query}"},
            )
            for _ in range(load_max_docs)
        ]

    def load(self, *args, **kwargs) -> List[Document]:
        return self.result


class MockWikipediaException(Exception):
    """Mock exception for Wikipedia API errors"""

    pass
