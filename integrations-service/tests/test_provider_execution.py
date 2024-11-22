"""Tests for provider execution using mocks"""

import pytest

from integrations.autogen.Tools import (
    WikipediaSearchArguments,
)
from integrations.utils.execute_integration import execute_integration


@pytest.mark.asyncio
async def test_weather_get_mock(wikipedia_provider):
    """Test wikipedia lookup with mock client"""
    query = "London"

    result = await execute_integration(
        provider="wikipedia",
        method="search",
        arguments=WikipediaSearchArguments(query=query),
    )

    assert len(result.documents) > 0
    assert any([(query in doc.page_content) for doc in result.documents])


# @pytest.mark.asyncio
# async def test_weather_get_direct():
#     """Test weather lookup with mock client"""
#     raise NotImplementedError


# def test_weather_get_mock(weather_provider):
#     """Test weather lookup with mock client"""
#     raise NotImplementedError


# def test_spider_crawl(spider_provider):
#     """Test web crawling with mock client"""
#     raise NotImplementedError


# def test_brave_search(brave_provider):
#     """Test Brave search with mock client"""
#     raise NotImplementedError


# def test_email_send(email_provider):
#     """Test email sending with mock client"""
#     raise NotImplementedError
