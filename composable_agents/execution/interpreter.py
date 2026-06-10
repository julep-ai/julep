"""The deterministic IR interpreter (blueprint §2, the heart of the harness).

This walks a frozen flow and produces a value. It is deliberately *pure of
Temporal*: every effect (calling a hand, invoking a brain, running a child,
compiling a plan, waiting on a human) is delegated to an injected :class:`Env`,
and concurrency goes through ``Env.gather`` / ``Env.race_first`` rather than
``asyncio`` directly. That split is what lets the same interpreter run two ways:

* under Temporal (the real harness builds an ``Env`` whose handlers are
  ``workflow.execute_activity`` calls — see
  :mod:`composable_agents.execution.harness`), where the walk replays
  deterministically from history; and
* under :class:`InMemoryEnv` in tests, where handlers are plain callables, so
  the control-flow logic (seq threading, par/race semantics, alt predicates,
  bounded iteration, plan staging) is verifiable without a Temporal server.

Determinism contract: the interpreter introduces no wall-clock, no randomness,
and no ambient IO. ``cid``s come from ``Env.next_cid`` (a deterministic counter),
``arr``/``alt``/convergence predicates and reducers are named pures looked up via
``Env.get_pure`` and must be deterministic. Anything non-deterministic belongs in
an activity, behind the ``Env`` boundary.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, Protocol, Sequence

from ..contracts import CONSERVATIVE_DEFAULT, ToolManifest
from ..derived import flatten_race_group
from ..errors import CapabilityDenied, ComposableAgentsError, RaceAllFailed
from ..freeze import bind
from ..ir import CallStep, HUMAN_GATE_TOOL, Node, SLEEP_TOOL, SubContract, SubStep, ThinkStep, toolref_key
from ..kinds import EnforcementMode, Op
from ..projection import ProjectionEmitter
from ..registry import DEFAULT_REGISTRY, Registry
from ..shapes import surface_shape
from ..validate import reads_whole_session


# Runtime projection cost defaults for effect leaves without Ann.cost. These
# match the staged estimator's small fallback values.
DEFAULT_CALL_COST = 1.0
DEFAULT_THINK_COST = 2.0
DEFAULT_SUB_COST = 5.0


@dataclass
class Result:
    """A value plus the projection event id that recorded its production."""

    value: Any
    event_id: Optional[str] = None
    attrs: Optional[dict[str, Any]] = None
    reported_cost: Optional[float] = None


@dataclass(frozen=True)
class BranchOutcome:
    """A race-family branch result annotated with its original branch index."""

    index: int
    result: Any


BranchThunk = Callable[[], Awaitable[Any]]


def call_ref_key(node: Node, manifest: ToolManifest) -> str:
    """The tool-ref key for a ``call`` node, frozen or not.

    A flow frozen by :func:`~composable_agents.freeze.freeze` carries a
    ``frozen_hash`` resolving to a manifest entry; a *staged plan* compiled at
    runtime is admitted (§8) but not frozen, so its calls are late-bound here by
    their literal :class:`ToolRef`. This is what lets a stage's plan invoke tools
    without a second freeze pass.
    """
    step = node.step
    assert isinstance(step, CallStep)
    if step.frozen_hash is not None:
        return toolref_key(bind(node, manifest).ref)
    return toolref_key(step.tool)


def call_contract(node: Node, manifest: ToolManifest):
    """The contract for a ``call`` node, frozen or conservatively defaulted."""
    step = node.step
    assert isinstance(step, CallStep)
    if step.frozen_hash is not None:
        return bind(node, manifest).contract
    return CONSERVATIVE_DEFAULT


class Env(Protocol):
    """Everything the interpreter needs from the outside world."""

    manifest: ToolManifest
    emitter: ProjectionEmitter
    # The run's principal (opaque tenant/credential reference, never a secret).
    # The interpreter never reads it; engine envs stamp it into effect payloads.
    principal: Optional[dict[str, Any]]

    def next_cid(self, node_id: str) -> str: ...
    def get_pure(self, name: str) -> Callable[[Any], Any]: ...
    def charge_call(self, tool_key: str) -> None: ...

    async def call_hand(self, node: Node, value: Any, cid: str) -> Any: ...
    async def invoke_brain(
        self,
        brain: str,
        value: Any,
        cid: str,
        timeout_s: Optional[int],
    ) -> Any: ...
    async def run_sub(self, ref: str, contract: SubContract, value: Any, cid: str) -> Any: ...
    async def run_agent(
        self,
        controller: str,
        value: Any,
        cid: str,
        app_config: Optional[dict[str, Any]] = None,
    ) -> Any: ...
    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node: ...
    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any: ...
    async def sleep(self, seconds: int, cid: str) -> None: ...

    async def gather(self, coros: Sequence[Awaitable[Any]]) -> list[Any]: ...
    async def race_first(
        self, branches: Sequence[BranchThunk], *, kind: str, m: int, hedge_ms: Optional[int]
    ) -> Any: ...


async def interpret(
    node: Node,
    value: Any,
    env: Env,
    causes: tuple[str, ...] = (),
    *,
    principal: Optional[dict[str, Any]] = None,
) -> Result:
    """Evaluate ``node`` on ``value``; return its result and recording event id.

    ``principal`` installs a run principal on ``env`` for the in-memory path
    (the engine envs receive theirs from workflow input). It is set once at the
    top-level call; recursion never passes it.
    """
    if principal is not None:
        env.principal = principal
    cid = env.next_cid(node.id)
    shape = surface_shape(node).value
    planned = env.emitter.plan(node.id, cid, causes=causes, shape=shape)

    try:
        out = await _eval(node, value, env, cid, planned)
    except ComposableAgentsError:
        env.emitter.fail(node.id, cid, "framework-error", causes=(planned,))
        raise
    except Exception as e:  # noqa: BLE001 — record then re-raise for the engine
        env.emitter.fail(node.id, cid, repr(e), causes=(planned,))
        raise

    did = env.emitter.did(
        node.id,
        cid,
        value=out.value,
        cost=_projection_cost(node, out.reported_cost),
        shape=shape,
        causes=(planned,),
        attrs=out.attrs,
    )
    return Result(value=out.value, event_id=did)


async def _eval(node: Node, value: Any, env: Env, cid: str, planned: str) -> Result:
    op = node.op

    if op == Op.IDENT:
        return Result(value)

    if op == Op.ARR:
        assert node.pure is not None
        fn = env.get_pure(node.pure)
        return Result(fn(value))

    if op == Op.PRIM:
        return await _eval_prim(node, value, env, cid)

    if op == Op.SEQ:
        assert node.left is not None and node.right is not None
        left = await interpret(node.left, value, env, causes=(planned,))
        right = await interpret(node.right, left.value, env,
                                causes=(left.event_id,) if left.event_id else (planned,))
        return Result(right.value)

    if op == Op.PAR:
        return await _eval_par(node, value, env, planned)

    if op == Op.ALT:
        if node.cases is not None:
            assert node.select is not None
            key = env.get_pure(node.select)(value)
            child = node.cases.get(key, node.default)
            if child is None:
                raise ComposableAgentsError(f"alt: no case for key {key!r} at {node.id!r}")
            return await interpret(child, value, env, causes=(planned,))
        assert node.pure is not None and node.left is not None and node.right is not None
        pred = env.get_pure(node.pure)
        branch = node.left if pred(value) else node.right
        chosen = await interpret(branch, value, env, causes=(planned,))
        return Result(chosen.value)

    if op == Op.ITER_UP_TO:
        assert node.body is not None and node.bound is not None
        conv = env.get_pure(node.pure) if node.pure else None
        cur = value
        last_event = planned
        for _ in range(node.bound):
            r = await interpret(node.body, cur, env, causes=(last_event,))
            cur = r.value
            last_event = r.event_id or last_event
            if conv is not None and conv(cur):
                break
        return Result(cur)

    if op == Op.EVAL_PLAN:
        # Baked plan, or compile one at runtime from the planner controller.
        plan = node.plan
        if plan is None:
            assert node.controller is not None
            plan = await env.compile_plan(node.controller, value, cid)
        r = await interpret(plan, value, env, causes=(planned,))
        return Result(r.value)

    if op == Op.APP:
        assert node.controller is not None
        out = await env.run_agent(node.controller, value, cid, _app_config(node))
        return Result(out)

    raise ComposableAgentsError(f"interpreter: unhandled op {op!r}")


async def _eval_prim(node: Node, value: Any, env: Env, cid: str) -> Result:
    step = node.step
    if isinstance(step, CallStep):
        key = call_ref_key(node, env.manifest)
        env.charge_call(key)
        # Reserved human-gate hand becomes a signal-wait, not an HTTP call.
        if step.tool.kind == "native" and getattr(step.tool, "name", None) == HUMAN_GATE_TOOL:
            timeout_s = node.ann.timeout if node.ann else None
            return Result(await env.human_gate(value, cid, timeout_s))
        # Reserved sleep hand becomes a durable timer, not an HTTP call.
        if step.tool.kind == "native" and getattr(step.tool, "name", None) == SLEEP_TOOL:
            seconds = node.ann.timeout if node.ann and node.ann.timeout is not None else 0
            await env.sleep(seconds, cid)
            return Result(value)
        return Result(await env.call_hand(node, value, cid))
    if isinstance(step, ThinkStep):
        timeout_s = node.ann.timeout if node.ann else None
        out = await env.invoke_brain(step.brain, value, cid, timeout_s)
        return Result(out, reported_cost=_reported_brain_cost(out))
    if isinstance(step, SubStep):
        return Result(await env.run_sub(step.ref, step.contract, value, cid))
    raise ComposableAgentsError(f"interpreter: prim with no usable step at {node.id!r}")


async def _eval_par(node: Node, value: Any, env: Env, planned: str) -> Result:
    merge = node.merge
    kind = merge.kind if merge is not None else "all"

    branches = flatten_race_group(node) if kind in {"race", "hedge", "quorum"} else _all_branches(node)

    if kind in {"race", "hedge", "quorum"}:
        thunks = [
            (lambda idx=idx, b=b: _interpret_branch(idx, b, value, env, planned))
            for idx, b in enumerate(branches)
        ]
        m = (merge.quorum_m if merge and merge.quorum_m else 1)
        hedge_ms = merge.hedge_ms if merge else None
        winner = await env.race_first(thunks, kind=kind, m=m, hedge_ms=hedge_ms)
        outcomes = winner if isinstance(winner, list) else [winner]
        winner_indices = [o.index if isinstance(o, BranchOutcome) else idx for idx, o in enumerate(outcomes)]
        results = [o.result if isinstance(o, BranchOutcome) else o for o in outcomes]
        values = [r.value if isinstance(r, Result) else r for r in results]
        out_value = values if kind == "quorum" else values[0]
        attrs = {
            "merge": kind,
            "winner": winner_indices if kind == "quorum" else winner_indices[0],
            "cancelled": [idx for idx in range(len(branches)) if idx not in set(winner_indices)],
        }
    else:
        degraded = any(reads_whole_session(b) for b in branches)
        if degraded:
            results = []
            for branch in branches:
                results.append(await interpret(branch, value, env, causes=(planned,)))
            attrs = {"merge": "degraded", "reason": "whole_session"}
        else:
            results = await env.gather([interpret(b, value, env, causes=(planned,)) for b in branches])
            attrs = None
        out_value = [r.value if isinstance(r, Result) else r for r in results]

    if merge is not None and merge.reducer is not None:
        out_value = env.get_pure(merge.reducer)(out_value)
    return Result(out_value, attrs=attrs)


async def _interpret_branch(
    idx: int,
    branch: Node,
    value: Any,
    env: Env,
    planned: str,
) -> BranchOutcome:
    return BranchOutcome(idx, await interpret(branch, value, env, causes=(planned,)))


def _projection_cost(node: Node, reported_cost: Optional[float]) -> Optional[float]:
    if node.ann is not None and node.ann.cost is not None:
        return float(node.ann.cost)
    if node.op != Op.PRIM:
        return None

    step = node.step
    if isinstance(step, ThinkStep):
        return reported_cost if reported_cost is not None else DEFAULT_THINK_COST
    if isinstance(step, SubStep):
        return DEFAULT_SUB_COST
    if isinstance(step, CallStep):
        return DEFAULT_CALL_COST
    return None


def _reported_brain_cost(value: Any) -> Optional[float]:
    if not isinstance(value, dict):
        return None

    direct = _numeric_cost(value)
    if direct is not None:
        return direct

    for key in ("usage", "metadata", "meta"):
        nested = value.get(key)
        if isinstance(nested, dict):
            nested_cost = _numeric_cost(nested)
            if nested_cost is not None:
                return nested_cost
    return None


def _numeric_cost(data: dict[str, Any]) -> Optional[float]:
    for key in ("cost", "costUsd", "cost_usd", "totalCostUsd", "total_cost_usd"):
        cost = data.get(key)
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            return float(cost)
    return None


def _all_branches(node: Node) -> list[Node]:
    """Flatten a plain (``all``) ``par`` spine into its leaf branches."""
    out: list[Node] = []

    def rec(n: Node) -> None:
        if n.op == Op.PAR and (n.merge is None or n.merge.kind == "all"):
            assert n.left is not None and n.right is not None
            rec(n.left)
            rec(n.right)
        else:
            out.append(n)

    rec(node)
    return out


def _app_config(node: Node) -> Optional[dict[str, Any]]:
    encoded = node.to_json()
    config = {
        key: encoded[key]
        for key in ("tools", "subflows", "budget", "maxRounds")
        if key in encoded
    }
    return config or None


async def _raise_branch_failure(exc: Exception) -> Any:
    raise exc


async def race_first_from_thunks(
    branches: Sequence[BranchThunk],
    *,
    kind: str,
    m: int,
    hedge_ms: Optional[int],
    wait_first: Callable[
        [Sequence[Awaitable[Any]]],
        Awaitable[tuple[set[Awaitable[Any]], set[Awaitable[Any]]]],
    ],
) -> Any:
    """Settle a race-family group on successful branch results.

    ``wait_first`` is injected so the in-memory env can use ``asyncio.wait``
    while the Temporal env uses ``workflow.wait`` for replay-safe waiting.
    """

    total = len(branches)
    need = m if kind == "quorum" else 1
    if total == 0:
        raise RaceAllFailed([])

    tasks: list[asyncio.Future[Any] | None] = [None] * total
    running: set[asyncio.Future[Any]] = set()
    successes: dict[int, Any] = {}
    failures: dict[int, Exception] = {}
    timer: asyncio.Future[Any] | None = None

    def ordered_failures() -> list[Exception]:
        return [failures[i] for i in range(total) if i in failures]

    def start(idx: int) -> None:
        try:
            awaitable = branches[idx]()
        except Exception as exc:  # Synchronous thunk construction failure.
            awaitable = _raise_branch_failure(exc)
        task = asyncio.ensure_future(awaitable)
        tasks[idx] = task
        running.add(task)

    def process_done(done: set[Awaitable[Any]]) -> None:
        for idx, task in enumerate(tasks):
            if task is None or task not in done or idx in successes or idx in failures:
                continue
            try:
                successes[idx] = task.result()
            except Exception as exc:  # Branch failure; ignore until settlement is impossible.
                failures[idx] = exc

    def settlement() -> tuple[bool, Any]:
        if len(successes) >= need:
            ordered_successes = [successes[i] for i in sorted(successes)[:need]]
            return True, ordered_successes if kind == "quorum" else ordered_successes[0]
        if len(failures) > total - need:
            raise RaceAllFailed(ordered_failures())
        return False, None

    async def wait_for_first(waitset: set[Awaitable[Any]]) -> set[Awaitable[Any]]:
        done, _ = await wait_first(list(waitset))
        return set(done)

    try:
        if kind == "hedge" and hedge_ms is not None and hedge_ms > 0:
            start(0)
            next_idx = 1
            delay_s = hedge_ms / 1000.0
            while True:
                settled, value = settlement()
                if settled:
                    return value
                if timer is None and next_idx < total:
                    timer = asyncio.ensure_future(asyncio.sleep(delay_s))
                waitset: set[Awaitable[Any]] = set(running)
                if timer is not None:
                    waitset.add(timer)
                if not waitset:
                    raise RaceAllFailed(ordered_failures())

                done = await wait_for_first(waitset)
                branch_done = {t for t in done if t is not timer}
                running.difference_update(branch_done)
                process_done(branch_done)

                settled, value = settlement()
                if settled:
                    return value
                if timer is not None and timer in done:
                    timer = None
                    if next_idx < total:
                        start(next_idx)
                        next_idx += 1

        for idx in range(total):
            start(idx)
        pending = {t for t in tasks if t is not None}
        while True:
            settled, value = settlement()
            if settled:
                return value
            if not pending:
                raise RaceAllFailed(ordered_failures())
            done, pending_after = await wait_first(list(pending))
            done_set = set(done)
            pending = set(pending_after)
            process_done(done_set)
    finally:
        if timer is not None and not timer.done():
            timer.cancel()
        for task in tasks:
            if task is not None and not task.done():
                task.cancel()


async def gather_bounded(
    coros: Sequence[Awaitable[Any]],
    *,
    max_parallel: Optional[int],
) -> list[Any]:
    """``asyncio.gather`` with an optional concurrency ceiling.

    ``None`` (or a non-positive value) means unbounded — the existing behavior.
    A semaphore is replay-deterministic under Temporal's sandboxed event loop,
    so both engine envs share this helper.
    """
    items = list(coros)
    if max_parallel is None or max_parallel <= 0 or len(items) <= max_parallel:
        return list(await asyncio.gather(*items))

    sem = asyncio.Semaphore(max_parallel)

    async def gated(coro: Awaitable[Any]) -> Any:
        async with sem:
            return await coro

    return list(await asyncio.gather(*(gated(c) for c in items)))


# --------------------------------------------------------------------------- #
# In-memory Env for tests and local dry-runs (no Temporal, no network).
# --------------------------------------------------------------------------- #
class InMemoryEnv:
    """A deterministic, dependency-free :class:`Env`.

    Effect handlers are plain callables you supply (``hands``: name -> fn,
    ``brains``: name -> fn, etc.). Concurrency uses ``asyncio`` but stays
    deterministic for the control-flow under test: ``race_first`` resolves
    already-ready coroutines in branch order, so a race over synchronous fakes
    picks the first branch — exactly what a golden test wants to assert.
    """

    def __init__(
        self,
        manifest: ToolManifest,
        emitter: ProjectionEmitter,
        *,
        hands: Optional[dict[str, Callable[[Any], Any]]] = None,
        brains: Optional[dict[str, Callable[[Any], Any]]] = None,
        subs: Optional[dict[str, Callable[[Any], Any]]] = None,
        agents: Optional[dict[str, Callable[[Any], Any]]] = None,
        planners: Optional[dict[str, Callable[[Any], Node]]] = None,
        gate: Optional[Callable[[Any], Any]] = None,
        sleeper: Optional[Callable[[int], Awaitable[None]]] = None,
        max_parallel: Optional[int] = None,
        max_calls: Optional[dict[str, int]] = None,
        mode: EnforcementMode | str = EnforcementMode.STRICT,
        registry: Optional[Registry] = None,
        principal: Optional[dict[str, Any]] = None,
    ) -> None:
        self.manifest = manifest
        self.emitter = emitter
        self.principal = principal
        self._hands = hands or {}
        self._brains = brains or {}
        self._subs = subs or {}
        self._agents = agents or {}
        self._planners = planners or {}
        self._gate = gate or (lambda v: {"approved": True, "input": v})
        self._sleeper = sleeper
        self.max_parallel = max_parallel
        self._max_calls = dict(max_calls or {})
        self.mode = EnforcementMode.coerce(mode)
        self.dev_warnings: list[dict[str, Any]] = []
        self._registry = registry
        self.call_counts: dict[str, int] = {}
        self.sleeps: list[int] = []
        self._cid = 0

    # --- identity / pures --- #
    def next_cid(self, node_id: str) -> str:
        self._cid += 1
        return f"{node_id}@{self._cid}"

    def get_pure(self, name: str) -> Callable[[Any], Any]:
        registry = self._registry or DEFAULT_REGISTRY
        return registry.get_pure(name)

    def charge_call(self, tool_key: str) -> None:
        limit = self._max_calls.get(tool_key)
        if limit is None:
            return
        count = self.call_counts.get(tool_key, 0)
        if count >= limit:
            if self.mode is EnforcementMode.DEV:
                self.dev_warnings.append(
                    {
                        "code": "CAP_TOOL_DENIED_RUNTIME",
                        "tool": tool_key,
                        "limit": limit,
                    }
                )
                self.call_counts[tool_key] = count + 1
                return
            raise CapabilityDenied(f"tool {tool_key!r} exceeded maxCalls={limit}")
        self.call_counts[tool_key] = count + 1

    # --- effect handlers --- #
    async def call_hand(self, node: Node, value: Any, cid: str) -> Any:
        key = call_ref_key(node, self.manifest)
        fn = self._hands.get(key)
        if fn is None:
            raise KeyError(f"no in-memory hand for {key!r}")
        return fn(value)

    async def invoke_brain(
        self,
        brain: str,
        value: Any,
        cid: str,
        timeout_s: Optional[int],
    ) -> Any:
        if brain not in self._brains:
            raise KeyError(f"no in-memory brain for {brain!r}")
        return self._brains[brain](value)

    async def run_sub(self, ref: str, contract: SubContract, value: Any, cid: str) -> Any:
        if ref not in self._subs:
            raise KeyError(f"no in-memory sub for {ref!r}")
        return self._subs[ref](value)

    async def run_agent(
        self,
        controller: str,
        value: Any,
        cid: str,
        app_config: Optional[dict[str, Any]] = None,
    ) -> Any:
        if controller not in self._agents:
            raise KeyError(f"no in-memory agent for {controller!r}")
        out = self._agents[controller](value)
        return await out if inspect.isawaitable(out) else out

    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node:
        if planner not in self._planners:
            raise KeyError(f"no in-memory planner for {planner!r}")
        return self._planners[planner](value)

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        return self._gate(value)

    async def sleep(self, seconds: int, cid: str) -> None:
        self.sleeps.append(seconds)
        if self._sleeper is not None:
            await self._sleeper(seconds)

    # --- concurrency --- #
    async def gather(self, coros: Sequence[Awaitable[Any]]) -> list[Any]:
        return await gather_bounded(coros, max_parallel=self.max_parallel)

    async def race_first(
        self, branches: Sequence[BranchThunk], *, kind: str, m: int, hedge_ms: Optional[int]
    ) -> Any:
        async def wait_first(
            waitset: Sequence[Awaitable[Any]],
        ) -> tuple[set[Awaitable[Any]], set[Awaitable[Any]]]:
            done, pending = await asyncio.wait(waitset, return_when=asyncio.FIRST_COMPLETED)
            return set(done), set(pending)

        return await race_first_from_thunks(
            branches,
            kind=kind,
            m=m,
            hedge_ms=hedge_ms,
            wait_first=wait_first,
        )


def _ref_name(tool) -> str:
    ref = tool.ref
    j = ref.to_json()
    return j.get("name") if j.get("kind") == "native" else f"{j['server']}/{j['tool']}"
