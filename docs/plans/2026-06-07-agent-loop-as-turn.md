# Agent Loop as Iterated Turn — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reify the agent loop's per-round body as a first-class `Step` endomorphism on `AgentState`, driven by a thin `drive` combinator, so rounds become decoratable and unit-testable — with byte-identical behavior to today's `drive_agent_loop`.

**Architecture:** New pure module `composable_agents/turn.py` holds `Halt`, the `Step` type, the `drive` iterator, and `controller_turn`/`pre_round`/`make_finalize` extracted verbatim from `drive_agent_loop`'s `while True` body (`agent_loop.py:441–518`). `drive_agent_loop` then becomes a thin wrapper that wires those together. `Op.ITER_UP_TO` and `continue_as_new` are untouched (the latter stays a Temporal-harness concern, `harness.py:741`). The existing agent-loop test suite is the parity gate.

**Tech Stack:** Python 3, `asyncio`, pytest (`addopts = -q`, `testpaths = ["tests"]`).

**Design spec:** `docs/design/agent-loop-as-turn.md`.

---

### Task 1: `turn.py` — `Halt`, `Step`, and the `drive` iterator

**Files:**
- Create: `composable_agents/turn.py`
- Test: `tests/invariants/test_turn.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/invariants/test_turn.py
import asyncio
from typing import Any

from composable_agents.agent_loop import AgentState
from composable_agents.turn import Halt, drive


def test_drive_accumulates_then_halts() -> None:
    # A step that bumps round/cost twice, then halts with the carried state.
    async def step(s: AgentState) -> Any:
        if s.round >= 2:
            return Halt("done", output=s.last)
        s.round += 1
        s.charge(1.0)
        s.last = s.round
        return s

    out = asyncio.run(drive(step, AgentState(last=0), halt=lambda s: None))
    assert out == {"status": "done", "output": 2, "rounds": 2, "cost": 2.0, "trace": []}


def test_drive_pre_round_halt_wins_before_step() -> None:
    async def step(s: AgentState) -> Any:  # must never run
        raise AssertionError("step ran despite pre-round halt")

    out = asyncio.run(
        drive(step, AgentState(last="x"), halt=lambda s: Halt("max_rounds"))
    )
    assert out == {"status": "max_rounds", "output": "x", "rounds": 0, "cost": 0.0, "trace": []}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/invariants/test_turn.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'composable_agents.turn'`

- [ ] **Step 3: Write minimal implementation**

```python
# composable_agents/turn.py
"""The agent loop as an iterated endomorphism on AgentState (design:
docs/design/agent-loop-as-turn.md). Pure: no IO, no Temporal, no IR emitted.

A ``Step`` is one round in the turn category — ``AgentState -> (AgentState |
Halt)``, the operational reading of algebra.hs's ``Flow (a,s) (Either s b)``.
``drive`` iterates a Step to its verdict; ``Op.ITER_UP_TO`` is deliberately NOT
folded in here (its do-while convergence + causal threading would regress — see
the design note).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Optional, Union

from .agent_loop import AgentState, terminal_result


@dataclass(frozen=True)
class Halt:
    """A round's verdict (algebra.hs's ``Right b``). Cost/round/trace accrued on
    the shared AgentState before the Halt survive, because ``drive`` reads that
    same mutated state when it builds the terminal_result."""

    status: str
    output: Any = None
    reason: Optional[str] = None


StepResult = Union[AgentState, Halt]
Step = Callable[[AgentState], Awaitable[StepResult]]
Halter = Callable[[AgentState], Optional[Halt]]
Finalize = Callable[[dict[str, Any]], dict[str, Any]]


async def drive(
    step: Step,
    state: AgentState,
    *,
    halt: Halter,
    finalize: Optional[Finalize] = None,
) -> dict[str, Any]:
    """Iterate ``step`` to its verdict. ``halt`` is the pre-round guard; ``step``
    mutates ``state`` in place and may itself return a Halt. ``finalize``
    post-processes the terminal dict (used for DEV-mode prodGap)."""

    def done(h: Halt) -> dict[str, Any]:
        result = terminal_result(h.status, state, output=h.output, reason=h.reason)
        return finalize(result) if finalize is not None else result

    while True:
        pre = halt(state)
        if pre is not None:
            return done(pre)
        result = await step(state)
        if isinstance(result, Halt):
            return done(result)
        state = result


__all__ = ["Halt", "StepResult", "Step", "Halter", "Finalize", "drive"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/invariants/test_turn.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add composable_agents/turn.py tests/invariants/test_turn.py
git commit -m "feat(turn): drive combinator + Halt for the agent round category"
```

