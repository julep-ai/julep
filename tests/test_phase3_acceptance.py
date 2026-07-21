"""Phase 3 acceptance gate: a mem-mcp-shaped tool-loop fixture (record/execute
semantics — 3 mock tools, require_tool_call, max_rounds=12,
round_note="std.rounds_remaining_note") driven through drive_agent_loop with a
scripted provider, asserting the four acceptance behaviors together:

1. parallel (CALL_MANY) calls execute effect-fenced (reads concurrent, write after);
2. a raising tool becomes an error observation the controller recovers from;
3. the transcript replays in provider (OpenAI/Anthropic) tool-call grammar;
4. `julep eval` scores the run against the fixture eval suite with threshold +
   baseline regression gates.

No live provider and no temporal are needed: effects are injected callables and
the eval seam takes a fake ``acompletion``.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pytest

pytest.importorskip("jinja2")
pytest.importorskip("yglu")  # the fixture settings carry a `!?` env expression

from julep.agent_loop import ROUND_NOTE_KEY, AgentConfig, drive_agent_loop
from julep.cli.main import main
from julep.cli.evalrun import _run_tool_loop, diff_reports, run_eval
from julep.dotctx import load_dotctx
from julep.dotctx_evals import Sample, stop_after_turns
from julep.dotctx_rich import load_rich_dotctx
from conftest import run

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "memmcp" / "record_execute.ctx"
ROUND_NOTE = "std.rounds_remaining_note"
CONTRACTS = {
    "search": {"effect": "read"},
    "recall": {"effect": "read"},
    "record_memory": {"effect": "write"},
}
GRANTED = {"search", "recall", "record_memory"}


def _acceptance_cfg() -> AgentConfig:
    return AgentConfig(
        native_tools=True,
        require_tool_call=True,
        max_rounds=12,
        round_note=ROUND_NOTE,
    )


# --------------------------------------------------------------------------- #
# Provider-completion fakes for the `julep eval` seam (mirrors tests/julep conventions)
# --------------------------------------------------------------------------- #
@dataclass
class FakeMessage:
    content: Optional[str] = None
    parsed: Any = None
    tool_calls: Any = None


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]


@dataclass
class FakeFunction:
    name: str
    arguments: str


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunction


def _content(text: str) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(FakeMessage(content=text))])


def _tool_call(call_id: str, name: str, args_json: str) -> FakeCompletion:
    return FakeCompletion(
        choices=[FakeChoice(FakeMessage(tool_calls=[FakeToolCall(call_id, FakeFunction(name, args_json))]))]
    )


def _user_task(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content")
            return content if isinstance(content, str) else json.dumps(content)
    return ""


class GoodRecordExecuteFake:
    """Dispatches to the tool named by the task, then finishes in prose once it
    sees the tool observation. Every sample's must_call tool gets called."""

    async def __call__(self, **kwargs: Any) -> FakeCompletion:
        messages = kwargs["messages"]
        if any(m.get("role") == "tool" for m in messages):
            return _content("done: side effects applied")
        task = _user_task(messages)
        if "search" in task:
            return _tool_call("c1", "search", json.dumps({"query": "q"}))
        if "recall" in task:
            return _tool_call("c1", "recall", json.dumps({"key": "k"}))
        return _tool_call("c1", "record_memory", json.dumps({"content": "x"}))


class SilentBadFake:
    """A regressed model: answers in text and never calls a tool. Under
    require_tool_call the loop re-asks twice then halts controller_error, whose
    error-bearing trace scores 0 — exactly the regression an eval gate must catch."""

    async def __call__(self, **kwargs: Any) -> FakeCompletion:
        return _content("I will not call any tools")


class CapturingRecordFake:
    """Records the provider messages seen each round, then finishes after the
    first tool result. Used to prove the next round replays in provider grammar."""

    def __init__(self) -> None:
        self.rounds: list[list[dict[str, Any]]] = []

    async def __call__(self, **kwargs: Any) -> FakeCompletion:
        messages = kwargs["messages"]
        self.rounds.append(messages)
        if any(m.get("role") == "tool" for m in messages):
            return _content("done: stored")
        return _tool_call("call_rec", "record_memory", json.dumps({"content": "hi"}))


