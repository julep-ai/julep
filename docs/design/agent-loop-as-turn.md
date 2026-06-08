# Design note: the agent loop as an iterated turn

**Status: proposed (design).** Reify the agent-loop *round body* — currently the
un-named inside of `drive_agent_loop`'s `while True` — as a first-class
endomorphism on `AgentState`, driven by a thin `drive` combinator. This is an
**execution-layer refactor of the agent loop only**: no new IR, no wire change,
`Op.APP`'s `run_agent` boundary intact, and **`Op.ITER_UP_TO` is left exactly as
it is** (see *Why not unify the two loops*). It references [SPEC.md](../SPEC.md)
(§10 agent loop, §4.1 shape lattice, §6 freeze/replay), [algebra.hs](./algebra.hs)
(the formal model), and [cma-runtime.md](./cma-runtime.md) (the third `run_agent`
backend, which this refactor should stay compatible with).

## Motivation — the round body is trapped in a `while True`

`drive_agent_loop` (`agent_loop.py:441–518`) is a `while True:` whose body does
one round: build `payload = {"input": state.last, "trace": [...]}`,
`invoke_controller`, `interpret_brain_reply`, dispatch one bounded `CALL`/`SUB`,
charge, record a `TraceEntry`, `round += 1`. The body is not a value, so it can't
be named, wrapped, or unit-tested in isolation. Everything we'd want to do to a
round — retry it, guard it, trace it, test it without a controller server — is
out of reach because it lives inside the loop keyword.

`algebra.hs` already names the body: it's `Flow (a, s) (Either s b)` — take the
input plus loop-carried state `s`, return `Either s b` (*continue with new `s`*,
or *finish with output `b`*). That `Either s b` is exactly the terminal verdict
the agent loop computes ad hoc today. We make the Python say so — **for the agent
loop**. (The formal model treats `IterUpTo` and `App` as the *same* iteration
shape; in the code they are not interchangeable drivers, and forcing them into
one would regress behavior — that's the next section.)

## The model — the turn category, one driver

Keep the two categories `algebra.hs` separates:

- **The value category** — `Flow[In, Out]`, morphisms over business values
  (`flow.py`). The authoring layer over the frozen `Node` IR. Untouched.
- **The turn category** — endomorphisms on `AgentState` (the Writer-state:
  `last` + the `trace` pomset + `spent` + `call_counts`). The agent loop lives
  here.

A **Step** is one round in the turn category — `algebra.hs`'s `Flow (a,s) (Either
s b)` specialized to `AgentState`:

```python
@dataclass(frozen=True)
class Halt:                     # the algebra's `Right b`: the loop's verdict
    status: str                 # "done" | "escalated" | "controller_error" | "denied" | "over_budget"
    output: Any = None
    reason: Optional[str] = None

# Step :: AgentState -> F[Continue | Halt], where Continue is the mutated AgentState (the algebra's `Left s`).
StepResult = Union[AgentState, Halt]
Step = Callable[[AgentState], Awaitable[StepResult]]

async def drive(step: Step, state: AgentState, *, halt: Callable[[AgentState], Optional[Halt]]) -> dict:
    """Iterate a round to its verdict. `halt` is the pre-round guard; `step`
    mutates `state` in place and may itself return a Halt. Cost/round/trace
    accrued before a Halt survive, because terminal_result reads the *same*
    mutated `state` object."""
    while True:
        pre = halt(state)
        if pre is not None:
            return terminal_result(pre.status, state, output=pre.output, reason=pre.reason)
        result = await step(state)
        if isinstance(result, Halt):
            return terminal_result(result.status, state, output=result.output, reason=result.reason)
        state = result          # same object; the assignment is cosmetic
