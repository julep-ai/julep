from __future__ import annotations

import json
from typing import Any

import pytest

from julep.dotctx import Reasoner
from julep.execution import batch_provider
from julep.execution.batch_provider import (
    BatchProvider,
    register_batch_provider,
    select_batch_provider,
)
from test_llm import FakeChoice, FakeCompletion, FakeMessage


class Fake(BatchProvider):
    def build_request(
        self,
        custom_id: str,
        reasoner: Any,
        value: Any,
        *,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> dict[str, Any]:
        return {"custom_id": custom_id}

    async def submit(self, requests: list[dict[str, Any]]) -> str:
        return "b1"

    async def poll_status(self, batch_id: str) -> str:
        return "completed"

    async def results(self, batch_id: str) -> Any:
        return []


def _completion(content: str) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(FakeMessage(content=content))])


def test_batch_provider_is_abc() -> None:
    with pytest.raises(TypeError):
        BatchProvider()

    assert BatchProvider.__abstractmethods__.issuperset(
        {"build_request", "submit", "poll_status", "results"}
    )
    assert "parse" not in BatchProvider.__abstractmethods__


def test_select_batch_provider_unregistered_raises() -> None:
    with pytest.raises(NotImplementedError, match="missingp"):
        select_batch_provider("missingp:claude-x")

    with pytest.raises(NotImplementedError, match="otherp"):
        select_batch_provider("otherp:gpt-x")

    with pytest.raises(NotImplementedError, match="missingdefault"):
        select_batch_provider("claude-x", default_provider="missingdefault")


def test_register_and_select() -> None:
    register_batch_provider("fakep", Fake)
    try:
        assert isinstance(select_batch_provider("fakep:m"), Fake)
    finally:
        del batch_provider._PROVIDERS["fakep"]


def test_parse_reuses_llm_parse_reply() -> None:
    provider = Fake()
    reasoner_json = Reasoner(
        name="t",
        model="m",
        system="s",
        reply={"type": "object"},
    )
    assert provider.parse(_completion(json.dumps({"k": 1})), reasoner_json) == {"k": 1}

    reasoner_text = Reasoner(name="t2", model="m", system="s", reply=None)
    assert provider.parse(_completion("hello"), reasoner_text) == "hello"
