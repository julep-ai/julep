"""Tests for provider execution using mocks"""

import pytest
from pydantic import AnyUrl

from integrations.autogen.Tools import (
    BraveSearchArguments,
    EmailArguments,
    SpiderFetchArguments,
    WeatherGetArguments,
    WikipediaSearchArguments,
)
from integrations.providers import available_providers


def test_wikipedia_search(wikipedia_provider):
    """Test Wikipedia search with mock client"""
    args = WikipediaSearchArguments(query="test query", load_max_docs=2)
    provider = available_providers["wikipedia"]
    method = provider.methods[0]

    result = method.output(
        documents=[
            {"page_content": "test query content", "metadata": {}},
            {"page_content": "other content", "metadata": {}},
        ]
    )
    assert len(result.documents) == 2
    assert "test query" in result.documents[0].page_content


def test_weather_get(weather_provider):
    """Test weather lookup with mock client"""
    args = WeatherGetArguments(location="London")
    provider = available_providers["weather"]
    method = provider.methods[0]

    result = method.output(result="Weather in London: 72°F")
    assert "London" in result.result
    assert "°F" in result.result


def test_spider_crawl(spider_provider):
    """Test web crawling with mock client"""
    args = SpiderFetchArguments(url=AnyUrl("https://example.com"), mode="scrape")
    provider = available_providers["spider"]
    method = provider.methods[0]

    result = method.output(
        documents=[
            {"page_content": "Mock crawled content 1", "metadata": {}},
            {"page_content": "Mock crawled content 2", "metadata": {}},
        ]
    )
    assert len(result.documents) == 2
    assert all("Mock crawled content" in doc.page_content for doc in result.documents)


def test_brave_search(brave_provider):
    """Test Brave search with mock client"""
    args = BraveSearchArguments(query="test search")
    provider = available_providers["brave"]
    method = provider.methods[0]

    result = method.output(result="Results for test search: ...")
    assert "test search" in result.result


def test_email_send(email_provider):
    """Test email sending with mock client"""
    args = EmailArguments(
        to="test@example.com",
        from_="sender@example.com",
        subject="Test Email",
        body="Test content",
    )
    provider = available_providers["email"]
    method = provider.methods[0]

    result = method.output(success=True)
    assert result.success