---

### Task 2: `controller_turn`, `pre_round`, `make_finalize` (the extracted body)

**Files:**
- Modify: `composable_agents/turn.py`
- Test: `tests/invariants/test_turn.py`

The body is lifted verbatim from `agent_loop.py:441–518`. Faithfulness points: think-cost is charged *before* the terminal check (`agent_loop.py:453`); per-action budget is checked *after* the controller picks an action (`agent_loop.py:463`); DEV mode warns-but-allows a denial and still increments the maxCalls counter (`agent_loop.py:478–483`); `prodGap` rides on every terminal result when non-empty.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/invariants/test_turn.py
from composable_agents.agent_loop import AgentConfig, Decision
from composable_agents.kinds import EnforcementMode
from composable_agents.turn import controller_turn, pre_round, make_finalize


def test_controller_turn_call_round_records_trace() -> None:
    async def invoke_controller(_p):  # one CALL round
        return {"tool": "calc/add", "input": 5}

    async def call_tool(tool, value):
        assert (tool, value) == ("calc/add", 5)
        return value * 2

    step = controller_turn(
        cfg=AgentConfig(), invoke_controller=invoke_controller, call_tool=call_tool,
        run_subflow=None, granted=None, granted_subflows=None, contracts=None,
        mode=EnforcementMode.STRICT, prod_gap=[],
    )
    s = AgentState(last=1)
    out = asyncio.run(step(s))
    assert out is s and s.round == 1 and s.last == 10
    assert s.spent == 3.0  # think_cost(2.0) + DEFAULT_TOOL_COST(1.0)
    assert [t.to_json() for t in s.trace] == [{"decision": "call", "cost": 1.0, "ref": "calc/add"}]


def test_controller_turn_finish_returns_halt() -> None:
    async def invoke_controller(_p):
        return {"output": "ok"}

    step = controller_turn(
        cfg=AgentConfig(), invoke_controller=invoke_controller, call_tool=None,
        run_subflow=None, granted=None, granted_subflows=None, contracts=None,
        mode=EnforcementMode.STRICT, prod_gap=[],
    )
    out = asyncio.run(step(AgentState(last="q")))
    assert isinstance(out, Halt) and out.status == "done" and out.output == "ok"


def test_pre_round_max_rounds_and_budget() -> None:
    from composable_agents.capabilities import Budget
    over = pre_round(AgentConfig(max_rounds=1))
    s = AgentState(); s.round = 1
    assert isinstance(over(s), Halt) and over(s).status == "max_rounds"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/invariants/test_turn.py -v`
Expected: FAIL with `ImportError: cannot import name 'controller_turn'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to composable_agents/turn.py
from .agent_loop import (
    CallDenial, TraceEntry, action_cost, authorize_call, authorize_subflow,
    charge_tool_call, interpret_brain_reply, would_exceed_budget,
)
from .kinds import EnforcementMode


def pre_round(cfg) -> Halter:
    """Pre-round guards from agent_loop.py:442–449: max_rounds, then think-cost
    budget (precheck_controller). Returns a Halt or None."""
    def halt(state: AgentState) -> Optional[Halt]:
        if state.round >= cfg.max_rounds:
            return Halt("max_rounds")
        if would_exceed_budget(state, cfg.think_cost, cfg.budget):
            return Halt("over_budget")
        return None
    return halt


def make_finalize(prod_gap: list[str]) -> Finalize:
    """DEV-mode prodGap rides on every terminal result when non-empty
    (agent_loop.py:426–428, 447–449)."""
    def finalize(result: dict[str, Any]) -> dict[str, Any]:
        if prod_gap:
            result["prodGap"] = list(prod_gap)
        return result
    return finalize


