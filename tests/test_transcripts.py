"""Framework-owned transcripts for app agent loops (docs/design/agent-transcripts.md).

The transcript is derived, not stored: transcript_for projects a deterministic,
ref-bearing plan in workflow code; the invoke_reasoner effect hydrates blob refs,
enforces the hard token budget, runs the named summarizer for SUMMARY scope,
and tools the materialized turns to the LlmCaller as its fourth argument.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from julep import app, deploy
from julep.agent_loop import (
    AgentConfig,
    AgentState,
    FEEDBACK_KEY,
    TraceEntry,
    drive_agent_loop,
    state_fingerprint,
)
from julep.dotctx import Reasoner, reasoner_to_flow
from julep.registry import DEFAULT_REGISTRY
from julep.errors import ValidationError
from julep.execution import HAVE_DBOS, HAVE_TEMPORAL
from julep.execution.blobstore import InMemoryBlobStore, LocalDirBlobStore
from julep.execution.effects import (
    InvokeReasonerInput,
    WorkerContext,
    configure,
    invokeReasoner,
)
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.freeze import McpSnapshot
from julep.ir import ContextPolicy, Node
from julep.kinds import ContextScope, EnforcementMode
from julep.projection import InMemoryProjection, ProjectionEmitter
from julep.transcript import (
    SUMMARY_KEY,
    Turn,
    approx_token_count,
    bounded_transcript,
    elision_marker,
    split_summary_reply,
    split_to_budget,
    summary_turn,
    transcript_for,
    turn_text,
)
from julep.turn import controller_turn
from julep.validate import blocking, validate

WHOLE = ContextPolicy(scope=ContextScope.WHOLE_SESSION, max_tokens=1000)
SUMMARY = ContextPolicy(scope=ContextScope.SUMMARY, max_tokens=1000)


def _state() -> AgentState:
    return AgentState(
        last={"q": "x"},
        trace=[
            TraceEntry(decision="call", ref="kb/search", cost=1.0, output_ref="t/sha256:" + "a" * 64),
            TraceEntry(decision="sub", ref="child", cost=5.0),
            TraceEntry(decision="call", ref="index", cost=1.0),
        ],
    )


# --------------------------------------------------------------------------- #
# transcript_for: deterministic, ref-bearing plan.
# --------------------------------------------------------------------------- #
def test_local_scope_has_no_transcript() -> None:
    assert transcript_for(_state(), ContextPolicy(), input=1) == []
    assert transcript_for(_state(), ContextPolicy(scope=ContextScope.NONE), input=1) == []


def test_whole_session_plan_emits_input_then_action_result_pairs() -> None:
    plan = transcript_for(_state(), WHOLE, input={"task": "go"})
    assert plan[0] == {"role": "user", "content": {"task": "go"}}
    mcp_ref = {"kind": "mcp", "server": "kb", "tool": "search"}
    assert plan[1] == {"role": "assistant", "ref": mcp_ref}
    # The plan carries refs, never content: hydration is the effect's job.
    assert plan[2] == {"role": "tool", "ref": mcp_ref, "content_ref": "t/sha256:" + "a" * 64}
    assert plan[3] == {"role": "assistant", "ref": {"kind": "sub", "ref": "child"}}
    assert plan[4] == {"role": "tool", "ref": {"kind": "sub", "ref": "child"}}
    assert plan[5] == {"role": "assistant", "ref": {"kind": "native", "name": "index"}}
    assert plan[6] == {"role": "tool", "ref": {"kind": "native", "name": "index"}}
    assert len(plan) == 7


def test_whole_session_plan_uses_ephemeral_output_until_blob_ref_exists() -> None:
    entry = TraceEntry(
        decision="call",
        ref="lookup",
        output={"answer": 42},
        output_available=True,
    )
    state = AgentState(trace=[entry])

    assert transcript_for(state, WHOLE, input="question")[-1]["content"] == {
        "answer": 42
    }
    assert "output" not in entry.to_json()
    assert not AgentState.from_json(state.to_json()).trace[0].output_available


def test_transcript_for_is_deterministic() -> None:
    a = transcript_for(_state(), WHOLE, input=5)
    b = transcript_for(_state(), WHOLE, input=5)
    assert a == b
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_terminal_trace_entries_are_skipped() -> None:
    state = AgentState(trace=[TraceEntry(decision="finish", cost=0.0)])
    assert transcript_for(state, WHOLE, input="i") == [{"role": "user", "content": "i"}]


# --------------------------------------------------------------------------- #
# Budget: hard bound, oldest dropped, explicit elision marker.
# --------------------------------------------------------------------------- #
def _turns(n: int) -> list[Turn]:
    return [{"role": "user", "content": f"turn-{i}"} for i in range(n)]


def test_split_to_budget_keeps_newest() -> None:
    turns = _turns(4)
    per_turn = approx_token_count(turn_text(turns[0]))
    elided, kept = split_to_budget(turns, per_turn * 2, approx_token_count)
    assert kept == turns[2:]
    assert elided == turns[:2]


def test_split_to_budget_no_overflow_keeps_everything() -> None:
    turns = _turns(3)
    elided, kept = split_to_budget(turns, 10_000, approx_token_count)
    assert (elided, kept) == ([], turns)


def test_budget_is_hard_even_for_the_newest_turn() -> None:
    turns = _turns(2)
    elided, kept = split_to_budget(turns, 1, lambda text: 50)
    assert kept == [] and elided == turns
    assert bounded_transcript(turns, 1, lambda text: 50) == [elision_marker(2)]


def test_elision_marker_is_the_documented_system_turn() -> None:
    assert elision_marker(3) == {"role": "system", "content": "3 earlier turns elided"}


def test_bounded_transcript_prefixes_marker_on_overflow() -> None:
    turns = _turns(4)
    per_turn = approx_token_count(turn_text(turns[0]))
    out = bounded_transcript(turns, per_turn * 2, approx_token_count)
    assert out == [elision_marker(2), *turns[2:]]


def test_split_summary_reply_unwraps_envelope_only() -> None:
    assert split_summary_reply({SUMMARY_KEY: "s", "reply": {"ok": 1}}) == ("s", {"ok": 1})
    assert split_summary_reply({"output": "done"}) == (None, {"output": "done"})
    assert split_summary_reply("prose") == (None, "prose")


# --------------------------------------------------------------------------- #
# AgentState.summary: the single state addition; fingerprinted, conditional key.
# --------------------------------------------------------------------------- #
def test_state_summary_round_trips_and_key_is_conditional() -> None:
    state = AgentState(last=1)
    assert "summary" not in state.to_json()  # pre-transcript states hash identically
    state.summary = "running summary"
    encoded = state.to_json()
    assert encoded["summary"] == "running summary"
    assert AgentState.from_json(encoded).summary == "running summary"
    assert AgentState.from_json({"round": 0}).summary is None


def test_state_fingerprint_covers_summary() -> None:
    a, b = AgentState(last=1), AgentState(last=1)
    assert state_fingerprint(a) == state_fingerprint(b)
    b.summary = "s"
    assert state_fingerprint(a) != state_fingerprint(b)


# --------------------------------------------------------------------------- #
# app(ctx=...) carriage: conditional keys, stable hashes, codec round-trip.
# --------------------------------------------------------------------------- #
def test_bare_app_wire_format_is_unchanged() -> None:
    flow = app("c")
    assert flow.to_json() == {"op": "app", "id": flow.id, "controller": "c"}


def test_app_ctx_and_summarizer_round_trip() -> None:
    flow = app("c", ctx=SUMMARY, summarizer="sum.reasoner", max_rounds=3)
    encoded = flow.to_json()
    assert encoded["ctx"] == {"scope": "summary", "maxTokens": 1000}
    assert encoded["summarizer"] == "sum.reasoner"
    back = Node.from_json(encoded)
    assert back.ctx == SUMMARY
    assert back.summarizer == "sum.reasoner"
    assert back.to_json() == encoded


def test_app_ctx_accepts_bare_scope() -> None:
    flow = app("c", ctx=ContextScope.WHOLE_SESSION)
    assert flow.to_json()["ctx"] == {"scope": "whole_session"}


def test_freeze_preserves_app_ctx() -> None:
    deployment = deploy(app("c", ctx=WHOLE), McpSnapshot(), strict=False)
    frozen = deployment.flow_json
    assert frozen["ctx"] == {"scope": "whole_session", "maxTokens": 1000}


def test_app_ctx_reaches_run_agent_app_config() -> None:
    seen: dict[str, Any] = {}

    class CapturingEnv(InMemoryEnv):
        async def run_agent(self, controller, value, cid, app_config=None):  # noqa: ANN001
            seen["app_config"] = app_config
            return "ok"

    env = CapturingEnv({}, ProjectionEmitter(InMemoryProjection()))
    flow = app("ctrl", ctx=SUMMARY, summarizer="sum.reasoner")
    asyncio.run(interpret(flow, 1, env))
    assert seen["app_config"] == {
        "ctx": {"scope": "summary", "maxTokens": 1000},
        "summarizer": "sum.reasoner",
    }


def test_dotctx_agent_reasoner_derives_ctx_from_context_scope() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(
        name="tr.agent.whole", model="m", is_agent=True,
        context_scope=ContextScope.WHOLE_SESSION,
    ))
    node = reasoner_to_flow(DEFAULT_REGISTRY.register_reasoner(Reasoner(
        name="tr.agent.local", model="m", is_agent=True,
    )))
    assert "ctx" not in node.to_json()  # LOCAL agents: hash-stable, no ctx key
    node = reasoner_to_flow(Reasoner(
        name="tr.agent.whole", model="m", is_agent=True,
        context_scope=ContextScope.WHOLE_SESSION,
    ))
    assert node.to_json()["ctx"] == {"scope": "whole_session"}


# --------------------------------------------------------------------------- #
# Deploy-time blocking diagnostics: no implicit budget, no implicit summarizer.
# --------------------------------------------------------------------------- #
def _codes(flow: Node) -> set[str]:
    return {d.code for d in blocking(validate(flow))}


def test_whole_session_without_budget_is_blocking() -> None:
    flow = app("c", ctx=ContextScope.WHOLE_SESSION)
    assert "APP_CTX_NO_BUDGET" in _codes(flow)
    with pytest.raises(ValidationError):
        deploy(flow, McpSnapshot())


def test_summary_without_summarizer_is_blocking() -> None:
    assert "APP_SUMMARY_NO_SUMMARIZER" in _codes(app("c", ctx=SUMMARY))
    # Missing both: both diagnostics, not just the first.
    both = _codes(app("c", ctx=ContextScope.SUMMARY))
    assert {"APP_CTX_NO_BUDGET", "APP_SUMMARY_NO_SUMMARIZER"} <= both


def test_well_declared_transcript_scopes_deploy_clean() -> None:
    assert _codes(app("c", ctx=WHOLE)) == set()
    assert _codes(app("c", ctx=SUMMARY, summarizer="sum.reasoner")) == set()
    assert _codes(app("c")) == set()
    assert _codes(app("c", ctx=ContextPolicy())) == set()  # LOCAL needs nothing


# --------------------------------------------------------------------------- #
# Arity shim: 4-arg canonical; wrapped 2-/3-arg callers fail fast on transcripts.
# --------------------------------------------------------------------------- #
def _invoke(reasoner: str = "tr.reasoner", value: Any = 1, **kwargs: Any) -> Any:
    return asyncio.run(
        invokeReasoner(
            InvokeReasonerInput(reasoner=reasoner, value=value, cid="c", **kwargs)
        )
    )


def test_legacy_two_arg_caller_still_works_without_transcript() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.reasoner", model="m", system="s"))
    seen: dict[str, Any] = {}

    async def legacy(reasoner, value):
        seen["value"] = value
        return {"out": 1}

    configure(WorkerContext(llm=legacy))
    assert _invoke() == {"out": 1} and seen["value"] == 1


def test_three_arg_caller_still_receives_principal() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.reasoner", model="m", system="s"))
    seen: dict[str, Any] = {}

    async def principal_aware(reasoner, value, principal):
        seen["principal"] = principal
        return {"out": 2}

    configure(WorkerContext(llm=principal_aware))
    assert _invoke(principal={"storeId": 4}) == {"out": 2}
    assert seen["principal"] == {"storeId": 4}


@pytest.mark.parametrize("arity", [2, 3])
def test_narrow_callers_reject_transcripts_loudly(arity: int) -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.reasoner", model="m", system="s"))

    async def two(reasoner, value):
        return "ok"

    async def three(reasoner, value, principal):
        return "ok"

    configure(WorkerContext(llm=two if arity == 2 else three))
    with pytest.raises(RuntimeError, match="does not accept a transcript"):
        _invoke(
            transcript=[{"role": "user", "content": "hi"}],
            ctx={"scope": "whole_session", "maxTokens": 100},
        )


def test_four_arg_caller_is_used_unwrapped() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.reasoner", model="m", system="s"))
    seen: dict[str, Any] = {}

    async def canonical(reasoner, value, principal, transcript):
        seen["transcript"] = transcript
        return "ok"

    configure(WorkerContext(llm=canonical))
    assert _invoke() == "ok" and seen["transcript"] is None


# --------------------------------------------------------------------------- #
# invokeReasoner: hydration, budget enforcement, summarizer, summary envelope.
# --------------------------------------------------------------------------- #
def _blob(store: InMemoryBlobStore, tenant: str, value: Any) -> str:
    # Same canonical-JSON encoding as the putBlob activity.
    return asyncio.run(store.put(tenant, json.dumps(value, sort_keys=True).encode()))


def _capture_ctx(**kwargs: Any) -> tuple[WorkerContext, dict[str, Any]]:
    seen: dict[str, Any] = {}

    async def llm(reasoner, value, principal, transcript):
        seen.setdefault("calls", []).append(
            {"reasoner": reasoner.name, "value": value, "transcript": transcript}
        )
        return seen.get("replies", {}).get(reasoner.name, {"output": "done"})

    return WorkerContext(llm=llm, **kwargs), seen


def test_whole_session_transcript_is_hydrated_from_the_blob_store() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.ctrl", model="m", system="s"))
    store = InMemoryBlobStore()
    ref = _blob(store, "sess", {"hits": 3})
    ctx, seen = _capture_ctx(blob_store=store)
    configure(ctx)

    out = _invoke(
        reasoner="tr.ctrl",
        transcript=[
            {"role": "user", "content": "go"},
            {"role": "tool", "ref": {"kind": "native", "name": "t"}, "content_ref": ref},
        ],
        ctx={"scope": "whole_session", "maxTokens": 10_000},
    )
    assert out == {"output": "done"}
    (call,) = seen["calls"]
    assert call["transcript"] == [
        {"role": "user", "content": "go"},
        {"role": "tool", "ref": {"kind": "native", "name": "t"}, "content": {"hits": 3}},
    ]


def test_whole_session_transcript_hydrates_after_file_store_restart(
    tmp_path: Path,
) -> None:
    DEFAULT_REGISTRY.register_reasoner(
        Reasoner(name="tr.file.ctrl", model="m", system="s")
    )
    root = tmp_path / "blobs"
    writer = LocalDirBlobStore(root)
    ref = asyncio.run(
        writer.put("sess", json.dumps({"hits": 3}, sort_keys=True).encode())
    )

    reader = LocalDirBlobStore(root)
    ctx, seen = _capture_ctx(blob_store=reader)
    configure(ctx)
    _invoke(
        reasoner="tr.file.ctrl",
        transcript=[{"role": "tool", "content_ref": ref}],
        ctx={"scope": "whole_session", "maxTokens": 10_000},
    )

    (call,) = seen["calls"]
    assert call["transcript"] == [{"role": "tool", "content": {"hits": 3}}]


def test_transcript_renders_string_opening_ask_from_original_input_before_budget() -> None:
    renderer_name = "tests.transcript.string-opening"
    reasoner_name = "tr.string-opening"
    rendered_contexts: list[dict[str, Any]] = []
    counted: list[str] = []

    def render_user(context: Any) -> str:
        rendered_contexts.append(dict(context))
        assert "trace" not in context
        return f"Question: {context['value']}"

    previous = DEFAULT_REGISTRY.renderers.pop(renderer_name, None)
    DEFAULT_REGISTRY.register_renderer(renderer_name, render_user)
    DEFAULT_REGISTRY.register_reasoner(
        Reasoner(
            name=reasoner_name,
            model="m",
            system="s",
            user_render=renderer_name,
        )
    )
    ctx, seen = _capture_ctx(
        count_tokens=lambda text: counted.append(text) or 1,
    )
    configure(ctx)
    trace = [{"decision": "call", "ref": "search"}]
    try:
        _invoke(
            reasoner=reasoner_name,
            value={"input": "why?", "trace": trace},
            transcript=[{"role": "user", "content": "why?"}],
            ctx={"scope": "whole_session", "maxTokens": 10},
        )
    finally:
        DEFAULT_REGISTRY.renderers.pop(renderer_name, None)
        if previous is not None:
            DEFAULT_REGISTRY.renderers[renderer_name] = previous

    assert rendered_contexts == [{"value": "why?"}]
    (call,) = seen["calls"]
    assert call["transcript"] == [{"role": "user", "content": "Question: why?"}]
    assert any("Question: why?" in text for text in counted)


def test_feedback_looking_business_field_is_not_stripped_from_renderer_context() -> None:
    from julep.agent_loop import ROUND_NOTE_KEY
    from julep.execution.effects import _strip_reserved_controller_keys

    business = {FEEDBACK_KEY: "ordinary business value", "category": "billing"}
    assert _strip_reserved_controller_keys(business) == business
    assert _strip_reserved_controller_keys(
        {
            "input": {"category": "billing"},
            "trace": [],
            FEEDBACK_KEY: "retry",
            ROUND_NOTE_KEY: "round note",
        }
    ) == {"input": {"category": "billing"}, "trace": []}


def test_loop_feedback_is_inserted_before_transcript_budgeting() -> None:
    counted: list[str] = []
    ctx, seen = _capture_ctx(
        count_tokens=lambda text: counted.append(text) or 1,
    )
    configure(ctx)
    feedback = {"error": "final output failed validation"}

    _invoke(
        value={
            "input": {"task": "answer"},
            "trace": [{"decision": "output_reask"}],
            FEEDBACK_KEY: feedback,
        },
        transcript=[{"role": "user", "content": {"task": "answer"}}],
        ctx={"scope": "whole_session", "maxTokens": 2},
    )

    (call,) = seen["calls"]
    assert call["transcript"][-1] == {"role": "user", "content": feedback}
    assert any("final output failed validation" in text for text in counted)


def test_whole_session_budget_uses_worker_tokenizer_and_marks_elision() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.ctrl", model="m", system="s"))
    ctx, seen = _capture_ctx(count_tokens=lambda text: 1)  # one token per turn
    configure(ctx)

    _invoke(
        reasoner="tr.ctrl",
        transcript=[{"role": "user", "content": f"t{i}"} for i in range(5)],
        ctx={"scope": "whole_session", "maxTokens": 2},
    )
    (call,) = seen["calls"]
    assert call["transcript"] == [
        elision_marker(3),
        {"role": "user", "content": "t3"},
        {"role": "user", "content": "t4"},
    ]


def test_transcript_without_budget_fails_fast() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.ctrl", model="m", system="s"))
    ctx, _ = _capture_ctx()
    configure(ctx)
    with pytest.raises(RuntimeError, match="no implicit default"):
        _invoke(
            reasoner="tr.ctrl",
            transcript=[{"role": "user", "content": "x"}],
            ctx={"scope": "whole_session"},
        )


def test_transcript_ref_without_blob_store_fails_fast() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.ctrl", model="m", system="s"))
    ctx, _ = _capture_ctx()
    configure(ctx)
    with pytest.raises(RuntimeError, match="blob store"):
        _invoke(
            reasoner="tr.ctrl",
            transcript=[{"role": "tool", "content_ref": "t/sha256:" + "b" * 64}],
            ctx={"scope": "whole_session", "maxTokens": 100},
        )


def test_summary_scope_without_summarizer_fails_fast() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.ctrl", model="m", system="s"))
    ctx, _ = _capture_ctx()
    configure(ctx)
    with pytest.raises(RuntimeError, match="summarizer"):
        _invoke(
            reasoner="tr.ctrl",
            transcript=[{"role": "user", "content": "x"}],
            ctx={"scope": "summary", "maxTokens": 100},
        )


def test_summary_scope_runs_summarizer_and_returns_envelope() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.ctrl", model="m", system="s"))
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.sum", model="m", system="summarize"))
    ctx, seen = _capture_ctx(count_tokens=lambda text: 1)
    seen["replies"] = {"tr.sum": "folded summary", "tr.ctrl": {"output": "done"}}
    configure(ctx)

    out = _invoke(
        reasoner="tr.ctrl",
        transcript=[{"role": "user", "content": f"t{i}"} for i in range(4)],
        ctx={"scope": "summary", "maxTokens": 2},
        summarizer="tr.sum",
        summary="prior",
    )
    # Envelope: the workflow persists the new running summary in AgentState.
    assert out == {SUMMARY_KEY: "folded summary", "reply": {"output": "done"}}
    summarizer_call, controller_call = seen["calls"]
    assert summarizer_call["reasoner"] == "tr.sum"
    assert summarizer_call["value"] == {
        "summary": "prior",
        "turns": [{"role": "user", "content": "t0"}, {"role": "user", "content": "t1"}],
    }
    assert controller_call["transcript"] == [
        summary_turn("folded summary"),
        {"role": "user", "content": "t2"},
        {"role": "user", "content": "t3"},
    ]


def test_summary_scope_without_elision_reuses_prior_summary_no_envelope() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.ctrl", model="m", system="s"))
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.sum", model="m", system="summarize"))
    ctx, seen = _capture_ctx()
    configure(ctx)

    out = _invoke(
        reasoner="tr.ctrl",
        transcript=[{"role": "user", "content": "x"}],
        ctx={"scope": "summary", "maxTokens": 10_000},
        summarizer="tr.sum",
        summary="prior",
    )
    assert out == {"output": "done"}  # nothing newly summarized -> no envelope
    (controller_call,) = seen["calls"]  # the summarizer never ran
    assert controller_call["transcript"][0] == summary_turn("prior")


def test_summarizer_must_reply_with_text() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.ctrl", model="m", system="s"))
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="tr.sum", model="m", system="summarize"))
    ctx, seen = _capture_ctx(count_tokens=lambda text: 1)
    seen["replies"] = {"tr.sum": ["not", "text"]}
    configure(ctx)
    with pytest.raises(RuntimeError, match="must reply with text"):
        _invoke(
            reasoner="tr.ctrl",
            transcript=[{"role": "user", "content": f"t{i}"} for i in range(4)],
            ctx={"scope": "summary", "maxTokens": 1},
            summarizer="tr.sum",
        )


# --------------------------------------------------------------------------- #
# controller_turn (the shared workflow-side seam, used by DBOS + local loops).
# --------------------------------------------------------------------------- #
def _turn_step(cfg: AgentConfig, replies: list[Any], payloads: list[dict[str, Any]]):
    async def invoke_controller(payload: dict[str, Any]) -> Any:
        payloads.append(payload)
        return replies.pop(0)

    async def call_tool(tool: str, value: Any) -> Any:
        return {"tool": tool, "out": value}

    return controller_turn(
        cfg=cfg, invoke_controller=invoke_controller, call_tool=call_tool,
        run_subflow=None, granted=None, granted_subflows=None, contracts=None,
        mode=EnforcementMode.STRICT, prod_gap=[], run_input={"task": "go"},
    )


def test_controller_turn_local_payload_is_unchanged() -> None:
    payloads: list[dict[str, Any]] = []
    step = _turn_step(AgentConfig(), [{"output": "done"}], payloads)
    asyncio.run(step(AgentState(last=1)))
    assert payloads == [{"input": 1, "trace": []}]


def test_controller_turn_attaches_plan_and_persists_summary() -> None:
    payloads: list[dict[str, Any]] = []
    cfg = AgentConfig(ctx=SUMMARY, summarizer="sum.reasoner")
    step = _turn_step(
        cfg,
        [{SUMMARY_KEY: "s1", "reply": {"tool": "t", "input": 2}}],
        payloads,
    )
    state = AgentState(last=1)
    out = asyncio.run(step(state))
    (payload,) = payloads
    assert payload["transcript"] == [{"role": "user", "content": {"task": "go"}}]
    assert payload["ctx"] == {"scope": "summary", "maxTokens": 1000}
    assert payload["summarizer"] == "sum.reasoner"
    assert "summary" not in payload  # no running summary yet
    # The envelope's summary lands on state; the inner reply drives the round.
    assert out is state and state.summary == "s1"
    assert state.last == {"tool": "t", "out": 2}


def test_drive_agent_loop_threads_transcript_for_summary_scope() -> None:
    payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        payloads.append(payload)
        return {"output": "done"}

    async def call_tool(tool: str, value: Any) -> Any:
        return value

    out = asyncio.run(drive_agent_loop(
        input={"task": "go"},
        cfg=AgentConfig(ctx=WHOLE),
        invoke_controller=invoke_controller,
        call_tool=call_tool,
    ))
    assert out["status"] == "done"
    assert payloads[0]["transcript"] == [{"role": "user", "content": {"task": "go"}}]


def test_transcript_tool_input_reask_keeps_original_render_context_and_full_trace() -> None:
    payloads: list[dict[str, Any]] = []
    replies = iter(
        [
            {"tool": "search", "input": {"query": 7}},
            {"done": True, "output": {"answer": "fixed"}},
        ]
    )

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        payloads.append(payload)
        return next(replies)

    async def call_tool(_tool: str, _value: Any) -> Any:
        raise AssertionError("invalid tool input must not dispatch")

    original = {"category": "billing"}
    out = asyncio.run(
        drive_agent_loop(
            input=original,
            cfg=AgentConfig(ctx=WHOLE, native_tools=True, max_rounds=3),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            tool_schemas={
                "search": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                }
            },
        )
    )

    assert out["status"] == "done"
    assert payloads[1]["input"] == original
    assert payloads[1]["trace"][0]["decision"] == "tool_input_reask"
    assert payloads[1][FEEDBACK_KEY]["error"] == "tool_input_validation_failed"
    assert payloads[1]["transcript"] == [{"role": "user", "content": original}]


# --------------------------------------------------------------------------- #
# Temporal harness: plan in workflow code, summary across continue-as-new.
# --------------------------------------------------------------------------- #
if HAVE_TEMPORAL:
    from julep.execution import harness
    from julep.execution.harness import AgentInput, AgentWorkflow


class _Stop(Exception):
    """Raised by the fake continue_as_new to capture the next segment's input."""


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_agent_workflow_threads_transcript_plan_into_invoke_reasoner(monkeypatch) -> None:
    payloads: list[Any] = []

    async def fake_execute_activity(fn, payload, **kwargs):
        payloads.append(payload)
        return {"output": "done"}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    inp = AgentInput(
        controller="ctrl", session_id="sess", input={"task": "go"},
        config={
            "maxRounds": 3, "budget": {"cost": 100},
            "ctx": {"scope": "whole_session", "maxTokens": 500},
        },
        resolve_spec=False,
    )
    out = asyncio.run(AgentWorkflow().run(inp))
    assert out["status"] == "done"
    reasoner_payloads = [p for p in payloads if isinstance(p, harness.InvokeReasonerInput)]
    assert len(reasoner_payloads) == 1
    reasoner_payload = reasoner_payloads[0]
    assert reasoner_payload.transcript == [{"role": "user", "content": {"task": "go"}}]
    assert reasoner_payload.ctx == {"scope": "whole_session", "maxTokens": 500}
    assert reasoner_payload.summary is None


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_agent_workflow_local_scope_sends_no_transcript(monkeypatch) -> None:
    payloads: list[Any] = []

    async def fake_execute_activity(fn, payload, **kwargs):
        payloads.append(payload)
        return {"output": "done"}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    inp = AgentInput(
        controller="ctrl", session_id="sess", input=5,
        config={"maxRounds": 3, "budget": {"cost": 100}},
        resolve_spec=False,
    )
    asyncio.run(AgentWorkflow().run(inp))
    reasoner_payloads = [p for p in payloads if isinstance(p, harness.InvokeReasonerInput)]
    assert len(reasoner_payloads) == 1
    reasoner_payload = reasoner_payloads[0]
    assert reasoner_payload.transcript is None and reasoner_payload.ctx is None


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_summary_survives_temporal_continue_as_new(monkeypatch) -> None:
    captured: list[Any] = []
    payloads: list[Any] = []

    async def fake_execute_activity(fn, payload, **kwargs):
        if fn.__name__ not in {"startTrajectory", "finishTrajectory"}:
            payloads.append(payload)
        if fn.__name__ == "invokeReasoner":
            # The activity ran the summarizer: envelope with the new summary.
            return {SUMMARY_KEY: "carried summary", "reply": {"tool": "t", "input": 1}}
        return {"tool": "out"}

    def fake_continue_as_new(next_input):
        captured.append(next_input)
        raise _Stop()

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    monkeypatch.setattr(harness.workflow, "continue_as_new", fake_continue_as_new)

    inp = AgentInput(
        controller="ctrl", session_id="sess", input=5,
        config={
            "maxRounds": 5, "budget": {"cost": 1000}, "continueAsNewAfter": 1,
            "ctx": {"scope": "summary", "maxTokens": 100}, "summarizer": "sum.reasoner",
        },
        resolve_spec=False,
    )
    with pytest.raises(_Stop):
        asyncio.run(AgentWorkflow().run(inp))

    (next_input,) = captured
    assert next_input.state["summary"] == "carried summary"
    # The carried config keeps the transcript policy for the next segment.
    assert next_input.config["ctx"] == {"scope": "summary", "maxTokens": 100}
    assert next_input.config["summarizer"] == "sum.reasoner"
    reasoner_payload = payloads[0]
    assert reasoner_payload.summarizer == "sum.reasoner"
    assert reasoner_payload.summary is None  # first round: nothing carried yet


