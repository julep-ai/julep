"""End-to-end flows on a real DBOS runtime.

Needs ``DBOS_TEST_DATABASE_URL`` (see ``tests/test_dbos_api_spike.py`` for the
docker one-liner). Reuses one module-scoped event loop because DBOS async
methods install DBOS's executor as the loop default executor; closing a
per-test ``asyncio.run`` loop closes that executor for later tests.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections.abc import Awaitable, Callable, Iterator
from typing import Any, TypeVar

import pytest

from julep.execution import HAVE_DBOS

DB_URL = os.environ.get("DBOS_TEST_DATABASE_URL")
T = TypeVar("T")
pytestmark = pytest.mark.skipif(
    not HAVE_DBOS or not DB_URL,
    reason="dbos not installed or DBOS_TEST_DATABASE_URL not set",
)

if HAVE_DBOS and DB_URL:
    from dbos import DBOS, DBOSConfig

    from julep import arr, call, freeze, mcp, register_pure, seq
    from julep.continuation import continue_with
    from julep.derived import delay, human_gate
    from julep.dsl import par
    from julep.execution.dbos_backend import run_flow_dbos, submit_human_dbos
    from julep.execution.effects import WorkerContext, configure
    from julep.execution.policy import ExecutionPolicy
    from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec

    SNAPSHOT = McpSnapshot(
        servers={
            "kb": McpServerSnapshot(
                server="kb",
                version="1.0",
                tools={"search": McpToolSpec(input_schema={})},
            ),
        }
    )

    def _frozen(flow: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        frozen = freeze(flow, SNAPSHOT)
        return frozen.flow.to_json(), {
            h: t.to_json() for h, t in frozen.manifest.items()
        }

    _CONC = {"now": 0, "peak": 0}

    async def fake_mcp(
        server: str, tool: str, value: Any, key: str
    ) -> dict[str, Any]:
        assert key
        _CONC["now"] += 1
        _CONC["peak"] = max(_CONC["peak"], _CONC["now"])
        await asyncio.sleep(0.05)
        _CONC["now"] -= 1
        return {"echo": value, "tool": f"{server}/{tool}"}

    def _bump(value: dict[str, int]) -> Any:
        n = value["n"]
        return continue_with({"n": n + 1}) if n < 2 else {"done": n}

    register_pure("e2edbos.bump", _bump)


@pytest.fixture(scope="module")
def run_async() -> Iterator[Callable[[Awaitable[T]], T]]:
    loop = asyncio.new_event_loop()

    def run(awaitable: Awaitable[T]) -> T:
        return loop.run_until_complete(awaitable)

    yield run
    loop.close()


@pytest.fixture(scope="module")
def dbos_runtime(run_async: Callable[[Awaitable[Any]], Any]) -> Iterator[None]:
    configure(WorkerContext(mcp_call=fake_mcp))
    DBOS(
        config=DBOSConfig(
            name=f"julep-e2e-{uuid.uuid4().hex[:8]}",
            system_database_url=DB_URL,
        )
    )
    DBOS.launch()
    yield
    DBOS.destroy()


def test_seq_pipeline(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    flow_json, manifest_json = _frozen(
        seq(call(mcp("kb", "search")), call(mcp("kb", "search")))
    )
    out = run_async(
        run_flow_dbos(
            flow_json,
            manifest_json,
            session_id=f"e2e-seq-{uuid.uuid4().hex[:8]}",
            input={"q": "x"},
        )
    )
    assert out["tool"] == "kb/search"
    assert out["echo"]["tool"] == "kb/search"  # first call's output fed the second


def test_delay_is_durable_wait(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    flow_json, manifest_json = _frozen(delay(seconds=1))
    t0 = time.monotonic()
    out = run_async(
        run_flow_dbos(
            flow_json,
            manifest_json,
            session_id=f"e2e-delay-{uuid.uuid4().hex[:8]}",
            input={"v": 9},
        )
    )
    assert out == {"v": 9}
    assert time.monotonic() - t0 >= 1.0


def test_human_gate_timeout(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    flow_json, manifest_json = _frozen(human_gate(timeout_s=1))
    out = run_async(
        run_flow_dbos(
            flow_json,
            manifest_json,
            session_id=f"e2e-gate-to-{uuid.uuid4().hex[:8]}",
            input={"ask": 1},
        )
    )
    assert out == {"approved": False, "reason": "timeout", "input": {"ask": 1}}


def test_human_gate_release(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, bool]]], dict[str, bool]]
) -> None:
    gate = human_gate(timeout_s=30)
    flow_json, manifest_json = _frozen(gate)
    wfid = f"e2e-gate-{uuid.uuid4().hex[:8]}"

    async def main() -> dict[str, bool]:
        task = asyncio.create_task(
            run_flow_dbos(
                flow_json,
                manifest_json,
                session_id=wfid,
                input={"ask": 1},
            )
        )
        await asyncio.sleep(1.0)
        # DbosEnv cids are session-prefixed; the frozen root node is activation 1.
        await submit_human_dbos(wfid, f"{wfid}/{flow_json['id']}@1", {"approved": True})
        return await task

    assert run_async(main()) == {"approved": True}


def test_continuation_chain(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, int]]], dict[str, int]]
) -> None:
    flow_json, manifest_json = _frozen(arr("e2edbos.bump"))
    out = run_async(
        run_flow_dbos(
            flow_json,
            manifest_json,
            session_id=f"e2e-chain-{uuid.uuid4().hex[:8]}",
            input={"n": 0},
        )
    )
    assert out == {"done": 2}


def test_bounded_par(
    dbos_runtime: None, run_async: Callable[[Awaitable[list[Any]]], list[Any]]
) -> None:
    _CONC["peak"] = 0
    flow_json, manifest_json = _frozen(
        par(
            call(mcp("kb", "search")),
            call(mcp("kb", "search")),
            call(mcp("kb", "search")),
        )
    )
    out = run_async(
        run_flow_dbos(
            flow_json,
            manifest_json,
            session_id=f"e2e-par-{uuid.uuid4().hex[:8]}",
            input={"q": "x"},
            policy=ExecutionPolicy(max_parallel=1),
        )
    )
    assert len(out) == 3
    assert _CONC["peak"] == 1
