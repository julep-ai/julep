from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from typing import Any

import pytest

import composable_agents.execution.openai_batch as openai_batch
from composable_agents.dotctx import Brain
from composable_agents.execution.batch_provider import select_batch_provider
from conftest import run

HAS_OPENAI = importlib.util.find_spec("openai") is not None


@dataclass(frozen=True)
class FakeFile:
    id: str


@dataclass(frozen=True)
class FakeBatch:
    id: str
    status: str = "pending"
    output_file_id: str | None = None


@dataclass(frozen=True)
class FakeTextContent:
    text: str


@dataclass(frozen=True)
class FakeReadContent:
    payload: bytes

    def read(self) -> bytes:
        return self.payload


class FakeFiles:
    def __init__(self, content_by_id: dict[str, Any] | None = None) -> None:
        self.content_by_id = content_by_id or {}
        self.create_calls: list[dict[str, Any]] = []

    async def create(self, *, file: Any, purpose: str) -> Any:
        data = file.read() if hasattr(file, "read") else file
        if isinstance(data, str):
            data = data.encode()
        self.create_calls.append({"file": data, "purpose": purpose})
        return FakeFile(f"file_{len(self.create_calls)}")

    async def content(self, file_id: str) -> Any:
        return self.content_by_id[file_id]


class FakeBatches:
    def __init__(
        self,
        *,
        statuses: dict[str, str] | None = None,
        output_file_ids: dict[str, str] | None = None,
    ) -> None:
        self.statuses = statuses or {}
        self.output_file_ids = output_file_ids or {}
        self.create_calls: list[dict[str, Any]] = []

    async def create(
        self,
        *,
        input_file_id: str,
        endpoint: str,
        completion_window: str,
    ) -> Any:
        batch_id = f"batch_{len(self.create_calls) + 1}"
        self.create_calls.append(
            {
                "input_file_id": input_file_id,
                "endpoint": endpoint,
                "completion_window": completion_window,
            }
        )
        self.statuses.setdefault(batch_id, "completed")
        self.output_file_ids.setdefault(batch_id, f"out_{batch_id}")
        return FakeBatch(
            id=batch_id,
            status=self.statuses[batch_id],
            output_file_id=self.output_file_ids[batch_id],
        )

    async def retrieve(self, batch_id: str) -> Any:
        return FakeBatch(
            id=batch_id,
            status=self.statuses[batch_id],
            output_file_id=self.output_file_ids.get(batch_id),
        )


class FakeOpenAIClient:
    def __init__(
        self,
        *,
        files: FakeFiles | None = None,
        batches: FakeBatches | None = None,
    ) -> None:
        self.files = files or FakeFiles()
        self.batches = batches or FakeBatches()


def _request(custom_id: str, model: str) -> dict[str, Any]:
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "messages": [{"role": "user", "content": custom_id}],
            "max_tokens": 16,
        },
    }


def _jsonl_rows(payload: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in payload.decode().splitlines()]


def test_registers_openai_provider() -> None:
    assert isinstance(
        select_batch_provider("openai:gpt-x"),
        openai_batch.OpenAIBatchProvider,
    )


def test_build_request_chat_completions_shape() -> None:
    provider = openai_batch.OpenAIBatchProvider(client=FakeOpenAIClient())
    brain = Brain(name="b", model="openai:gpt-x", system="s", reply_schema=None)

    request = provider.build_request("c1", brain, "hello")

    assert request["custom_id"] == "c1"
    assert request["method"] == "POST"
    assert request["url"] == "/v1/chat/completions"
    assert request["body"]["model"] == "gpt-x"
    assert request["body"]["max_tokens"] == 1024
    assert request["body"]["messages"][-1] == {"role": "user", "content": "hello"}


