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

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, Protocol, Sequence

from ..contracts import CONSERVATIVE_DEFAULT, ToolManifest
from ..derived import flatten_race_group
from ..errors import ComposableAgentsError
from ..freeze import bind
from ..ir import CallStep, HUMAN_GATE_TOOL, Node, SubContract, SubStep, ThinkStep, toolref_key
from ..kinds import Op
from ..purity import get_pure as _registry_get_pure
from ..projection import ProjectionEmitter
from ..shapes import surface_shape


@dataclass
class Result:
    """A value plus the projection event id that recorded its production."""

    value: Any
    event_id: Optional[str] = None


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

    def next_cid(self, node_id: str) -> str: ...
    def get_pure(self, name: str) -> Callable[[Any], Any]: ...

    async def call_hand(self, node: Node, value: Any, cid: str) -> Any: ...
    async def invoke_brain(self, brain: str, value: Any, cid: str) -> Any: ...
    async def run_sub(self, ref: str, contract: SubContract, value: Any, cid: str) -> Any: ...
    async def run_agent(self, controller: str, value: Any, cid: str) -> Any: ...
    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node: ...
    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any: ...

    async def gather(self, coros: Sequence[Awaitable[Any]]) -> list[Any]: ...
    async def race_first(
        self, coros: Sequence[Awaitable[Any]], *, kind: str, m: int, hedge_ms: Optional[int]
    ) -> Any: ...


async def interpret(node: Node, value: Any, env: Env, causes: tuple[str, ...] = ()) -> Result:
    """Evaluate ``node`` on ``value``; return its result and recording event id."""
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

    did = env.emitter.did(node.id, cid, value=out.value, shape=shape, causes=(planned,))
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
        out = await env.run_agent(node.controller, value, cid)
        return Result(out)

    raise ComposableAgentsError(f"interpreter: unhandled op {op!r}")


async def _eval_prim(node: Node, value: Any, env: Env, cid: str) -> Result:
    step = node.step
    if isinstance(step, CallStep):
        # Reserved human-gate hand becomes a signal-wait, not an HTTP call.
        if step.tool.kind == "native" and getattr(step.tool, "name", None) == HUMAN_GATE_TOOL:
            timeout_s = node.ann.timeout if node.ann else None
            return Result(await env.human_gate(value, cid, timeout_s))
        return Result(await env.call_hand(node, value, cid))
    if isinstance(step, ThinkStep):
        return Result(await env.invoke_brain(step.brain, value, cid))
    if isinstance(step, SubStep):
        return Result(await env.run_sub(step.ref, step.contract, value, cid))
    raise ComposableAgentsError(f"interpreter: prim with no usable step at {node.id!r}")


async def _eval_par(node: Node, value: Any, env: Env, planned: str) -> Result:
    merge = node.merge
    kind = merge.kind if merge is not None else "all"

    branches = flatten_race_group(node) if kind in {"race", "hedge", "quorum"} else _all_branches(node)

    if kind in {"race", "hedge", "quorum"}:
        coros = [interpret(b, value, env, causes=(planned,)) for b in branches]
        m = (merge.quorum_m if merge and merge.quorum_m else 1)
        hedge_ms = merge.hedge_ms if merge else None
        winner = await env.race_first(coros, kind=kind, m=m, hedge_ms=hedge_ms)
        results = winner if isinstance(winner, list) else [winner]
        values = [r.value if isinstance(r, Result) else r for r in results]
        out_value = values if kind == "quorum" else values[0]
    else:
        results = await env.gather([interpret(b, value, env, causes=(planned,)) for b in branches])
        out_value = [r.value if isinstance(r, Result) else r for r in results]

    if merge is not None and merge.reducer is not None:
        out_value = env.get_pure(merge.reducer)(out_value)
    return Result(out_value)


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
    ) -> None:
        self.manifest = manifest
        self.emitter = emitter
        self._hands = hands or {}
        self._brains = brains or {}
        self._subs = subs or {}
        self._agents = agents or {}
        self._planners = planners or {}
        self._gate = gate or (lambda v: {"approved": True, "input": v})
        self._cid = 0

    # --- identity / pures --- #
    def next_cid(self, node_id: str) -> str:
        self._cid += 1
        return f"{node_id}@{self._cid}"

    def get_pure(self, name: str) -> Callable[[Any], Any]:
        return _registry_get_pure(name)

    # --- effect handlers --- #
    async def call_hand(self, node: Node, value: Any, cid: str) -> Any:
        key = call_ref_key(node, self.manifest)
        fn = self._hands.get(key)
        if fn is None:
            raise KeyError(f"no in-memory hand for {key!r}")
        return fn(value)

    async def invoke_brain(self, brain: str, value: Any, cid: str) -> Any:
        if brain not in self._brains:
            raise KeyError(f"no in-memory brain for {brain!r}")
        return self._brains[brain](value)

    async def run_sub(self, ref: str, contract: SubContract, value: Any, cid: str) -> Any:
        if ref not in self._subs:
            raise KeyError(f"no in-memory sub for {ref!r}")
        return self._subs[ref](value)

    async def run_agent(self, controller: str, value: Any, cid: str) -> Any:
        if controller not in self._agents:
            raise KeyError(f"no in-memory agent for {controller!r}")
        return self._agents[controller](value)

    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node:
        if planner not in self._planners:
            raise KeyError(f"no in-memory planner for {planner!r}")
        return self._planners[planner](value)

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        return self._gate(value)

    # --- concurrency --- #
    async def gather(self, coros: Sequence[Awaitable[Any]]) -> list[Any]:
        import asyncio

        return list(await asyncio.gather(*coros))

    async def race_first(
        self, coros: Sequence[Awaitable[Any]], *, kind: str, m: int, hedge_ms: Optional[int]
    ) -> Any:
        import asyncio

        tasks = [asyncio.ensure_future(c) for c in coros]
        done_results: list[Any] = []
        need = m if kind == "quorum" else 1
        try:
            pending = set(tasks)
            while pending and len(done_results) < need:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                # Preserve branch order among the just-completed set.
                for t in tasks:
                    if t in done:
                        done_results.append(t.result())
            if kind == "quorum":
                return done_results[:need]
            return done_results[0]
        finally:
            for t in tasks:
                if not t.done():
                    t.cancel()


def _ref_name(tool) -> str:
    ref = tool.ref
    j = ref.to_json()
    return j.get("name") if j.get("kind") == "native" else f"{j['server']}/{j['tool']}"
