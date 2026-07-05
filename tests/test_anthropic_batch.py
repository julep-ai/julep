from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from julep.dotctx import Reasoner
from julep.execution.anthropic_batch import AnthropicBatchProvider
from julep.execution.batch_provider import select_batch_provider
from julep.execution.llm import _parse_reply
from conftest import run
from test_llm import FakeChoice, FakeCompletion, FakeMessage as SyncFakeMessage

HAS_ANTHROPIC = importlib.util.find_spec("anthropic") is not None


@dataclass(frozen=True)
class FakeBlock:
    type: str
    text: str


@dataclass(frozen=True)
class FakeMessage:
    content: list[FakeBlock]
    parsed: Any = None


@dataclass(frozen=True)
class FakeParsed:
    x: int

    def model_dump(self) -> dict[str, int]:
        return {"x": self.x}


@dataclass(frozen=True)
class FakeResultPayload:
    type: str
    message: Any = None


@dataclass(frozen=True)
class FakeEntry:
    custom_id: str
    result: FakeResultPayload


class FakeBatches:
    def __init__(self, entries: list[FakeEntry] | None = None) -> None:
        self.entries = entries or []
        self.created_requests: list[Any] = []

    async def create(self, requests: list[Any]) -> Any:
        self.created_requests = requests
        return SimpleNamespace(id="batch_x")

    async def retrieve(self, batch_id: str) -> Any:
        assert batch_id == "batch_x"
        return SimpleNamespace(processing_status="ended")

    def results(self, batch_id: str) -> Any:
        assert batch_id == "batch_x"

        async def gen() -> Any:
            for entry in self.entries:
                yield entry

        return gen()


class FakeAsyncClient:
    def __init__(self, batches: FakeBatches | None = None) -> None:
        self.messages = SimpleNamespace(batches=batches or FakeBatches())


def test_registers_anthropic_provider() -> None:
    assert isinstance(select_batch_provider("anthropic:claude-x"), AnthropicBatchProvider)


def test_build_request_splits_system_and_messages() -> None:
    provider = AnthropicBatchProvider(client=FakeAsyncClient())
    reasoner = Reasoner(name="b", model="anthropic:claude-x", system="s", reply=None)

    request = provider.build_request("c1", reasoner, "hello")

    assert request["custom_id"] == "c1"
    assert request["params"]["model"] == "claude-x"
    assert request["params"]["max_tokens"] == 1024
    assert "s" in request["params"]["system"]
    assert request["params"]["messages"] == [{"role": "user", "content": "hello"}]


def test_build_request_forwards_effort_and_suppresses_temperature() -> None:
    # BATCH must honor the frozen reasoner's effort like the sync path does;
    # the mapping mirrors any-llm's anthropic translation (codex PR #11).
    provider = AnthropicBatchProvider(client=FakeAsyncClient())
    reasoner = Reasoner(
        name="b", model="anthropic:claude-x", system="s",
        temperature=0.2, reasoning_effort="minimal",
    )

    params = provider.build_request("c1", reasoner, "hello")["params"]

    assert params["thinking"] == {"type": "adaptive"}
    assert params["output_config"] == {"effort": "low"}   # minimal → low
    assert "temperature" not in params


def test_build_request_effort_none_keeps_temperature() -> None:
    provider = AnthropicBatchProvider(client=FakeAsyncClient())
    reasoner = Reasoner(
        name="b", model="anthropic:claude-x", system="s",
        temperature=0.2, reasoning_effort="none",
    )

    params = provider.build_request("c1", reasoner, "hello")["params"]

    assert "thinking" not in params
    assert "output_config" not in params
    assert params["temperature"] == 0.2


def test_build_request_injects_schema_hint_into_system() -> None:
    provider = AnthropicBatchProvider(client=FakeAsyncClient())
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    reasoner = Reasoner(name="b", model="anthropic:claude-x", system="s", reply=schema)

    request = provider.build_request("c1", reasoner, {"input": "hello"})

    system_text = request["params"]["system"]
    assert "s" in system_text
    assert "Reply with a single JSON object" in system_text
    assert '"type": "object"' in system_text
    assert request["params"]["messages"] == [
        {"role": "user", "content": json.dumps({"input": "hello"})}
    ]


@pytest.mark.skipif(not HAS_ANTHROPIC, reason="anthropic SDK not installed")
def test_submit_returns_batch_id() -> None:
    batches = FakeBatches()
    provider = AnthropicBatchProvider(client=FakeAsyncClient(batches))
    requests = [
        {
            "custom_id": "c1",
            "params": {
                "model": "claude-x",
                "max_tokens": 16,
                "system": None,
                "messages": [{"role": "user", "content": "hello"}],
            },
        }
    ]

    assert run(provider.submit(requests)) == "batch_x"
    assert batches.created_requests[0]["custom_id"] == "c1"
    assert batches.created_requests[0]["params"]["model"] == "claude-x"
    assert "system" not in batches.created_requests[0]["params"]


def test_poll_status_maps_ended_to_completed() -> None:
    provider = AnthropicBatchProvider(client=FakeAsyncClient())

    assert run(provider.poll_status("batch_x")) == "completed"


def test_results_and_parse_successful_entries() -> None:
    json_reasoner = Reasoner(
        name="json",
        model="anthropic:claude-x",
        system="s",
        reply={"type": "object"},
    )
    text_reasoner = Reasoner(name="text", model="anthropic:claude-x", system="s")
    batches = FakeBatches(
        [
            FakeEntry(
                "json-1",
                FakeResultPayload(
                    "succeeded",
                    FakeMessage([FakeBlock("text", '```json\n{"x": 1}\n```')]),
                ),
            ),
            FakeEntry(
                "text-1",
                FakeResultPayload("succeeded", FakeMessage([FakeBlock("text", "hello")])),
            ),
        ]
    )
    provider = AnthropicBatchProvider(client=FakeAsyncClient(batches))

    async def collect() -> list[tuple[str, Any]]:
        out = []
        async for custom_id, raw in provider.results("batch_x"):
            reasoner = json_reasoner if custom_id == "json-1" else text_reasoner
            out.append((custom_id, provider.parse(raw, reasoner)))
        return out

    assert run(collect()) == [("json-1", {"x": 1}), ("text-1", "hello")]


def test_parse_structured_entry_matches_shared_llm_parser() -> None:
    provider = AnthropicBatchProvider(client=FakeAsyncClient())
    reasoner = Reasoner(
        name="json",
        model="anthropic:claude-x",
        system="s",
        reply={"type": "object"},
    )
    parsed = FakeParsed(7)
    raw = FakeMessage([FakeBlock("text", '{"x": 0}')], parsed=parsed)
    sync_completion = FakeCompletion(
        choices=[FakeChoice(SyncFakeMessage(content='{"x": 0}', parsed=parsed))]
    )

    assert provider.parse(raw, reasoner) == _parse_reply(sync_completion, expect_json=True)


def test_parse_entry_error_raises() -> None:
    batches = FakeBatches([FakeEntry("c1", FakeResultPayload("errored"))])
    provider = AnthropicBatchProvider(client=FakeAsyncClient(batches))
    reasoner = Reasoner(name="b", model="anthropic:claude-x", system="s")

    async def collect() -> None:
        async for _, raw in provider.results("batch_x"):
            provider.parse(raw, reasoner)

    with pytest.raises(RuntimeError, match="batch entry errored"):
        run(collect())
