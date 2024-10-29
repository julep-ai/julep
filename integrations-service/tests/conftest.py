import pytest
from unittest.mock import patch

from integrations.providers import available_providers
from .mocks.brave import MockBraveSearchClient
from .mocks.email import MockEmailClient
from .mocks.spider import MockSpiderClient
from .mocks.weather import MockWeatherClient
from .mocks.wikipedia import MockWikipediaClient


@pytest.fixture(autouse=True)
def mock_external_services():
    """Automatically mock all external service clients"""
    with patch("langchain_community.tools.BraveSearch", MockBraveSearchClient), patch(
        "smtplib.SMTP", MockEmailClient
    ), patch(
        "langchain_community.document_loaders.SpiderLoader", MockSpiderClient
    ), patch(
        "langchain_community.utilities.OpenWeatherMapAPIWrapper", MockWeatherClient
    ), patch(
        "langchain_community.document_loaders.WikipediaLoader", MockWikipediaClient
    ):
        yield


@pytest.fixture
def providers():
    """Fixture that provides access to all available integration providers"""
    return available_providers


@pytest.fixture
def wikipedia_provider():
    """Fixture that provides access to the Wikipedia provider"""
    return available_providers["wikipedia"]


@pytest.fixture
def weather_provider():
    """Fixture that provides access to the Weather provider"""
    return available_providers["weather"]


@pytest.fixture
def spider_provider():
    """Fixture that provides access to the Spider provider"""
    return available_providers["spider"]


@pytest.fixture
def brave_provider():
    """Fixture that provides access to the Brave provider"""
    return available_providers["brave"]


@pytest.fixture
def email_provider():
    """Fixture that provides access to the Email provider"""
    return available_providers["email"]
