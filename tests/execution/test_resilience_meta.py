import asyncio
from types import SimpleNamespace

from composable_agents.dotctx import Reasoner
from composable_agents.execution.llm import make_resilient_llm_caller
from composable_agents.execution.llm_result import LlmResult
from composable_agents.resilience import ResiliencePolicy


def _completion(pt=5, ct=3):
    msg = SimpleNamespace(content="ok", parsed=None)
    usage = SimpleNamespace(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=msg)], usage=usage, model="anthropic/m2"
    )


def test_caller_returns_result_and_records_fallback_attempts():
    calls = {"n": 0}

    async def flaky(**kwargs):
        calls["n"] += 1
        if kwargs["model"] == "m1":
            raise TimeoutError("provider down")
        return _completion()

    policy = ResiliencePolicy(fallbacks={"anthropic:m1": ["anthropic:m2"]})
    caller = make_resilient_llm_caller(policy=policy, acompletion=flaky)
    reasoner = Reasoner(
        name="r", model="anthropic:m1", system="s", reply_schema=None
    )

    out = asyncio.run(caller(reasoner, {"x": 1}))

    assert isinstance(out, LlmResult)
    assert out.reply == "ok"
    assert out.meta.served_model == "m2"
    assert out.meta.input_tokens == 5
    outcomes = [a.outcome for a in out.meta.attempts]
    assert outcomes[-1] == "ok"
    assert any(o != "ok" for o in outcomes)
