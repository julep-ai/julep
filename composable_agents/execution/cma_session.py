"""CMA-backed per-turn live session handle."""

from __future__ import annotations

import asyncio
import inspect
import contextlib
from collections.abc import AsyncIterator, Callable, Mapping
from typing import Any, Optional

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
    would_exceed_budget,
)
from ..errors import ComposableAgentsError
from ..kinds import EnforcementMode
from ..session import SessionEvent, _local_value_fingerprint
from .cma import CMAClient, CMAEvent, CMASession
from .interpreter import SessionClosed

__all__ = ["CMASessionHandle"]


class CMASessionHandle:
    """SessionHandle-compatible facade backed by one CMA session per turn."""

    _WAKE: object = object()

    def __init__(
        self,
        *,
        client: CMAClient,
        tools: Mapping[str, Callable[[Any], Any]],
        agent: dict[str, Any],
        environment: Any = None,
        in_channel: str = "in",
        out_channel: str = "out",
        session_cid: str = "cma-session",
        cfg: Optional[AgentConfig] = None,
        granted: Optional[set[str]] = None,
        contracts: Optional[AgentContractMap] = None,
    ) -> None:
        self._client = client
        self._tools: dict[str, Callable[[Any], Any]] = dict(tools)
        self._agent = dict(agent)
        self._environment = environment
        self._in_channel = in_channel
        self._out_channel = out_channel
        self._session_cid = session_cid
        self._cfg = cfg or AgentConfig()
        self._granted = granted
        self._contracts = contracts
        self._mode = EnforcementMode.coerce(self._cfg.mode)
        self._prod_gaps: list[str] = []

        self._events: asyncio.Queue[SessionEvent] = asyncio.Queue()
        self._inbound: asyncio.Queue[Any] = asyncio.Queue()
        self._active_session: Optional[CMASession] = None

        self._send_seq = 0
        self._idem: dict[str, dict[str, tuple[int, str]]] = {}
        self._out_seq = 0
        self._turn_seq = 0
        self._completed_turns = 0

        self._closed = False
        self._closing = False
        self._close_reason: Optional[str] = None
        self._closed_event_sent = False
        self._events_subscribed = False
        self._driver = asyncio.create_task(self._drive())

    @classmethod
    async def open(
        cls,
        *,
        client: CMAClient,
        tools: Mapping[str, Callable[[Any], Any]],
        agent: dict[str, Any],
        environment: Any = None,
        in_channel: str = "in",
        out_channel: str = "out",
        session_cid: str = "cma-session",
        cfg: Optional[AgentConfig] = None,
        granted: Optional[set[str]] = None,
        contracts: Optional[AgentContractMap] = None,
    ) -> "CMASessionHandle":
        return cls(
            client=client,
            tools=tools,
            agent=agent,
            environment=environment,
            in_channel=in_channel,
            out_channel=out_channel,
            session_cid=session_cid,
            cfg=cfg,
            granted=granted,
            contracts=contracts,
        )

    async def _drive(self) -> None:
        reason: Optional[str] = None
        try:
            while True:
                item = await self._inbound.get()
                if item is self._WAKE or self._closing:
                    break

                self._turn_seq += 1
                state = AgentState(last=item)
                # CMA starts one hosted session per accepted inbound turn; for
                # recv-then-emit session bodies this aligns with local turn events.
                await self._events.put(SessionEvent.turn_started())
                cma_session = await self._client.create_session(
                    agent=self._agent,
                    environment=self._environment,
                    session_cid=f"{self._session_cid}-turn-{self._turn_seq}",
                    input=item,
                )
                self._active_session = cma_session
                terminal_seen = False

                try:
                    async for event in cma_session.events():
                        if self._closing:
                            break
                        if event.is_custom_tool_use:
                            if not await self._service_tool(cma_session, event, state):
                                reason = "CMA session tool request failed"
                                self._closing = True
                                break
                            continue
                        if event.is_terminal:
                            policy_error = self._terminal_policy_error(state)
                            if policy_error is not None:
                                reason = policy_error
                                self._closing = True
                                await self._events.put(
                                    SessionEvent.error(policy_error, fatal=True)
                                )
                                break
                            await self._handle_terminal(event)
                            terminal_seen = True
                            self._completed_turns += 1
                            break
                        if event.is_error:
                            reason = event.reason or "session error"
                            self._closing = True
                            await self._events.put(
                                SessionEvent.error(reason, fatal=True)
                            )
                            break
                finally:
                    try:
                        await cma_session.cancel()
                    finally:
                        if self._active_session is cma_session:
                            self._active_session = None

                if self._closing:
                    break
                if not terminal_seen:
                    reason = "session ended without terminal output"
                    await self._events.put(SessionEvent.error(reason, fatal=True))
                    break
        except Exception as exc:
            reason = str(exc)
            self._closing = True
            await self._events.put(SessionEvent.error(reason, fatal=True))
        finally:
            self._closed = True
            await self._put_closed_once(self._close_reason or reason)

    async def _service_tool(
        self,
        cma_session: CMASession,
        event: CMAEvent,
        state: AgentState,
    ) -> bool:
        call_id = self._event_call_id(event)
        try:
            tool = self._event_tool(event)
            policy_error, skip_tool = await self._tool_policy_decision(
                cma_session,
                event,
                state,
                tool,
            )
            if policy_error is not None:
                await self._events.put(SessionEvent.error(policy_error, fatal=True))
                return False
            if skip_tool:
                return True
            fn = self._tools[tool]
            call_input = event.input if event.input is not None else state.last
            result = fn(call_input)
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:
            await cma_session.tool_error(call_id, str(exc))
            return True

        cost = action_cost(RoundAction(Decision.CALL, {"tool": tool, "input": event.input}))
        state.charge(cost)
        state.last = result
        state.record(TraceEntry(decision="call", ref=tool, cost=cost))
        state.round += 1
        try:
            await cma_session.tool_result(call_id, result)
        except Exception as exc:
            await self._events.put(
                SessionEvent.error(f"failed to deliver tool result: {exc}", fatal=True)
            )
            return False
        return True

    async def _tool_policy_decision(
        self,
        cma_session: CMASession,
        event: CMAEvent,
        state: AgentState,
        tool: str,
    ) -> tuple[Optional[str], bool]:
        if state.round >= self._cfg.max_rounds:
            return "max_rounds", False

        controller_precheck = precheck_controller(state, self._cfg)
        if controller_precheck is not None:
            return str(controller_precheck["status"]), False

        state.charge(self._cfg.think_cost)
        action = RoundAction(Decision.CALL, {"tool": tool, "input": event.input})
        cost = action_cost(action)
        if would_exceed_budget(state, cost, self._cfg.budget):
            return "over_budget", False

        denial = authorize_call(
            tool,
            unconstrained=self._granted is None,
            granted_set=set(self._granted or set()),
            contracts=self._contracts,
        )
        denial_action = await self._denial_action(cma_session, event, denial)
        if denial_action == "abort":
            return denial.reason if denial is not None else "denied", False
        if denial_action == "skip":
            return None, True

        denial = charge_tool_call(state, tool, self._contracts)
        denial_action = await self._denial_action(cma_session, event, denial)
        if denial_action == "abort":
            return denial.reason if denial is not None else "denied", False
        if denial_action == "skip":
            return None, True
        return None, False

    async def _denial_action(
        self,
        cma_session: CMASession,
        event: CMAEvent,
        denial: Optional[CallDenial],
    ) -> Optional[str]:
        if denial is None:
            return None
        if self._mode is EnforcementMode.DEV:
            self._prod_gaps.append(denial.reason)
            return "skip"
        try:
            await cma_session.tool_error(self._event_call_id(event), denial.reason)
        except Exception:
            pass
        return "abort"

    def _terminal_policy_error(self, state: AgentState) -> Optional[str]:
        if state.round >= self._cfg.max_rounds:
            return "max_rounds"
        controller_precheck = precheck_controller(state, self._cfg)
        if controller_precheck is not None:
            return str(controller_precheck["status"])
        state.charge(self._cfg.think_cost)
        return None

    async def _handle_terminal(self, event: CMAEvent) -> None:
        if event.output is not None:
            self._out_seq += 1
            await self._events.put(
                SessionEvent.emit(self._out_channel, self._out_seq, event.output)
            )
        await self._events.put(SessionEvent.turn_done())

    async def _put_closed_once(self, reason: Optional[str]) -> None:
        if self._closed_event_sent:
            return
        self._closed_event_sent = True
        await self._events.put(SessionEvent.closed(reason))

    def events(self) -> AsyncIterator[SessionEvent]:
        if self._events_subscribed:
            raise ComposableAgentsError("session events() is single-consumer per handle")
        self._events_subscribed = True

        async def gen() -> AsyncIterator[SessionEvent]:
            while True:
                event = await self._events.get()
                yield event
                if event.is_closed:
                    return

        return gen()

    async def send(
        self,
        value: Any,
        *,
        channel: Optional[str] = None,
        idempotency_key: Any = None,
    ) -> dict[str, Any]:
        if self._closed or self._closing:
            raise SessionClosed("session is closed")
        ch = channel or self._in_channel
        if ch != self._in_channel:
            raise ComposableAgentsError(
                f"unsupported channel {ch!r}; CMA session backend accepts only "
                f"the in_channel {self._in_channel!r}"
            )

        if idempotency_key is not None:
            key = str(idempotency_key)
            fingerprint = _local_value_fingerprint(value)
            channel_index = self._idem.setdefault(ch, {})
            prior = channel_index.get(key)
            if prior is not None:
                seq, prior_fingerprint = prior
                if prior_fingerprint != fingerprint:
                    raise ComposableAgentsError(
                        f"idempotency_key {key!r} reused with a different payload "
                        f"on channel {ch!r}"
                    )
                return {"seq": seq, "channel": ch}

        self._send_seq += 1
        self._inbound.put_nowait(value)
        if idempotency_key is not None:
            self._idem.setdefault(ch, {})[str(idempotency_key)] = (
                self._send_seq,
                _local_value_fingerprint(value),
            )
        return {"seq": self._send_seq, "channel": ch}

    async def state(self) -> dict[str, Any]:
        return {
            "closed": self._closed,
            "capacity": None,
            "pending": {self._in_channel: self._inbound.qsize()},
            "turns": self._completed_turns,
        }

    async def open_receives(self) -> list[dict[str, Any]]:
        return []

    async def close(self, reason: Optional[str] = None) -> None:
        if self._closed:
            return
        self._close_reason = reason
        self._closing = True
        active = self._active_session
        if active is not None:
            with contextlib.suppress(Exception):
                await active.cancel()
        self._inbound.put_nowait(self._WAKE)
        self._driver.cancel()
        try:
            await asyncio.wait_for(
                asyncio.gather(self._driver, return_exceptions=True),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            self._driver.cancel()
            await self._put_closed_once(reason)
        finally:
            await self._put_closed_once(reason)

    @staticmethod
    def _event_tool(event: CMAEvent) -> str:
        if event.tool is None:
            raise ComposableAgentsError("custom_tool_use event missing tool")
        return event.tool

    @staticmethod
    def _event_call_id(event: CMAEvent) -> str:
        if event.call_id is None:
            raise ComposableAgentsError("custom_tool_use event missing call_id")
        return event.call_id
