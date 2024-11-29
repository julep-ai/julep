"""Mock implementation of llama parse client"""

from typing import List, Dict
from llama_index.core.schema import Document


class MockLlamaParseClient:
    def __init__(self, api_key: str, result_type: str, num_workers: int, language: str):
        self.api_key = api_key
        self.result_type = result_type
        self.num_workers = num_workers
        self.language = language

    async def aload_data(self, file_content: bytes, extra_info: dict) -> List[Dict]:
        """Mock loading data that returns fixed documents"""
        return [
            Document(page_content="Mock document content 1", metadata=extra_info),
            Document(page_content="Mock document content 2", metadata=extra_info),
        ]


class MockLlamaParseException(Exception):
    """Mock exception for llama parse errors"""

    pass
