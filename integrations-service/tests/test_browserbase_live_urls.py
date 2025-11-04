import sys
import types
from unittest.mock import AsyncMock

import pytest

# Create minimal stubs for the external browserbase package so the module can be imported
browserbase_stub = types.ModuleType("browserbase")
browserbase_stub.Browserbase = object

session_live_urls_module = types.ModuleType("browserbase.types.session_live_urls")


class SessionLiveURLs:
    def __init__(self, url: str = ""):
        self.url = url


session_live_urls_module.SessionLiveURLs = SessionLiveURLs
sys.modules.setdefault("browserbase", browserbase_stub)
sys.modules.setdefault("browserbase.types", types.ModuleType("browserbase.types"))
sys.modules.setdefault("browserbase.types.session_live_urls", session_live_urls_module)

from integrations.autogen.Tools import (
    BrowserbaseGetSessionLiveUrlsArguments,
    BrowserbaseSetup,
)
from integrations.models.browserbase import BrowserbaseGetSessionLiveUrlsOutput
from integrations.utils.integrations import browserbase


@pytest.mark.asyncio
async def test_get_live_urls_uses_to_thread(monkeypatch):
    mock_client = types.SimpleNamespace()
    mock_client.sessions = types.SimpleNamespace(debug=AsyncMock())

    monkeypatch.setattr(browserbase, "get_browserbase_client", lambda setup: mock_client)

    expected_urls = SessionLiveURLs("http://example.com")
    to_thread_mock = AsyncMock(return_value=expected_urls)
    monkeypatch.setattr(browserbase.asyncio, "to_thread", to_thread_mock)

    setup = BrowserbaseSetup(api_key="k", project_id="p")
    args = BrowserbaseGetSessionLiveUrlsArguments(id="123")
    result = await browserbase.get_live_urls(setup, args)

    assert isinstance(result, BrowserbaseGetSessionLiveUrlsOutput)
    assert result.urls is expected_urls
    to_thread_mock.assert_awaited_once_with(mock_client.sessions.debug, id="123")
    mock_client.sessions.debug.assert_not_called()