def test_build_request_injects_response_format_for_schema() -> None:
    provider = openai_batch.OpenAIBatchProvider(client=FakeOpenAIClient())
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    brain = Brain(name="b", model="openai:gpt-x", system="s", reply_schema=schema)

    request = provider.build_request("c1", brain, {"input": "hello"})

    response_format = request["body"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["schema"] == schema
    assert request["body"]["messages"][-1] == {
        "role": "user",
        "content": json.dumps({"input": "hello"}),
    }


def test_submit_sub_splits_by_model_into_two_batches() -> None:
    client = FakeOpenAIClient()
    provider = openai_batch.OpenAIBatchProvider(client=client)
    requests = [_request("c1", "gpt-a"), _request("c2", "gpt-b")]

    batch_id = run(provider.submit(requests))

    assert set(batch_id.split(",")) == {"batch_1", "batch_2"}
    assert len(client.files.create_calls) == 2
    assert len(client.batches.create_calls) == 2
    assert [call["purpose"] for call in client.files.create_calls] == [
        "batch",
        "batch",
    ]
    assert all(
        call["endpoint"] == "/v1/chat/completions"
        and call["completion_window"] == "24h"
        for call in client.batches.create_calls
    )

    uploaded = [_jsonl_rows(call["file"]) for call in client.files.create_calls]
    assert [[row["custom_id"] for row in rows] for rows in uploaded] == [
        ["c1"],
        ["c2"],
    ]
    assert [{row["body"]["model"] for row in rows} for rows in uploaded] == [
        {"gpt-a"},
        {"gpt-b"},
    ]


def test_submit_single_model_one_batch() -> None:
    client = FakeOpenAIClient()
    provider = openai_batch.OpenAIBatchProvider(client=client)
    requests = [_request("c1", "gpt-a"), _request("c2", "gpt-a")]

    batch_id = run(provider.submit(requests))

    assert batch_id == "batch_1"
    assert len(client.files.create_calls) == 1
    assert len(client.batches.create_calls) == 1
    rows = _jsonl_rows(client.files.create_calls[0]["file"])
    assert [row["custom_id"] for row in rows] == [
        "c1",
        "c2",
    ]


def test_poll_status_all_completed() -> None:
    client = FakeOpenAIClient(
        batches=FakeBatches(statuses={"b1": "completed", "b2": "completed"})
    )
    provider = openai_batch.OpenAIBatchProvider(client=client)

    assert run(provider.poll_status("b1,b2")) == "completed"


def test_poll_status_any_failed() -> None:
    client = FakeOpenAIClient(
        batches=FakeBatches(statuses={"b1": "completed", "b2": "failed"})
    )
    provider = openai_batch.OpenAIBatchProvider(client=client)

    assert run(provider.poll_status("b1,b2")) == "failed"


def test_poll_status_else_pending() -> None:
    client = FakeOpenAIClient(
        batches=FakeBatches(statuses={"b1": "completed", "b2": "in_progress"})
    )
    provider = openai_batch.OpenAIBatchProvider(client=client)

    assert run(provider.poll_status("b1,b2")) == "pending"


def test_results_and_parse_success_and_error() -> None:
    text_body = {"choices": [{"message": {"content": "hello"}}]}
    json_body = {"choices": [{"message": {"content": '```json\n{"x": 1}\n```'}}]}
    files = FakeFiles(
        {
            "out_b1": FakeTextContent(
                json.dumps(
                    # Real OpenAI success lines carry ``"error": null``; a bare
                    # key check must NOT treat this as a per-entry failure.
                    {
                        "custom_id": "text-1",
                        "response": {"body": text_body},
                        "error": None,
                    }
                )
                + "\n"
            ),
            "out_b2": FakeReadContent(
                (
                    json.dumps(
                        {
                            "custom_id": "json-1",
                            "response": {"body": json_body},
                            "error": None,
                        }
                    )
                    + "\n"
                    + json.dumps(
                        {"custom_id": "bad-1", "error": {"message": "boom"}}
                    )
                    + "\n"
                ).encode()
            ),
        }
    )
    batches = FakeBatches(
        statuses={"b1": "completed", "b2": "completed"},
        output_file_ids={"b1": "out_b1", "b2": "out_b2"},
    )
    provider = openai_batch.OpenAIBatchProvider(
        client=FakeOpenAIClient(files=files, batches=batches)
    )
    text_brain = Brain(name="text", model="openai:gpt-x", system="s")
    json_brain = Brain(
        name="json",
        model="openai:gpt-x",
        system="s",
        reply_schema={"type": "object"},
    )

    async def collect() -> dict[str, Any]:
        out = {}
        async for custom_id, raw in provider.results("b1,b2"):
            out[custom_id] = raw
        return out

    raw_by_id = run(collect())

    assert provider.parse(raw_by_id["text-1"], text_brain) == "hello"
    assert provider.parse(raw_by_id["json-1"], json_brain) == {"x": 1}
    with pytest.raises(RuntimeError, match="batch entry"):
        provider.parse(raw_by_id["bad-1"], text_brain)
