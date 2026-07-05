import asyncio
from types import SimpleNamespace
from julep.execution.llm_result import LlmResult, LlmCallMeta
from julep.execution import llm as llm_mod
from julep.dotctx import Reasoner

def _fake_completion(content="hello", pt=11, ct=7):
    msg = SimpleNamespace(content=content, parsed=None)
    choice = SimpleNamespace(message=msg)
    usage = SimpleNamespace(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct)
    return SimpleNamespace(choices=[choice], usage=usage, model="anthropic/claude-x")

def test_complete_reasoner_returns_result_with_usage():
    async def fake_acompletion(**kwargs):
        return _fake_completion()
    reasoner = Reasoner(name="r", model="anthropic:claude-x", system="s", reply=None)
    out = asyncio.run(llm_mod.complete_reasoner(
        reasoner, {"x": 1}, acompletion=fake_acompletion,
    ))
    assert isinstance(out, LlmResult)
    assert out.reply == "hello"
    assert out.meta.input_tokens == 11
    assert out.meta.output_tokens == 7
    assert out.meta.total_tokens == 18
    assert out.meta.started_at is not None and out.meta.ended_at is not None
    assert out.meta.ended_at >= out.meta.started_at
    assert out.meta.served_model == "claude-x"

def test_to_attrs_shape():
    meta = LlmCallMeta(
        served_model="m", provider="p", input_tokens=1, output_tokens=2,
        total_tokens=3, started_at=10.0, ended_at=12.0, attempts=(), cost=None,
    )
    attrs = meta.to_attrs()
    assert attrs["llm.model"] == "m"
    assert attrs["llm.usage"] == {"input": 1, "output": 2, "total": 3}
    assert attrs["llm.started_at"] == 10.0
    assert attrs["llm.ended_at"] == 12.0
