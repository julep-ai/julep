from julep.projection import SpanData
from julep.execution.langfuse import span_attributes

def _gen_span():
    return SpanData(
        name="reasoner", cid="c0", node="reasoner", start_ts=0.0, end_ts=1.0,
        status="ok", parents=(),
        attrs={"llm.model": "claude-opus-4-8",
               "llm.usage": {"input": 1200, "output": 340, "total": 1540}},
    )

def test_generation_mapping():
    a = span_attributes(_gen_span(), session_id="s1", trace_name="run", capture_io=False)
    assert a["langfuse.observation.type"] == "generation"
    assert a["gen_ai.request.model"] == "claude-opus-4-8"
    assert a["gen_ai.usage.input_tokens"] == 1200
    assert a["gen_ai.usage.output_tokens"] == 340
    assert a["langfuse.session.id"] == "s1"
    assert a["langfuse.trace.name"] == "run"

def test_plain_span_is_not_generation():
    s = SpanData(name="pure", cid="c1", node="pure", start_ts=0.0, end_ts=1.0,
                 status="ok", parents=(), attrs={})
    a = span_attributes(s, session_id="s1", trace_name="run", capture_io=False)
    assert a.get("langfuse.observation.type") != "generation"
