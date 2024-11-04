"""Mock implementation of Brave Search API client"""

from typing import Optional


class MockBraveSearchClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, query: str) -> str:
        """Mock search that returns a fixed response"""
        return f"Mock Brave search results for: {query}"


class MockBraveSearchException(Exception):
    """Mock exception for Brave Search errors"""

    pass
