import asyncio
from composable_agents.execution.langfuse import export_temporal_run
from composable_agents.projection import ProjectionEvent, EventType
from tests.execution.test_langfuse_export import _Tracer

class _FakeHandleObj:
    def __init__(self, events_json): self._e = events_json
    async def query(self, name): return self._e

class _FakeClient:
    def __init__(self, events_json): self._e = events_json
    def get_workflow_handle(self, wid): return _FakeHandleObj(self._e)

class _ExpHandle:
    def __init__(self): self.tracer = _Tracer(); self.flushed = False
    def flush(self): self.flushed = True

def test_export_temporal_run_queries_and_exports():
    events_json = [
        ProjectionEvent("e0", EventType.PLANNED, "reasoner", "c0", 0.0).to_json(),
        ProjectionEvent("e1", EventType.DID, "reasoner", "c0", 1.0, causes=("e0",),
                        attrs={"llm.model": "m", "llm.usage": {"input": 1, "output": 1, "total": 2}}).to_json(),
    ]
    handle = _ExpHandle()
    n = asyncio.run(export_temporal_run(handle, client=_FakeClient(events_json),
                                        workflow_id="wf-1"))
    assert n >= 1 and handle.flushed