# --------------------------------------------------------------------------- #
# 0. The fixture is record/execute-shaped: 3 tools, require_tool_call, max_rounds=12.
# --------------------------------------------------------------------------- #
def test_acceptance_fixture_is_record_execute_shaped() -> None:
    reasoner = load_dotctx(str(FIXTURE), env={})
    assert set(reasoner.tools) == {"record_memory", "search", "recall"}
    assert reasoner.require_tool_call is True
    assert reasoner.max_rounds == 12


# --------------------------------------------------------------------------- #
# 1. Parallel (CALL_MANY) calls execute effect-fenced: reads concurrent, write after.
# --------------------------------------------------------------------------- #
def test_acceptance_parallel_calls_execute_effect_fenced() -> None:
    events: list[str] = []
    started: set[str] = set()
    both_reads_started = asyncio.Event()
    payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        payloads.append(payload)
        if len(payloads) == 1:
            return {
                "tool_calls": [
                    {"id": "s", "tool": "search", "input": {"query": "q"}},
                    {"id": "r", "tool": "recall", "input": {"key": "k"}},
                    {"id": "w", "tool": "record_memory", "input": {"content": "c"}},
                ]
            }
        return {"done": True, "output": payload["input"]}

    async def call_tool(name: str, value: Any, *, call_index: Optional[int] = None) -> Any:
        del call_index
        events.append(f"{name}:start")
        if name in ("search", "recall"):
            started.add(name)
            if started == {"search", "recall"}:
                both_reads_started.set()
            await asyncio.wait_for(both_reads_started.wait(), timeout=0.5)
            await asyncio.sleep(0)
        events.append(f"{name}:finish")
        return {"tool": name, "value": value}

    out = asyncio.run(
        drive_agent_loop(
            input={"task": "record with reads first"},
            cfg=_acceptance_cfg(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            granted=GRANTED,
            contracts=CONTRACTS,
        )
    )

    assert out["status"] == "done"
    assert out["rounds"] == 1
    assert [e["ref"] for e in out["trace"] if e["decision"] == "call"] == [
        "search",
        "recall",
        "record_memory",
    ]
    # round_note computed fresh from loop state on round 0 with max_rounds=12.
    assert payloads[0][ROUND_NOTE_KEY] == "[REMAINING ROUNDS: 12]"

    read_finishes = [i for i, e in enumerate(events) if e in ("search:finish", "recall:finish")]
    # both reads STARTED before either read FINISHED -> they ran concurrently
    assert events.index("search:start") < min(read_finishes)
    assert events.index("recall:start") < min(read_finishes)
    # the WRITE started only after both reads finished -> effect fence held
    assert events.index("record_memory:start") > events.index("search:finish")
    assert events.index("record_memory:start") > events.index("recall:finish")


# --------------------------------------------------------------------------- #
# 2. A raising tool becomes an error observation the controller recovers from.
# --------------------------------------------------------------------------- #
def test_acceptance_raising_tool_becomes_observation_controller_recovers() -> None:
    exc = RuntimeError("search backend down")
    payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        payloads.append(payload)
        n = len(payloads)
        if n == 1:
            return {"tool_calls": [{"id": "s1", "tool": "search", "input": {"query": "q"}}]}
        if n == 2:
            observations = payload["input"]
            # the controller SEES the raising tool as an error observation ...
            assert isinstance(observations, list)
            assert observations[0]["output"] == {"error": repr(exc), "tool": "search"}
            # ... and recovers by calling a different, working tool.
            return {"tool_calls": [{"id": "r1", "tool": "record_memory", "input": {"content": "fallback"}}]}
        return {"done": True, "output": payload["input"]}

    async def call_tool(name: str, value: Any, *, call_index: Optional[int] = None) -> Any:
        del call_index
        if name == "search":
            raise exc
        return {"ok": True, "stored": value}

    out = asyncio.run(
        drive_agent_loop(
            input={"task": "find then store"},
            cfg=_acceptance_cfg(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            granted=GRANTED,
            contracts=CONTRACTS,
        )
    )

    assert out["status"] == "done"
    call_entries = [(e["ref"], bool(e.get("error"))) for e in out["trace"] if e["decision"] == "call"]
    assert ("search", True) in call_entries  # the raising tool -> error observation, run did not abort
    assert ("record_memory", False) in call_entries  # controller recovered on the next round
    # round notes decremented every round (per-round dynamic context)
    assert payloads[0][ROUND_NOTE_KEY] == "[REMAINING ROUNDS: 12]"
    assert payloads[1][ROUND_NOTE_KEY] == "[REMAINING ROUNDS: 11]"
    assert payloads[2][ROUND_NOTE_KEY] == "[REMAINING ROUNDS: 10]"


# --------------------------------------------------------------------------- #
# 3. The transcript replays in provider tool-call grammar on the next round.
# --------------------------------------------------------------------------- #
def test_acceptance_transcript_replays_in_provider_grammar() -> None:
    rich = load_rich_dotctx(str(FIXTURE), env={})
    sample = Sample(
        name="grammar",
        input={"task": "record a memory"},
        mock_tools={"record_memory": {"ok": True}},
        stop_on=stop_after_turns(6),
    )
    fake = CapturingRecordFake()

    result = run(_run_tool_loop(rich, sample, fake))

    assert result["status"] == "done"
    assert [e["ref"] for e in result["trace"] if e["decision"] == "call"] == ["record_memory"]

    # The SECOND round's provider messages replay the prior exchange in native
    # OpenAI/Anthropic tool-call grammar: an assistant tool_calls turn followed by
    # a tool-role result keyed by the same id.
    round_two = fake.rounds[1]
    assistant_tc = [m for m in round_two if m.get("role") == "assistant" and m.get("tool_calls")]
    assert assistant_tc, "assistant tool_calls turn must replay in provider grammar"
    call = assistant_tc[0]["tool_calls"][0]
    assert call["id"] == "call_rec"
    assert call["function"]["name"] == "record_memory"
    tool_msgs = [m for m in round_two if m.get("role") == "tool"]
    assert tool_msgs, "the tool result must replay as a tool-role message"
    assert tool_msgs[0]["tool_call_id"] == "call_rec"


# --------------------------------------------------------------------------- #
# 4a. `julep eval` scores the run against the fixture suite and PASSES the threshold.
# --------------------------------------------------------------------------- #
def test_acceptance_julep_eval_threshold_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    report = run(run_eval(str(FIXTURE), acompletion=GoodRecordExecuteFake()))
    data = report.to_json()

    assert set(data) == {"ctx", "model", "samples", "scores", "mean", "threshold", "passed"}
    assert report.samples == 3
    assert {s.id for s in report.scores} == {"records_ok", "searches_ok", "recalls_ok"}
    assert report.mean == 1.0
    assert report.passed is True
    assert all(s.passed for s in report.scores)

    monkeypatch.setattr(
        "julep.cli.evalrun._resolve_acompletion",
        lambda _a: GoodRecordExecuteFake(),
    )
    assert main(["eval", str(FIXTURE)]) == 0


# --------------------------------------------------------------------------- #
# 4b. `julep eval` below-threshold gate (exit 2) and baseline-regression gate (exit 3).
# --------------------------------------------------------------------------- #
def test_acceptance_julep_eval_below_threshold_and_baseline_regression(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    good = run(run_eval(str(FIXTURE), acompletion=GoodRecordExecuteFake()))
    bad = run(run_eval(str(FIXTURE), acompletion=SilentBadFake()))

    assert bad.mean == 0.0
    assert bad.passed is False

    regressed, mean_regressed = diff_reports(good.to_json(), bad.to_json())
    assert set(regressed) == {"records_ok", "searches_ok", "recalls_ok"}
    assert mean_regressed is True

    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(good.to_json()), encoding="utf-8")

    monkeypatch.setattr(
        "julep.cli.evalrun._resolve_acompletion",
        lambda _a: SilentBadFake(),
    )
    assert main(["eval", str(FIXTURE)]) == 2
    assert main(["eval", str(FIXTURE), "--baseline", str(baseline)]) == 3
