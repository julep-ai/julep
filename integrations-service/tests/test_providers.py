import pytest
from integrations.models import BaseProvider, BaseProviderMethod, ProviderInfo


def test_available_providers(providers):
    """Test that the available providers dictionary is properly structured"""
    assert isinstance(providers, dict)
    assert all(isinstance(key, str) for key in providers.keys())
    assert all(isinstance(value, BaseProvider) for value in providers.values())


def test_provider_structure(providers):
    """Test that each provider has the required attributes"""
    for provider_name, provider in providers.items():
        assert isinstance(provider.provider, str)
        assert isinstance(provider.methods, list)
        assert all(
            isinstance(method, BaseProviderMethod) for method in provider.methods
        )
        assert isinstance(provider.info, ProviderInfo)


def test_wikipedia_provider(wikipedia_provider):
    """Test Wikipedia provider specific configuration"""
    assert wikipedia_provider.provider == "wikipedia"
    assert wikipedia_provider.setup is None
    assert len(wikipedia_provider.methods) == 1
    assert wikipedia_provider.methods[0].method == "search"


def test_weather_provider(weather_provider):
    """Test Weather provider specific configuration"""
    assert weather_provider.provider == "weather"
    assert weather_provider.setup is not None
    assert len(weather_provider.methods) == 1
    assert weather_provider.methods[0].method == "get"


def test_llama_parse_provider(llama_parse_provider):
    """Test LlamaParse provider specific configuration"""
    assert llama_parse_provider.provider == "llama_parse"
    assert llama_parse_provider.setup is not None
    assert len(llama_parse_provider.methods) == 1
    assert llama_parse_provider.methods[0].method == "parse"
