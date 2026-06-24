"""Session IR foundation tests."""

from __future__ import annotations

import pytest

from composable_agents import call, emit, human_gate, recv
from composable_agents.derived import HUMAN_CHANNEL
from composable_agents.errors import ComposableAgentsError
from composable_agents.ir import (
    EMIT_TOOL,
    HUMAN_GATE_TOOL,
    RECV_TOOL,
    CallStep,
    ChannelRef,
    NativeTool,
    Node,
    canonical_json,
    channelref_key,
)
from composable_agents.kinds import Op, Shape
from composable_agents.session import Channel, drive_session, scan
from composable_agents.shapes import closed_shape, surface_shape
from composable_agents.transforms import normalize_ids


def test_loop_ir_round_trips_and_non_loop_json_is_unchanged() -> None:
    body = call("turn")
    state_schema = {"type": "array", "items": {"type": "string"}}

    session = scan(body, init=[], state_schema=state_schema)
    encoded = session.body.to_json()
    decoded = Node.from_json(encoded)

    assert session.body.op == Op.LOOP
    assert encoded["stateSchema"] == state_schema
    assert encoded["channels"] == [{"name": "in"}, {"name": "out"}]
    assert decoded.to_json() == encoded
    assert canonical_json(encoded) == canonical_json(session.body.to_json())

    leaf = call("x")
    before = leaf.to_json()
    after = Node.from_json(before).to_json()

    assert after == before
    assert "stateSchema" not in after
    assert "channels" not in after


def test_channelref_json_round_trip_and_key() -> None:
    payload = {"type": "object", "properties": {"text": {"type": "string"}}}
    with_payload = ChannelRef("messages", payload)
    without_payload = ChannelRef("events")

    assert ChannelRef.from_json(with_payload.to_json()) == with_payload
    assert ChannelRef.from_json(without_payload.to_json()) == without_payload
    assert with_payload.to_json() == {"name": "messages", "payload": payload}
    assert without_payload.to_json() == {"name": "events"}
    assert channelref_key(with_payload) == "messages"


def test_recv_and_emit_construct_reserved_tool_leaves() -> None:
    got = recv("topic", timeout_s=7)
    sent = emit("topic", value="ready")

    assert got.op == Op.PRIM
    assert isinstance(got.step, CallStep)
    assert got.step.tool == NativeTool(RECV_TOOL)
    assert got.prompt == "topic"
    assert got.ann is not None
    assert got.ann.timeout == 7

    assert sent.op == Op.PRIM
    assert isinstance(sent.step, CallStep)
    assert sent.step.tool == NativeTool(EMIT_TOOL)
    assert sent.prompt == "topic"
    assert sent.args == {"value": "ready"}


def test_human_gate_keeps_reserved_tool_and_matches_recv_leaf_shape() -> None:
    gate = human_gate(prompt="ok")
    channel_recv = recv(HUMAN_CHANNEL)

    assert isinstance(gate.step, CallStep)
    assert gate.step.tool == NativeTool(HUMAN_GATE_TOOL)
    assert gate.prompt == "ok"

    assert gate.op == channel_recv.op == Op.PRIM
    assert isinstance(channel_recv.step, CallStep)
    assert gate.step.kind == channel_recv.step.kind == "call"
    assert channel_recv.prompt == HUMAN_CHANNEL


def test_loop_is_agent_shaped() -> None:
    session = scan(recv("in"), init={})

    assert surface_shape(session.body) == Shape.AGENT
    assert closed_shape(session.body) == Shape.AGENT


@pytest.mark.asyncio
async def test_scan_and_drive_session_thread_carrier_and_outputs() -> None:
    session = scan(recv("in"), init=[])

    async def step(carrier: object, msg: str) -> tuple[object, str]:
        assert isinstance(carrier, list)
        next_carrier = [*carrier, msg]
        return next_carrier, f"reply:{msg}"

    carrier, outputs = await drive_session(session, step, inputs=["a", "b", "c"])

    assert carrier == ["a", "b", "c"]
    assert outputs == ["reply:a", "reply:b", "reply:c"]


@pytest.mark.asyncio
async def test_drive_session_raises_when_max_turns_exceeded() -> None:
    session = scan(recv("in"), init=0)

    async def step(carrier: object, msg: int) -> tuple[object, int]:
        assert isinstance(carrier, int)
        return carrier + msg, carrier + msg

    with pytest.raises(ComposableAgentsError, match="did not park within 2 turns"):
        await drive_session(session, step, inputs=[1, 2, 3], max_turns=2)


@pytest.mark.asyncio
async def test_channel_buffers_inputs_and_outputs() -> None:
    channel: Channel[str] = Channel("events")
    channel.append("first")
    channel.append("second")

    assert await channel.recv() == "first"
    assert await channel.recv() == "second"

    channel.emit({"ok": True})
    channel.emit("done")
    assert channel.drain() == [{"ok": True}, "done"]
    assert channel.drain() == []


def test_normalize_ids_recurses_into_loop_body() -> None:
    session = scan(call("turn"), init={})

    normalized = normalize_ids(session.body)

    assert normalized.id == "$"
    assert normalized.body is not None
    assert normalized.body.id == "$.B"
