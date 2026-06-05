"""Pure Claude Managed Agents execution-layer adapter.

This module contains only the normalized CMA event loop and a structural
``Env`` wrapper for the interpreter's ``run_agent`` seam. Vendor SDK and
network translation belongs in a separate adapter that produces ``CMAEvent``
values and implements the protocols below.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Protocol

from ..agent_loop import (
    AgentConfig,
    AgentContractMap,
    AgentState,
    CallDenial,
    Decision,
    RoundAction,
    TraceEntry,
    action_cost,
    authorize_call,
    charge_tool_call,
    precheck_controller,
    terminal_result,
    would_exceed_budget,
)
from ..kinds import EnforcementMode

if TYPE_CHECKING:
    from .interpreter import BranchThunk, Env
    from ..ir import Node, SubContract
else:
    Env = Any


# --------------------------------------------------------------------------- #
# Normalized CMA events and protocols.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CMAEvent:
    """A normalized session event the driver consumes.

    The CMA-specific correlation (agent.custom_tool_use +
    session.status_idle/requires_action + event IDs, end_turn, session.error) is
    the adapter's job; by the time an event reaches the driver it is one of
    three normalized kinds.
    """

    kind: str
    tool: Optional[str] = None
    input: Any = None
    call_id: Optional[str] = None
    output: Any = None
    reason: Optional[str] = None
    usage: Optional[dict[str, Any]] = None

    @property
    def is_custom_tool_use(self) -> bool:
        return self.kind == "custom_tool_use"

    @property
    def is_terminal(self) -> bool:
        return self.kind == "terminal"

    @property
    def is_error(self) -> bool:
        return self.kind == "error"


class CMASession(Protocol):
    """One running managed-agent session. Async-iterable normalized events."""

    def events(self) -> AsyncIterator[CMAEvent]: ...
    async def tool_result(self, call_id: str, result: Any) -> None: ...
    async def tool_error(self, call_id: str, reason: str) -> None: ...
    async def cancel(self) -> None: ...


class CMAClient(Protocol):
    async def create_session(
        self,
        *,
        agent: dict[str, Any],
        environment: Any,
        session_cid: str,
    ) -> CMASession: ...


# --------------------------------------------------------------------------- #
# Manifest projection.
# --------------------------------------------------------------------------- #
def manifest_to_custom_tools(
    tool_names: Iterable[str],
    *,
    input_schemas: Optional[Mapping[str, dict[str, Any]]] = None,
    descriptions: Optional[Mapping[str, str]] = None,
) -> list[dict[str, Any]]:
    """Project granted tools into CMA custom-tool definitions.

    This intentionally emits only manifest-named custom tools and never includes
    the built-in ``agent_toolset_20260401``. SPEC §7 is deny-by-default: the
    hosted model must see only the already-granted surface.
    """
    schemas = input_schemas or {}
    descs = descriptions or {}
    return [
        {
            "type": "custom",
            "name": name,
            "description": descs.get(name, ""),
            "input_schema": schemas.get(name, {"type": "object"}),
        }
        for name in tool_names
        if name != "agent_toolset_20260401"
    ]


# --------------------------------------------------------------------------- #
# Inverted CMA agent loop.
# --------------------------------------------------------------------------- #
async def drive_cma_agent_loop(
    *,
    input: Any,
    cfg: AgentConfig,
    session: CMASession,
    call_tool: Callable[[str, Any, str], Awaitable[Any]],
    granted: Optional[set[str]] = None,
    contracts: Optional[AgentContractMap] = None,
    state: Optional[AgentState] = None,
    session_cid: str = "cma",
) -> dict[str, Any]:
    """Drive a normalized CMA session through the same gates as the local loop."""
    mode = EnforcementMode.coerce(cfg.mode)
    prod_gap: list[str] = []
    state = state or AgentState(last=input)
    unconstrained = granted is None
    granted_set = set(granted or [])

    def finish(status: str, output: Any = None, reason: Optional[str] = None) -> dict[str, Any]:
        result = terminal_result(status, state, output=output, reason=reason)
        if prod_gap:
            result["prodGap"] = list(prod_gap)
        return result

    async def strict_denial_or_dev_gap(ev: CMAEvent, denial: Optional[CallDenial]) -> bool:
        if denial is None:
            return False
        if mode is EnforcementMode.DEV:
            prod_gap.append(denial.reason)
            return False
        await session.tool_error(_event_call_id(ev), denial.reason)
        return True

    try:
        async for ev in session.events():
            if ev.is_error:
                return finish("controller_error", reason=ev.reason or "session error")

            if ev.is_terminal:
                state.charge(cfg.think_cost)
                return finish("done", output=ev.output)

            if not ev.is_custom_tool_use:
                continue

            if state.round >= cfg.max_rounds:
                return finish("max_rounds")

            controller_precheck = precheck_controller(state, cfg)
            if controller_precheck is not None:
                if prod_gap:
                    controller_precheck["prodGap"] = list(prod_gap)
                return controller_precheck

            state.charge(cfg.think_cost)
            tool = _event_tool(ev)
            action = RoundAction(Decision.CALL, {"tool": tool, "input": ev.input})
            cost = action_cost(action)
            if would_exceed_budget(state, cost, cfg.budget):
                return finish("over_budget")

            denial = authorize_call(
                tool,
                unconstrained=unconstrained,
                granted_set=granted_set,
                contracts=contracts,
            )
            if await strict_denial_or_dev_gap(ev, denial):
                return finish("denied", reason=denial.reason if denial is not None else None)

            denial = charge_tool_call(state, tool, contracts)
            if await strict_denial_or_dev_gap(ev, denial):
                return finish("denied", reason=denial.reason if denial is not None else None)
            if denial is not None:
                state.call_counts[tool] = state.call_counts.get(tool, 0) + 1

            call_input = ev.input if ev.input is not None else state.last
            call_cid = f"{session_cid}-call-{state.round}"
            out = await call_tool(tool, call_input, call_cid)
            state.charge(cost)
            state.last = out
            state.record(TraceEntry(decision="call", ref=tool, cost=cost))
            state.round += 1
            await session.tool_result(_event_call_id(ev), out)

        return finish("controller_error", reason="session ended without terminal output")
    finally:
        await session.cancel()


def _event_tool(ev: CMAEvent) -> str:
    if ev.tool is None:
        raise ValueError("custom_tool_use event missing tool")
    return ev.tool


def _event_call_id(ev: CMAEvent) -> str:
    if ev.call_id is None:
        raise ValueError("custom_tool_use event missing call_id")
    return ev.call_id


# --------------------------------------------------------------------------- #
# Env wrapper for the app-node run_agent seam.
# --------------------------------------------------------------------------- #
class CMAAgentEnv:
    """An ``Env`` wrapper that replaces only ``run_agent`` with CMA execution."""

    def __init__(
        self,
        inner: Env,
        *,
        client: CMAClient,
        environment: Any = None,
        hands: Mapping[str, Callable[[Any], Any]],
        cfg: AgentConfig,
        granted: Optional[set[str]] = None,
        contracts: Optional[AgentContractMap] = None,
        custom_tools: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        self._inner = inner
        self.manifest = inner.manifest
        self.emitter = inner.emitter
        self._client = client
        self._environment = environment
        self._hands = hands
        self._cfg = cfg
        self._granted = granted
        self._contracts = contracts
        self._custom_tools = custom_tools

    def next_cid(self, node_id: str) -> str:
        return self._inner.next_cid(node_id)

    def get_pure(self, name: str) -> Callable[[Any], Any]:
        return self._inner.get_pure(name)

    def charge_call(self, tool_key: str) -> None:
        return self._inner.charge_call(tool_key)

    async def call_hand(self, node: Node, value: Any, cid: str) -> Any:
        return await self._inner.call_hand(node, value, cid)

    async def invoke_brain(
        self,
        brain: str,
        value: Any,
        cid: str,
        timeout_s: Optional[int],
    ) -> Any:
        return await self._inner.invoke_brain(brain, value, cid, timeout_s)

    async def run_sub(self, ref: str, contract: SubContract, value: Any, cid: str) -> Any:
        return await self._inner.run_sub(ref, contract, value, cid)

    async def run_agent(
        self,
        controller: str,
        value: Any,
        cid: str,
        app_config: Optional[dict[str, Any]] = None,
    ) -> Any:
        cfg = _cfg_with_app_overrides(self._cfg, app_config)
        agent_payload = {
            "name": controller,
            "tools": self._custom_tools or manifest_to_custom_tools(self._granted or []),
        }
        session = await self._client.create_session(
            agent=agent_payload,
            environment=self._environment,
            session_cid=cid,
        )

        async def call_tool(tool: str, v: Any, _call_cid: str) -> Any:
            fn = self._hands.get(tool)
            if fn is None:
                return {"error": f"tool {tool!r} unavailable"}
            result = fn(v)
            return await result if inspect.isawaitable(result) else result

        return await drive_cma_agent_loop(
            input=value,
            cfg=cfg,
            session=session,
            call_tool=call_tool,
            granted=self._granted,
            contracts=self._contracts,
            session_cid=cid,
        )

    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node:
        return await self._inner.compile_plan(planner, value, cid)

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        return await self._inner.human_gate(value, cid, timeout_s)

    async def gather(self, coros: Sequence[Awaitable[Any]]) -> list[Any]:
        return await self._inner.gather(coros)

    async def race_first(
        self,
        branches: Sequence[BranchThunk],
        *,
        kind: str,
        m: int,
        hedge_ms: Optional[int],
    ) -> Any:
        return await self._inner.race_first(branches, kind=kind, m=m, hedge_ms=hedge_ms)


def _cfg_with_app_overrides(
    cfg: AgentConfig,
    app_config: Optional[dict[str, Any]],
) -> AgentConfig:
    if not app_config or ("budget" not in app_config and "maxRounds" not in app_config):
        return cfg
    data = cfg.to_json()
    if "budget" in app_config:
        data["budget"] = app_config["budget"]
    if "maxRounds" in app_config:
        data["maxRounds"] = app_config["maxRounds"]
    return AgentConfig.from_json(data)


__all__ = [
    "CMAEvent",
    "CMASession",
    "CMAClient",
    "CMAAgentEnv",
    "drive_cma_agent_loop",
    "manifest_to_custom_tools",
]