```

The agent round body, lifted verbatim out of the `while`:

```python
def controller_turn(*, cfg, invoke_controller, call_tool, run_subflow, grants) -> Step:
    async def step(s: AgentState) -> StepResult:
        payload = {"input": s.last, "trace": [t.to_json() for t in s.trace]}
        reply   = await invoke_controller(payload)
        s.charge(cfg.think_cost)                       # charged BEFORE the terminal check, as today (agent_loop.py:453)
        action  = interpret_brain_reply(reply, strict=not cfg.permissive_controller)
        if action.decision is Decision.FINISH:           return Halt("done", output=action.payload)
        if action.decision is Decision.ESCALATE:         return Halt("escalated", reason=str(action.payload))
        if action.decision is Decision.CONTROLLER_ERROR: return Halt("controller_error", reason=str(action.payload))
        # per-action budget check (depends on the chosen action), then the
        # existing CALL / SUB dispatch — grants, approval, maxCalls, call_tool/
        # run_subflow, s.last update, s.record(TraceEntry(...)), s.round += 1 —
        # all verbatim from agent_loop.py:463–518. A denial returns Halt("denied", ...).
        return s
    return step

# drive_agent_loop collapses to:
return await drive(controller_turn(...), state or AgentState(last=input), halt=pre_round(cfg))
```

`pre_round(cfg)` is the existing **pre-round** guards as a function: `state.round
>= cfg.max_rounds` → `Halt("max_rounds")`, and `precheck_controller` (the
**think-cost** budget check) → `Halt("over_budget")`. That's all the top of the
`while` did (`agent_loop.py:442–449`). The **per-action** budget check —
`would_exceed_budget(state, action_cost(action), cfg.budget)` — stays **inside**
the step after the controller picks an action (`agent_loop.py:463–465`), because
it depends on which action was chosen.

**`continue_as_new` is not in here.** It is a Temporal-harness concern
(`execution/harness.py`), checked *after* a completed action carries state
forward — it is **not** a terminal result and the pure `drive_agent_loop` never
calls `should_continue_as_new` today. The refactor keeps it that way: `drive`
returns only real `terminal_result`s; the durable harness wraps the agent in a
child workflow and owns continue-as-new exactly as before.

### Why not unify the two loops (the codex finding, kept honest)

It is tempting to make `Op.ITER_UP_TO` (`interpreter.py:196–207`) share `drive`,
since `algebra.hs` models both as `Flow (a,s) (Either s b)`. **Don't** — a naive
shared driver regresses two observable behaviors:

1. **Do-while vs while.** `iter_up_to` checks convergence *after* the body runs at
   least once (`interpreter.py:201,205`). A pre-round `halt` would check before
   the first body run: a seed that already satisfies `conv` runs the body **once**
   today, **zero** times under a pre-round halt. That moves the golden corpus.
2. **Causality threading.** `iter_up_to` threads `causes=(last_event,)` into each
   iteration (`interpreter.py:200,202,204`) — the pomset causality of
   `algebra.hs`. A generic `body_turn` that calls `interpret(body, s.last, env)`
   drops it, moving projection output.

So `Op.ITER_UP_TO` is **untouched**. The `algebra.hs` "one iteration shape" is a
conceptual truth; it does not buy a shared Python driver, and pretending it does
would trade real behavior for tidiness. We extract the agent body only.

### What this respects (non-negotiable)

- **No new IR, no new recursion primitive** (`algebra.hs` law 6). `drive`/`Step`
  are the interpreter realization of the existing `Op.APP` node. The frozen tree,
  golden hashes, and cross-language corpus do not move — execution-layer code that
  emits no IR, like the CMA backend ([cma-runtime.md](./cma-runtime.md)).
- **The closed *decision vocabulary* holds.** A `Step` dispatches exactly one of
  the closed `Decision` enum outcomes (`agent_loop.py:49`) and **cannot emit
  fresh IR** — it is `AgentState → AgentState`, never `AgentState → Flow`
  (`agent_loop.py:7–12`). (Orthogonal to grants: `granted is None` /
  `granted_subflows is None` still mean *unconstrained tools / any subflow* —
  the *vocabulary* is closed even when the *grant set* is open. The invariant the
  refactor preserves is "no fresh IR", not "a finite tool set".)
- **The `run_agent` boundary is unchanged.** `Op.APP` still delegates to
  `env.run_agent` (`interpreter.py:218`); only the *local* `drive_agent_loop`
  body is refactored. Temporal and CMA backends untouched.
- **The lattice is not collapsed.** Feedback stays strictly below Agent
  ([SPEC §4.1](../SPEC.md#41-shape-lattice)); we add no shared node.

### The payoff — rounds become decoratable

Once the round is a value, it takes `Step → Step` decorators — impossible while
it's trapped in `while True`:

```python
def with_retry(step: Step, *, attempts: int) -> Step: ...   # retry a transient round
def with_guard(step: Step, *, policy)      -> Step: ...      # extra per-round policy gate
def with_trace(step: Step, *, sink)        -> Step: ...      # emit a structured round event

