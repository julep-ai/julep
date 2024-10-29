"""Mock implementation of Wikipedia API client"""

from typing import List
from langchain_core.documents import Document


class MockWikipediaClient:
    def search(self, query: str, load_max_docs: int = 2) -> List[Document]:
        """Mock Wikipedia search that returns fixed documents"""
        return [
            Document(
                page_content=f"Mock Wikipedia content about {query}",
                metadata={"source": f"wikipedia/{query}"},
            )
            for _ in range(load_max_docs)
        ]


class MockWikipediaException(Exception):
    """Mock exception for Wikipedia API errors"""

    pass
