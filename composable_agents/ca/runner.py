from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

from composable_agents.ca.resolve import ResolvedAgent
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.ir import CallStep, Node, SubStep, toolref_key
from composable_agents.kinds import EnforcementMode, Op
from composable_agents.projection import InMemoryProjection, ProjectionEmitter, ProjectionEvent

EchoHandler = Callable[[Any], Any]


@dataclass(frozen=True)
class RunOutcome:
    """The result of executing a resolved agent locally.

    ``error`` is ``None`` on success; on failure it carries the message and
    ``value`` is ``None``. ``events`` holds whatever the projection captured
    before the run finished (possibly empty on early failure).
    """

    run_id: str
    value: Any
    events: list[ProjectionEvent] = field(default_factory=list)
    error: str | None = None


def _echo(value: Any) -> dict[str, Any]:
    """Dev stub: wrap any handler's input in a record.

    Env pures (``std.init``/``std.assign``/``std.collect``/``std.merge``) treat
    each env field as a dict, so a record-returning stub keeps those folds happy
    where a bare ``lambda v: v`` (which can yield a scalar) would make ``merge``
    raise. This is the offline echo semantics the local runner advertises.
    """

    return {"output": value}


def run_agent_local(resolved: ResolvedAgent, value: Any, *, run_id: str) -> RunOutcome:
    """Execute a resolved agent in-memory, owning the projection to return events.

    Mirrors the proven echo-stub wiring in ``composable_agents.cli._cmd_run_local``:
    an empty manifest, frozen hashes cleared, record-returning stubs for every
    tool/reasoner/sub/agent, an auto-approving gate, and dev-mode enforcement so
    effectful calls do not block. Any runtime failure (including a malformed IR
    dict) is surfaced as ``RunOutcome.error`` rather than propagating.
    """

    if resolved.error is not None:
        return RunOutcome(run_id=run_id, value=None, events=[], error=resolved.error)

    projection: InMemoryProjection | None = None
    try:
        node = Node.from_json(resolved.ir)
        _clear_frozen_hashes(node)

        projection = InMemoryProjection()
        env = InMemoryEnv(
            {},
            ProjectionEmitter(projection),
            tools=_echo_tools(node),
            reasoners=_echo_reasoners(node),
            subs=_echo_subs(node),
            agents=_echo_agents(node),
            gate=lambda value: {"approved": True, "input": value},
            mode=EnforcementMode.DEV,
        )
        result = asyncio.run(interpret(node, value, env))
    except Exception as exc:  # noqa: BLE001 - surface runtime errors in the outcome, never crash.
        events = projection.events() if projection is not None else []
        return RunOutcome(run_id=run_id, value=None, events=events, error=str(exc))

    return RunOutcome(run_id=run_id, value=result.value, events=projection.events(), error=None)


def _clear_frozen_hashes(flow: Node) -> None:
    for node in flow.walk():
        step = node.step
        if isinstance(step, CallStep):
            step.frozen_hash = None


def _echo_tools(flow: Node) -> dict[str, EchoHandler]:
    tools: dict[str, EchoHandler] = {}
    for ref in flow.tool_refs():
        tools[toolref_key(ref)] = _echo
    return tools


def _echo_reasoners(flow: Node) -> dict[str, EchoHandler]:
    reasoners: dict[str, EchoHandler] = {}
    for node in flow.walk():
        step = node.step
        reasoner = getattr(step, "reasoner", None)
        if isinstance(reasoner, str):
            reasoners[reasoner] = _echo
        if node.op in {Op.APP, Op.EVAL_PLAN} and node.controller is not None:
            reasoners[node.controller] = _echo
    return reasoners


def _echo_subs(flow: Node) -> dict[str, EchoHandler]:
    subs: dict[str, EchoHandler] = {}
    for node in flow.walk():
        step = node.step
        if isinstance(step, SubStep):
            subs[step.ref] = _echo
    return subs


def _echo_agents(flow: Node) -> dict[str, EchoHandler]:
    agents: dict[str, EchoHandler] = {}
    for node in flow.walk():
        if node.op == Op.APP and node.controller is not None:
            agents[node.controller] = _echo
    return agents