drive(with_guard(with_retry(controller_turn(...), attempts=3), policy), state, halt=pre_round(cfg))
```

And a single round is testable as `await step(AgentState(last=x))` — no Temporal,
no controller server, no loop.

## Invariants preserved (checklist)

- **IR / freeze / golden** — no IR emitted; `to_json`/`from_json` unchanged;
  golden + cross-language hashes must not move. `Op.ITER_UP_TO` untouched, so its
  corpus is trivially stable.
- **Closed decision vocabulary** — preserved; a `Step` cannot emit IR.
- **`run_agent` boundary** — `Op.APP` still calls `env.run_agent`.
- **Budget guard** — same predicates; pre-round think-cost in `halt`, per-action
  cost in `step`; charges accrue on the shared mutable `state` and survive a Halt.
- **continue_as_new / cancellation / race admission** — unchanged (harness
  concerns; this is not a new node and `drive` returns no pseudo-terminal).
- **Parity** — the refactored `drive_agent_loop` returns a **byte-identical**
  `terminal_result` to today's over the existing scenarios (`assert refactor ==
  original`, the discipline the CMA backend used: `cma == local`).

## Phasing (parity-gated)

1. Introduce `Halt` / `StepResult` / `Step`, `drive`, and `controller_turn`;
   refactor `drive_agent_loop` to `return await drive(...)`. **Assert
   terminal_result byte-identical** over the agent-loop scenarios (done/escalate/
   controller_error/denied/over_budget/max_rounds, STRICT and DEV).
2. Ship `with_retry` / `with_guard` / `with_trace` (`Step → Step`) and a
   single-round unit-test helper — the payoff surface.
3. *(optional, separate decision)* Adopt `drive` in the CMA driver
   (`drive_cma_agent_loop`), whose `step` is "handle one `custom_tool_use` event"
   and whose `halt` is the same pre-round guard — if a shared driver across the
   two `run_agent` backends earns its keep without an event-arg leak.

## Open questions

- **Home.** New `composable_agents/loop.py` (shared by the agent loop and a
  possible future CMA adoption), or fold into `agent_loop.py`?
- **CMA driver shape.** `drive_cma_agent_loop` is event-driven; does one `drive`
  cover both, or does the CMA `step` need an event argument that the local `step`
  doesn't (phase 3 decides — don't pollute the local `Step` type for it)?
- **Typing.** Concrete `Step = Callable[[AgentState], Awaitable[StepResult]]`, or
  `Generic[StateT]` in case a non-`AgentState` round ever appears?

## Non-goals

- Touching `Op.ITER_UP_TO`, its convergence semantics, or its causality threading.
- Putting `continue_as_new` inside the loop (it is and stays a harness concern).
- A new recursion primitive (law 6) or merging Feedback into Agent (the lattice).
- Changing the IR, freeze/replay, or golden/cross-language hashes.
