"""The response_format fallback is recorded + logged, never silent (G-8)."""
import asyncio
import logging
from types import SimpleNamespace
from typing import Any

import pytest

from composable_agents.dotctx import Reasoner
from composable_agents.execution.llm import complete_reasoner

SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}}}


def _completion(content: str) -> Any:
    msg = SimpleNamespace(content=content, parsed=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=None, model="m")


def test_fallback_recorded_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    calls: list[dict[str, Any]] = []

    async def flaky(**kwargs: Any) -> Any:
        calls.append(kwargs)
        if "response_format" in kwargs:
            raise RuntimeError("native structured output unsupported")
        return _completion('{"x": 1}')

    r = Reasoner(name="t", model="openai:gpt-4o", reply=SCHEMA)
    with caplog.at_level(logging.WARNING, "composable_agents.execution.llm"):
        result = asyncio.run(complete_reasoner(r, "hi", acompletion=flaky))

    assert result.reply == {"x": 1}
    assert len(calls) == 2
    assert result.meta.response_format_fallback is not None
    assert "native structured output unsupported" in result.meta.response_format_fallback
    assert result.meta.to_attrs()["llm.response_format_fallback"] == (
        result.meta.response_format_fallback)
    assert any("response_format" in rec.message for rec in caplog.records)


def test_no_fallback_attr_on_clean_native() -> None:
    async def ok(**kwargs: Any) -> Any:
        return _completion('{"x": 1}')

    r = Reasoner(name="t", model="openai:gpt-4o", reply=SCHEMA)
    result = asyncio.run(complete_reasoner(r, "hi", acompletion=ok))
    assert result.meta.response_format_fallback is None
    assert "llm.response_format_fallback" not in result.meta.to_attrs()


def test_bad_request_on_response_format_still_falls_back() -> None:
    # A provider rejecting only response_format surfaces as a 400; that must
    # reach the prompt-injected fallback, not die as CONFIG (codex PR #11).
    class BadRequest(Exception):
        status_code = 400

    calls: list[dict[str, Any]] = []

    async def rejects_native(**kwargs: Any) -> Any:
        calls.append(kwargs)
        if "response_format" in kwargs:
            raise BadRequest("response_format is not supported for this model")
        return _completion('{"x": 1}')

    r = Reasoner(name="t", model="openai:gpt-4o", reply=SCHEMA)
    result = asyncio.run(complete_reasoner(r, "hi", acompletion=rejects_native))
    assert result.reply == {"x": 1}
    assert len(calls) == 2
    assert result.meta.response_format_fallback is not None


def test_config_error_not_masked_by_fallback() -> None:
    class AuthError(Exception):
        status_code = 401

    async def unauthorized(**kwargs: Any) -> Any:
        if "response_format" in kwargs:
            raise AuthError("invalid api key")
        return _completion('{"x": 1}')   # fallback would "succeed" — must not run

    r = Reasoner(name="t", model="openai:gpt-4o", reply=SCHEMA)
    with pytest.raises(AuthError):
        asyncio.run(complete_reasoner(r, "hi", acompletion=unauthorized))
