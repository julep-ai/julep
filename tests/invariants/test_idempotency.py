from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("temporalio")
pytest.importorskip("httpx")

from julep import call, freeze, mcp
from julep.execution import harness
from julep.execution.activities import CallToolInput, WorkerContext, callTool, configure
from julep.execution.interpreter import interpret
from julep.projection import InMemoryProjection, ProjectionEmitter
from conftest import read_snapshot, run


@pytest.fixture(autouse=True)
def _reset_worker_context():
    configure(WorkerContext())
    yield
    configure(WorkerContext())


def test_calltool_mcp_passes_cid_as_idempotency_key() -> None:
    calls: list[tuple[str, str, Any, str]] = []

    async def mcp_call(server: str, tool: str, value: Any, key: str) -> Any:
        calls.append((server, tool, value, key))
        return {"ok": True}

    configure(WorkerContext(mcp_call=mcp_call))
    inp = CallToolInput(
        tool_ref=mcp("srv", "search").to_json(),
        value={"q": "temporal"},
        cid="activation-123",
    )

    assert run(callTool(inp)) == {"ok": True}
    assert calls == [("srv", "search", {"q": "temporal"}, inp.cid)]


def test_calltool_mcp_reuses_same_key_for_same_input_retry() -> None:
    keys: list[str] = []

    async def mcp_call(_server: str, _tool: str, _value: Any, key: str) -> Any:
        keys.append(key)
        return "ok"

    configure(WorkerContext(mcp_call=mcp_call))
    inp = CallToolInput(
        tool_ref=mcp("srv", "write").to_json(),
        value={"id": 7},
        cid="activation-retry",
    )

    assert run(callTool(inp)) == "ok"
    assert run(callTool(inp)) == "ok"
    assert keys == [inp.cid, inp.cid]


def test_temporal_tool_keys_distinguish_executions_and_continuations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    results_by_key: dict[str, str] = {}

    async def provider(_server: str, _tool: str, value: Any, key: str) -> str:
        return results_by_key.setdefault(key, value["q"])

    async def execute_activity(activity: Any, inp: CallToolInput, **_: Any) -> str:
        assert activity is callTool
        result = await callTool(inp)
        assert await callTool(inp) == result
        return result

    async def gate_waiter(_value: Any, _cid: str, _timeout_s: int | None) -> Any:
        pytest.fail("unexpected human gate")

    configure(WorkerContext(mcp_call=provider))
    monkeypatch.setattr(harness.workflow, "in_workflow", lambda: True)
    monkeypatch.setattr(harness.workflow, "patched", lambda _change: True)
    monkeypatch.setattr(harness.workflow, "execute_activity", execute_activity)
    frozen = freeze(call(mcp("srv", "search")), read_snapshot("search"))

    def execute(run_id: str, segment: int, value: str) -> Any:
        monkeypatch.setattr(harness.workflow, "info", lambda: SimpleNamespace(first_execution_run_id=run_id))
        env = harness._TemporalEnv(
            frozen.manifest,
            ProjectionEmitter(InMemoryProjection()),
            session_id="same-session",
            manifest_json=None,
            policy=harness.ExecutionPolicy(),
            gate_waiter=gate_waiter,
            segment_seq=segment,
        )
        return run(interpret(frozen.flow, {"q": value}, env)).value

    first = execute("first-execution", 0, "first")
    continued = execute("first-execution", 1, "continued")
    independent = execute("second-execution", 0, "independent")

    assert [first, continued, independent] == ["first", "continued", "independent"]
    assert len(results_by_key) == 3


@pytest.mark.parametrize("key", [None, "execution/0/activation-native"])
def test_calltool_native_sends_idempotency_header(
    monkeypatch: pytest.MonkeyPatch, key: str | None
) -> None:
    import httpx

    calls: list[dict[str, Any]] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, bool]:
            return {"ok": True}

    class FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        async def post(
            self,
            url: str,
            *,
            json: dict[str, Any],
            headers: dict[str, str],
        ) -> FakeResponse:
            calls.append({"url": url, "json": json, "headers": headers, "timeout": self.timeout})
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    configure(
        WorkerContext(
            tool_urls={"native_tool": "https://tools.example/native"},
            http_timeout_s=12.5,
        )
    )
    inp = CallToolInput(
        tool_ref={"kind": "native", "name": "native_tool"},
        value={"payload": 1},
        cid="activation-native",
        idempotency_key=key,
    )

    assert run(callTool(inp)) == {"ok": True}
    assert calls == [
        {
            "url": "https://tools.example/native",
            "json": {"input": {"payload": 1}},
            "headers": {"Idempotency-Key": key or inp.cid},
            "timeout": 12.5,
        }
    ]
