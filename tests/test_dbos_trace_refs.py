from __future__ import annotations

import asyncio
from typing import Any

from julep.agent_loop import (
    AgentState,
    TraceEntry,
    blob_round_output_refs,
)


def test_call_many_round_blobs_each_new_call_output() -> None:
    state = AgentState(
        trace=[
            TraceEntry(decision="call", ref="old", output_ref="old"),
            TraceEntry(decision="call", ref="x", call_id="a"),
            TraceEntry(decision="call", ref="y", call_id="b"),
        ],
        last=[
            {"id": "a", "tool": "x", "output": {"r": 1}},
            {"id": "b", "tool": "y", "output": {"r": 2}},
        ],
    )
    blobbed: list[Any] = []

    async def blob(value: Any) -> str:
        blobbed.append(value)
        return f"blob-{len(blobbed) - 1}"

    asyncio.run(blob_round_output_refs(state, 1, blob))

    assert state.trace[0].output_ref == "old"
    assert state.trace[1].output_ref == "blob-0"
    assert state.trace[2].output_ref == "blob-1"
    assert blobbed == [{"r": 1}, {"r": 2}]


def test_single_call_round_blobs_state_last() -> None:
    state = AgentState(
        trace=[TraceEntry(decision="call", ref="x")],
        last={"r": 9},
    )
    blobbed: list[Any] = []

    async def blob(value: Any) -> str:
        blobbed.append(value)
        return f"blob-{len(blobbed) - 1}"

    asyncio.run(blob_round_output_refs(state, 0, blob))

    assert state.trace[0].output_ref == "blob-0"
    assert blobbed == [{"r": 9}]


def test_reask_only_round_does_not_blob() -> None:
    state = AgentState(trace=[TraceEntry(decision="reask")], last={"r": 9})
    blobbed: list[Any] = []

    async def blob(value: Any) -> str:
        blobbed.append(value)
        return f"blob-{len(blobbed) - 1}"

    asyncio.run(blob_round_output_refs(state, 0, blob))

    assert state.trace[0].output_ref is None
    assert blobbed == []
