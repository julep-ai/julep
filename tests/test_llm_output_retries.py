import asyncio
from types import SimpleNamespace
from typing import Any

from composable_agents.dotctx import Reasoner
from composable_agents.execution.llm import complete_reasoner

SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}}}


def _completion(content: str) -> Any:
    msg = SimpleNamespace(content=content, parsed=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=None, model="m")


def _reasoner(retries: int) -> Reasoner:
    return Reasoner(name="t", model="gemini:gemini-2.5-flash",  # prompt-fallback provider: single path
                    reply=SCHEMA, output_retries=retries)


def test_reask_until_parse() -> None:
    replies = iter(["not json", "still not json", '{"x": 2}'])

    async def acompletion(**kwargs: Any) -> Any:
        return _completion(next(replies))

    result = asyncio.run(complete_reasoner(_reasoner(2), "hi", acompletion=acompletion))
    assert result.reply == {"x": 2}
    assert result.meta.output_retries_used == 2
    assert result.meta.to_attrs()["llm.output_retries"] == 2


def test_exhausted_returns_last_raw_reply() -> None:
    async def acompletion(**kwargs: Any) -> Any:
        return _completion("garbage")

    result = asyncio.run(complete_reasoner(_reasoner(1), "hi", acompletion=acompletion))
    assert result.reply == "garbage"          # resilient caller/strict interpret escalates from here
    assert result.meta.output_retries_used == 1


def test_reask_carries_corrective_message() -> None:
    seen_messages: list[list[dict]] = []
    replies = iter(["not json", '{"x": 2}'])

    async def acompletion(**kwargs: Any) -> Any:
        seen_messages.append(kwargs["messages"])
        return _completion(next(replies))

    asyncio.run(complete_reasoner(_reasoner(1), "hi", acompletion=acompletion))
    assert len(seen_messages) == 2
    assert "not a single valid JSON object" in seen_messages[1][-1]["content"]
    assert len(seen_messages[1]) == len(seen_messages[0]) + 1


def test_usage_accumulates_across_reasks() -> None:
    # Every attempt costs tokens; the meta must report all of them, not just
    # the final completion's (codex PR #11 review).
    replies = iter(["not json", '{"x": 2}'])

    async def acompletion(**kwargs: Any) -> Any:
        completion = _completion(next(replies))
        completion.usage = SimpleNamespace(
            prompt_tokens=10, completion_tokens=5, total_tokens=15)
        return completion

    result = asyncio.run(complete_reasoner(_reasoner(1), "hi", acompletion=acompletion))
    assert result.reply == {"x": 2}
    assert result.meta.input_tokens == 20
    assert result.meta.output_tokens == 10
    assert result.meta.total_tokens == 30


def test_usage_none_stays_none_when_no_attempt_reports() -> None:
    async def acompletion(**kwargs: Any) -> Any:
        return _completion('{"x": 2}')

    result = asyncio.run(complete_reasoner(_reasoner(0), "hi", acompletion=acompletion))
    assert result.meta.input_tokens is None
    assert result.meta.total_tokens is None


def test_zero_retries_is_single_call() -> None:
    calls = []

    async def acompletion(**kwargs: Any) -> Any:
        calls.append(1)
        return _completion("garbage")

    asyncio.run(complete_reasoner(_reasoner(0), "hi", acompletion=acompletion))
    assert len(calls) == 1
