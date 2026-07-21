import asyncio

from julep.dotctx import Reasoner
from julep.execution import effects
from julep.execution.effects import (
    InvokeReasonerInput,
    WorkerContext,
    _unwrap_llm,
    configure,
)
from julep.execution.interpreter import _unwrap_julep_meta
from julep.execution.llm_result import LlmCallMeta, LlmResult
from julep.registry import Registry


def _configure_restoring(ctx):
    prev = effects._CTX
    configure(ctx)
    return prev


def _restore_ctx(prev):
    effects._CTX = prev


def test_unwrap_llm_result():
    meta = LlmCallMeta(served_model="m", provider="p", input_tokens=1,
                       output_tokens=2, total_tokens=3, started_at=1.0, ended_at=2.0)
    reply, attrs = _unwrap_llm(LlmResult(reply={"a": 1}, meta=meta))
    assert reply == {"a": 1}
    assert attrs["llm.model"] == "m"
    assert attrs["llm.usage"] == {"input": 1, "output": 2, "total": 3}


def test_unwrap_bare_reply_backcompat():
    reply, attrs = _unwrap_llm({"a": 1})  # a fake caller that returns a bare reply
    assert reply == {"a": 1}
    assert attrs == {}


def test_did_event_carries_llm_usage():
    registry = Registry()
    registry.register_reasoner(Reasoner(name="metered", model="test", system="s"))
    meta = LlmCallMeta(
        served_model="m",
        provider="p",
        input_tokens=1,
        output_tokens=2,
        total_tokens=3,
        started_at=1.0,
        ended_at=2.0,
    )

    async def fake_llm(reasoner, value, principal, transcript, dispatch):
        return LlmResult(reply={"answer": 42}, meta=meta)

    prev = _configure_restoring(WorkerContext(llm=fake_llm, registry=registry))
    try:
        out = asyncio.run(
            effects.invokeReasoner(
                InvokeReasonerInput(
                    reasoner="metered",
                    value={"question": "usage?"},
                    cid="think@usage",
                )
            )
        )
    finally:
        _restore_ctx(prev)

    reply, attrs = _unwrap_julep_meta(out)
    assert reply == {"answer": 42}
    assert attrs is not None
    assert attrs["llm.usage"] == {"input": 1, "output": 2, "total": 3}
    assert attrs["llm.started_at"] == 1.0
    assert attrs["llm.ended_at"] == 2.0