def controller_turn(
    *, cfg, invoke_controller, call_tool, run_subflow, granted, granted_subflows,
    contracts, mode: EnforcementMode, prod_gap: list[str],
) -> Step:
    """One agent round, lifted verbatim from drive_agent_loop's while-body."""
    mode = EnforcementMode.coerce(mode)
    unconstrained = granted is None
    granted_set = set(granted or [])

    def denial_to_halt(denial: Optional[CallDenial]) -> Optional[Halt]:
        # STRICT: denial halts; DEV: warn-but-allow (record prodGap, proceed).
        if denial is None:
            return None
        if mode is EnforcementMode.DEV:
            prod_gap.append(denial.reason)
            return None
        return Halt("denied", reason=denial.reason)

    async def step(state: AgentState) -> StepResult:
        payload = {"input": state.last, "trace": [t.to_json() for t in state.trace]}
        reply = await invoke_controller(payload)
        state.charge(cfg.think_cost)
        action = interpret_brain_reply(reply, strict=not cfg.permissive_controller)

        if action.decision.value == "finish":
            return Halt("done", output=action.payload)
        if action.decision.value == "escalate":
            return Halt("escalated", reason=str(action.payload))
        if action.decision.value == "controller_error":
            return Halt("controller_error", reason=str(action.payload))

        cost = action_cost(action)
        if would_exceed_budget(state, cost, cfg.budget):
            return Halt("over_budget")

        if action.decision.value == "call":
            tool = action.payload["tool"]
            halt = denial_to_halt(authorize_call(
                tool, unconstrained=unconstrained, granted_set=granted_set,
                contracts=contracts))
            if halt is not None:
                return halt
            denial = charge_tool_call(state, tool, contracts)
            halt = denial_to_halt(denial)
            if halt is not None:
                return halt
            if denial is not None:  # DEV warn-but-allow: still count the call
                state.call_counts[tool] = state.call_counts.get(tool, 0) + 1
            call_input = action.payload.get("input")
            if call_input is None:
                call_input = state.last
            out = await call_tool(tool, call_input)
            state.charge(cost)
            state.last = out
            state.record(TraceEntry(decision="call", ref=tool, cost=cost))
        else:  # sub
            ref = action.payload["ref"]
            halt = denial_to_halt(authorize_subflow(ref, granted_subflows=granted_subflows))
            if halt is not None:
                return halt
            if run_subflow is None:
                return Halt("denied", reason=f"no subflow runner for {ref!r}")
            sub_input = action.payload.get("input")
            if sub_input is None:
                sub_input = state.last
            out = await run_subflow(ref, sub_input)
            state.charge(cost)
            state.last = out
            state.record(TraceEntry(decision="sub", ref=ref, shape=action.payload.get("shape"), cost=cost))

        state.round += 1
        return state

    return step
```

Then extend `__all__`: `["Halt", "StepResult", "Step", "Halter", "Finalize", "drive", "controller_turn", "pre_round", "make_finalize"]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/invariants/test_turn.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add composable_agents/turn.py tests/invariants/test_turn.py
git commit -m "feat(turn): controller_turn + pre_round extracted from drive_agent_loop"
```

---

### Task 3: Refactor `drive_agent_loop` to delegate to `drive` (parity gate)

**Files:**
- Modify: `composable_agents/agent_loop.py:407–518`
- Test (parity, must pass UNCHANGED): `tests/invariants/test_local_agent_loop.py`, `tests/invariants/test_dev_mode_runtime.py`, `tests/test_cma.py`

- [ ] **Step 1: Confirm the parity baseline is green before touching anything**

Run: `pytest tests/invariants/test_local_agent_loop.py tests/invariants/test_dev_mode_runtime.py tests/test_cma.py -v`
Expected: PASS (all). These dicts are the byte-for-byte contract the refactor must preserve.

- [ ] **Step 2: Replace the `while True` body with a `drive` call**

Replace the body of `drive_agent_loop` (everything from `mode = EnforcementMode.coerce(cfg.mode)` at `agent_loop.py:420` through the end of the `while True` loop at `:518`) with:

```python
    from .turn import controller_turn, drive, make_finalize, pre_round

    mode = EnforcementMode.coerce(cfg.mode)
    prod_gap: list[str] = []
    state = state or AgentState(last=input)
    step = controller_turn(
        cfg=cfg, invoke_controller=invoke_controller, call_tool=call_tool,
        run_subflow=run_subflow, granted=granted, granted_subflows=granted_subflows,
        contracts=contracts, mode=mode, prod_gap=prod_gap,
    )
    return await drive(step, state, halt=pre_round(cfg), finalize=make_finalize(prod_gap))
