from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("temporalio")
pytest.importorskip("httpx")

from composable_agents import mcp
from composable_agents.execution.activities import CallToolInput, WorkerContext, callTool, configure
from conftest import run


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


def test_calltool_native_sends_cid_as_idempotency_header(monkeypatch: pytest.MonkeyPatch) -> None:
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
    )

    assert run(callTool(inp)) == {"ok": True}
    assert calls == [
        {
            "url": "https://tools.example/native",
            "json": {"input": {"payload": 1}},
            "headers": {"Idempotency-Key": inp.cid},
            "timeout": 12.5,
        }
    ]