# --------------------------------------------------------------------------- #
# DBOS backend: step payload split + summary in the continuation envelope.
# --------------------------------------------------------------------------- #
if HAVE_DBOS:
    from julep.continuation import CONTINUATION_KEY
    from julep.execution import dbos_backend


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_agent_segment_carries_summary_in_envelope(monkeypatch) -> None:
    payloads: list[dict] = []

    async def fake_reasoner(inp: dict) -> Any:
        payloads.append(inp)
        return {SUMMARY_KEY: "dbos summary", "reply": {"tool": "t", "input": 1}}

    async def fake_tool(inp: dict) -> Any:
        return {"tool": "out"}

    async def fake_blob(inp: dict) -> str:
        return f"{inp['tenant']}/sha256:" + "a" * 64

    monkeypatch.setattr(dbos_backend, "invokeReasonerStep", fake_reasoner)
    monkeypatch.setattr(dbos_backend, "callToolIdempotent", fake_tool)
    monkeypatch.setattr(dbos_backend, "callToolNoRetry", fake_tool)
    monkeypatch.setattr(dbos_backend, "putBlobStep", fake_blob)

    agent_body = inspect.unwrap(dbos_backend.agent_workflow)
    out = asyncio.run(agent_body({
        "controller": "ctrl",
        "sessionId": "sess",
        "input": {"task": "go"},
        "config": {
            "maxRounds": 5, "budget": {"cost": 1000}, "continueAsNewAfter": 1,
            "ctx": {"scope": "summary", "maxTokens": 100}, "summarizer": "sum.reasoner",
        },
        "resolveSpec": False,
    }))

    assert CONTINUATION_KEY in out
    assert out[CONTINUATION_KEY]["state"]["summary"] == "dbos summary"
    assert out[CONTINUATION_KEY]["config"]["summarizer"] == "sum.reasoner"

    (step_payload,) = payloads
    # The transcript rides beside the controller value, never inside it.
    assert step_payload["value"] == {"input": {"task": "go"}, "trace": []}
    assert step_payload["transcript"] == [{"role": "user", "content": {"task": "go"}}]
    assert step_payload["ctx"] == {"scope": "summary", "maxTokens": 100}
    assert step_payload["summarizer"] == "sum.reasoner"


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_transcript_round_keeps_original_input_and_full_trace(monkeypatch) -> None:
    payloads: list[dict[str, Any]] = []
    replies = iter(
        [
            {"tool": "search", "input": {"query": 7}},
            {"done": True, "output": "fixed"},
        ]
    )

    async def fake_reasoner(inp: dict[str, Any]) -> Any:
        payloads.append(inp)
        return next(replies)

    monkeypatch.setattr(dbos_backend, "invokeReasonerStep", fake_reasoner)
    agent_body = inspect.unwrap(dbos_backend.agent_workflow)
    original = {"category": "billing"}
    out = asyncio.run(
        agent_body(
            {
                "controller": "ctrl",
                "sessionId": "sess-dbos-feedback",
                "input": original,
                "config": {
                    "maxRounds": 3,
                    "nativeTools": True,
                    "ctx": {"scope": "whole_session", "maxTokens": 500},
                },
                "grantedTools": ["search"],
                "toolDefs": [
                    {
                        "type": "function",
                        "function": {
                            "name": "search",
                            "parameters": {
                                "type": "object",
                                "properties": {"query": {"type": "string"}},
                                "required": ["query"],
                            },
                        },
                    }
                ],
                "resolveSpec": False,
            }
        )
    )

    assert out["status"] == "done"
    assert payloads[1]["value"]["input"] == original
    assert payloads[1]["value"]["trace"][0]["decision"] == "tool_input_reask"
    assert payloads[1]["value"][FEEDBACK_KEY]["error"] == "tool_input_validation_failed"
