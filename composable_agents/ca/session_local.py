from __future__ import annotations

import json
from typing import Any

from composable_agents.ca._echo import (
    _clear_frozen_hashes,
    _echo_agents,
    _echo_reasoners,
    _echo_subs,
    _echo_tools,
)
from composable_agents.ca.resolve import ResolvedAgent
from composable_agents.derived import emit, recv
from composable_agents.dsl import arr, seq
from composable_agents.ir import Node
from composable_agents.kinds import EnforcementMode
from composable_agents.session import LocalSessionHandle, Session, SessionEvent, loop

IN_CHANNEL = "in"
OUT_CHANNEL = "out"


def parse_json_or_raw(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def event_to_json(event: SessionEvent) -> dict[str, Any]:
    return {
        "kind": event.kind,
        "channel": event.channel,
        "seq": event.seq,
        "payload": event.payload,
        "turn": event.turn,
        "reason": event.reason,
        "fatal": event.fatal,
    }


def build_session(resolved: ResolvedAgent) -> tuple[Session[Any, Any], Node]:
    """Wrap a resolved agent's turn flow as a session LOOP body."""
    if resolved.error is not None:
        raise ValueError(resolved.error)
    node = Node.from_json(resolved.ir)
    _clear_frozen_hashes(node)
    body = seq(recv(IN_CHANNEL), arr("std.pluck", {"key": "msg"}), node, emit(OUT_CHANNEL))
    session = loop(body, init=None, in_channel=IN_CHANNEL, out_channel=OUT_CHANNEL)
    return session, node


async def open_local_session(resolved: ResolvedAgent) -> LocalSessionHandle:
    session, node = build_session(resolved)
    return await LocalSessionHandle.open(
        session,
        tools=_echo_tools(node),
        reasoners=_echo_reasoners(node),
        subs=_echo_subs(node),
        agents=_echo_agents(node),
        mode=EnforcementMode.DEV,
    )
