from __future__ import annotations

from typing import Any, Callable

from julep.execution.interpreter import InMemoryEnv
from julep.ir import CallStep, Node, SubStep, toolref_key
from julep.kinds import EnforcementMode, Op
from julep.projection import InMemoryProjection, ProjectionEmitter

EchoHandler = Callable[[Any], Any]


def _echo(value: Any) -> dict[str, Any]:
    """Dev stub: wrap any handler's input in a record so env folds stay happy."""
    return {"output": value}


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


def build_echo_env(node: Node) -> tuple[InMemoryEnv, InMemoryProjection]:
    """Build the offline dev env for a flow: record-returning stubs for every
    tool/reasoner/sub/agent, an auto-approving gate, dev-mode enforcement, and a
    fresh projection to capture events. Mutates ``node`` to clear frozen hashes."""
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
    return env, projection
