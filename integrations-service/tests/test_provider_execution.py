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
from integrations.utils.execute_integration import execute_integration


async def test_weather_get_mock(weather_provider):
    """Test weather lookup with mock client"""
    result = await execute_integration(
        provider="weather",
        method="get",
        arguments=WeatherGetArguments(location="London"),
    )

    assert "London" in result.result


async def test_weather_get_direct():
    """Test weather lookup with mock client"""
    result = await execute_integration(
        provider="weather",
        method="get",
        arguments=WeatherGetArguments(location="London"),
    )

    assert "London" in result.result


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