```

Keep the function signature, docstring, and `__all__` entry for `drive_agent_loop` unchanged. (The import is function-local to avoid a module import cycle: `turn` imports from `agent_loop`.)

- [ ] **Step 3: Run the parity suite**

Run: `pytest tests/invariants/test_local_agent_loop.py tests/invariants/test_dev_mode_runtime.py tests/test_cma.py -v`
Expected: PASS, identical to Step 1. If any terminal_result dict differs, the extraction is not faithful — diff against `agent_loop.py:441–518` (most likely the DEV warn-but-allow counter or the think-cost ordering).

- [ ] **Step 4: Guard the rest of the suite (no IR moved)**

Run: `pytest tests/golden/test_golden.py -q && pytest -q`
Expected: PASS. The refactor emits no IR, so golden hashes must be unchanged.

- [ ] **Step 5: Commit**

```bash
git add composable_agents/agent_loop.py
git commit -m "refactor(agent_loop): drive_agent_loop delegates to turn.drive (parity-preserved)"
```

---

### Task 4: `Step -> Step` decorators (the payoff)

**Files:**
- Modify: `composable_agents/turn.py`
- Test: `tests/invariants/test_turn.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/invariants/test_turn.py
from composable_agents.turn import with_retry


def test_with_retry_reissues_a_transient_round() -> None:
    calls = {"n": 0}

    async def flaky(s: AgentState) -> Any:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return Halt("done", output="ok")

    out = asyncio.run(drive(with_retry(flaky, attempts=3), AgentState(), halt=lambda s: None))
    assert out["status"] == "done" and calls["n"] == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/invariants/test_turn.py::test_with_retry_reissues_a_transient_round -v`
Expected: FAIL with `ImportError: cannot import name 'with_retry'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to composable_agents/turn.py
def with_retry(step: Step, *, attempts: int) -> Step:
    """Reissue a round that raises, up to ``attempts`` times. The Step must be
    safe to retry (no half-applied effect); use only on idempotent rounds."""
    async def wrapped(state: AgentState) -> StepResult:
        last_exc: Optional[BaseException] = None
        for _ in range(attempts):
            try:
                return await step(state)
            except Exception as exc:  # noqa: BLE001 — re-raised after attempts
                last_exc = exc
        raise last_exc  # type: ignore[misc]
    return wrapped
```

Add `"with_retry"` to `__all__`. (`with_guard` / `with_trace` follow the same `Step -> Step` shape; add them when a caller needs them — YAGNI for now.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/invariants/test_turn.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add composable_agents/turn.py tests/invariants/test_turn.py
git commit -m "feat(turn): with_retry Step decorator"
```

---

### Task 5: Full-suite verification

- [ ] **Step 1: Run the whole suite**

Run: `pytest -q`
Expected: PASS (no regressions; golden corpus unchanged).

- [ ] **Step 2: Confirm the public surface is intact**

Run: `python -c "from composable_agents.agent_loop import drive_agent_loop; from composable_agents.turn import drive, controller_turn, Halt; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit (if any fixups were needed)**

```bash
git add -A && git commit -m "test: full-suite green for agent-loop-as-turn" || echo "nothing to commit"
```

---

## Self-Review

- **Spec coverage:** `drive`/`Step`/`Halt` (Task 1), `controller_turn`/`pre_round`/`make_finalize` with the budget split + think-cost-before-terminal + DEV warn-but-allow (Task 2), `Op.ITER_UP_TO` untouched and `continue_as_new` out of the loop (Tasks 3–4 touch only `agent_loop.py`/`turn.py`), `Step -> Step` decorators (Task 4), parity gate (Task 3). Covered.
- **Placeholders:** none — every code step shows complete code; commands are exact pytest invocations.
- **Type consistency:** `Step`/`Halt`/`StepResult`/`Halter`/`Finalize` defined in Task 1 and reused unchanged; `controller_turn`/`pre_round`/`make_finalize` signatures match their Task-3 call site.
