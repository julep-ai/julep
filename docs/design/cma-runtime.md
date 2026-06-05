# Design note: Claude Managed Agents as a runtime

**Status: as-built (v1, experimental).** This started as a design exploration of
whether Anthropic's hosted *Claude Managed Agents* (CMA) runtime can sit
alongside the in-memory and Temporal runtimes. It concluded — and the
implementation confirms — that CMA is a *competing control plane*, so the only
honest "third runtime" framing is a CMA backend for the `app` node: driving the
agent loop's controller while the framework stays the capability and budget
authority. **Framing 4 is now implemented** (see *What shipped* below). It
references [SPEC.md](../SPEC.md), [concepts.md](../concepts.md), and
[deploy-temporal.md](../deploy-temporal.md).

## What shipped

A third `run_agent` backend, built as a control-flow inversion of the local
`drive_agent_loop` and proven equivalent to it by a parity test
(`assert cma == local` over the same scenario):

- **`composable_agents/execution/cma.py`** (pure; no `temporalio`/`anthropic`/
  `httpx` import):
  - `CMAEvent` / `CMASession` / `CMAClient` — a normalized event surface. The
    CMA-specific correlation (`agent.custom_tool_use` → `session.status_idle`
    with `stop_reason.type == "requires_action"` and `stop_reason.event_ids` →
    `user.custom_tool_result`; `end_turn`; `session.error`) is the adapter's job,
    so the driver sees only `custom_tool_use` / `terminal` / `error`.
  - `drive_cma_agent_loop(...)` — the hosted model drives; this loop is the
    capability gateway + accountant, routing every tool call through the **same**
    helpers as the other two backends (`authorize_call`, `charge_tool_call`,
    `would_exceed_budget`/`action_cost`, `contract_for_tool`, `AgentState`,
    `TraceEntry`, `terminal_result`). STRICT/DEV mode parity; per-call
    idempotency cids (`{session_cid}-call-{round}`); a losing race branch (or any
    early return/exception) terminates the session via `finally: cancel()`.
  - `manifest_to_custom_tools(...)` — manifest-only projection; never the built-in
    `agent_toolset_20260401` (SPEC §7 deny-by-default).
  - `CMAAgentEnv` — wraps an inner `Env`, overrides only `run_agent`.
- **`Agent.run_on_cma(...)` / `arun_on_cma(...)`** (`agent.py`) — a third run
  surface beside `.run()` (local) and `.deploy()` (Temporal), reusing the
  facade's existing grants/contracts/budget/manifest.
- **`composable_agents/execution/cma_anthropic.py`** — an *experimental* HTTP
  client (`AnthropicCMAClient`) for the documented managed-agents beta
  (`anthropic-beta: managed-agents-2026-04-01`), behind the optional `cma` extra.
  The installed `anthropic` SDK (0.79.0) does not yet expose managed agents, so
  it targets the documented HTTP endpoints directly via `httpx`. It is **not**
  verified against a live CMA endpoint — only against unit tests and
  `httpx.MockTransport`. Swap the transport for SDK-typed calls once a new enough
  SDK ships.

The golden corpus did not move: this is all execution-layer code that emits no
new IR. See *Status of the open obligations* below for what is and isn't solved.

## What CMA is

Anthropic ships two separate things; only one is a runtime.

- **Claude Agent SDK** — the Claude Code agent loop as an in-process library.
  You own the loop; durability is your problem. This is a way to *write* a
  controller, not a runtime to host one.
- **Claude Managed Agents** (beta since 2026-04, header
  `managed-agents-2026-04-01`) — a *hosted* runtime. Anthropic owns the harness,
  the sandbox, and a **durable, resumable, server-side session log**. The caller
  defines an *agent* (model + prompt + tools + MCP servers + skills) and an
  *environment* (cloud or self-hosted sandbox), starts a *session*, and
  exchanges *events* over SSE. Sessions survive harness/container/network
  failures and persist conversation history, sandbox state, and outputs.

CMA's value proposition — *durable, long-running, autonomous agent execution* —
overlaps directly with the Temporal layer. That overlap is what makes "can CMA
be a runtime here?" a real question rather than a trivial one.

## The core tension: CMA owns the loop; this framework owns the loop

The north star ([SPEC §1](../SPEC.md#1-north-star)) is a *frozen, typed,
capability-bounded IR tree whose dynamic escape hatches can only choose
structure over already-authorized effects*. The **deterministic interpreter**
owns ordering and continuation; the model only chooses a branch or a bounded
plan inside an already-frozen tool surface; durability is **replay of the IR
program** against pinned pure hashes and an artifact hash
([SPEC §6](../SPEC.md#6-freeze--replay-integrity)).

CMA inverts every clause. The *model* owns control flow, tools are called (and
can be discovered) dynamically, and durability is "the session event log
survives crashes" — replay of a *model-driven session*, not of a typed frozen
program. **CMA is not an effect substrate the interpreter sits on top of; it is
a competing control plane.** That single fact decides where it can and cannot
plug in.

## Four framings, very different feasibility

### 1. As a Brain — trivially possible, pointless

A CMA session could back the `(brain, payload) -> reply` controller callable.
But that pays for CMA's loop, sandbox, and durability only to use it as one
expensive single-shot model call. It is not a runtime in any meaningful sense.

### 2. As a Hand / Sub — clean, recommended today

From the framework's perspective a CMA session is an *opaque external effect
that returns a value* — indistinguishable from an MCP tool or an HTTP hand.
Wrap "run a managed-agent session to do X, wait for its terminal result" as a
`@tool(effect="external")` or as a `sub`. A `sub` then genuinely *is* surface-
opaque — the **Sub one-way mirror** ([SPEC §2 invariant 5](../SPEC.md#2-invariants-normative)):
its surface shape is `Pipeline`, its internal shape never leaks into the parent
projection, and its closed shape charges the parent the sub's declared contract.
Capability checks for a `sub` ref are enforced at compile time. Note two honest
limits: approval gating is *tool-call*-specific ([SPEC §7.3](../SPEC.md#73-approval-gating-new--required)),
so wrapping CMA as a `sub` does not by itself impose an approval gate; and there
is no pre-execution runtime budget guard on the `sub` path the way there is
inside the agent loop. **This is the way to use CMA inside a flow today.**

### 3. As a peer control-plane runtime replacing Temporal — no

You cannot run the deterministic interpreter *on top of* CMA, because CMA wants
to drive, not to dispatch. Doing so would forfeit compile-time capability
enforcement, the shape lattice, race admission, frozen-manifest binding, and
frozen-IR replay integrity. CMA's session durability is not the IR replay
contract; the two are not substitutable.

### 4. As a backend for the `app` node — the principled "third runtime"

There is exactly one node whose semantics *are* an open-ended controller loop
with a closed action vocabulary and a budget guard: `Op.APP`, produced by `app`
([SPEC §10](../SPEC.md#10-agent-loop)). It is `Shape.AGENT` — the **top** of the
lattice (`shapes.py`), and explicitly *not* surface-opaque the way a `SubStep`
is. The opacity that makes a CMA backend tractable is not the Sub mirror; it is
the **`run_agent` effect boundary**: the parent flow observes only the `app`
node's terminal value, and the loop's internal rounds are not part of the parent
continuation. In Temporal that boundary is realized as the agent running in its
own child workflow, so `continue_as_new` truncates only the loop's history.

`run_agent` is a single injectable seam —
`Env.run_agent(controller, value, cid, app_config)` — with two existing
backends:

- **local** — `InMemoryEnv.run_agent` (`execution/interpreter.py`) looks up the
  registered agent callable and invokes it (await-aware). The facade registers
  the pure `drive_agent_loop(...)` (`agent_loop.py`) for that controller via the
  `agents={...}` map in `agent.py`; the pure loop is a *facade-level local
  registration*, not intrinsic to `InMemoryEnv`.
- **Temporal** — `Env.run_agent` (`execution/harness.py`) spawns a child
  `AgentWorkflow`.

A `CMAAgentEnv.run_agent(...)` would be a **third implementation of that one
method** — a true peer of the Temporal backend: same seam, same gating helpers,
same terminal-result shape; only the *driver of the loop* differs (CMA emits the
next action instead of `invoke_controller`).

## What an honest CMA `app` backend must do

Staying capability-authoritative is **necessary but not sufficient**. The real
`app` contract ([SPEC §10](../SPEC.md#10-agent-loop)) also requires budget
prechecks, a strict controller vocabulary, state carry-forward, retry/idempotency
shaping, human-gate behavior, and continue-as-new/state durability. Concretely:

1. **Tool surface = the frozen manifest, nothing more.** Define the granted
   manifest entries as CMA **custom tools** (the better fit than MCP tunnels:
   custom tools pause the session while *your* code executes the operation and
   returns the result, which is exactly where local contract checks belong). Do
   **not** include CMA's built-in `agent_toolset_20260401`, or set its
   `default_config.enabled: false` and enable nothing — otherwise CMA's
   bash/file/web tools blow the capability envelope
   ([SPEC §7](../SPEC.md#7-capabilities-deny-by-default)). MCP-server grants in
   the manifest can additionally use MCP tunnels (research preview).
2. **Route every tool call through the existing gating path.** On each
   `agent.custom_tool_use` event, run the same helpers the loop uses:
   `authorize_call(tool, unconstrained=..., granted_set=..., contracts=...)`
   covers grant membership and approval-required refusal;
   `charge_tool_call(state, tool, contracts)` enforces `maxCalls` and **returns a
   denial that must be checked**. Budget is a *separate* check —
   `would_exceed_budget(state, action_cost(...), cfg.budget)` — and idempotency
   affects *retry shaping* via the frozen `ToolContract`, not those two helpers.
   A denial maps to a `user.custom_tool_result` error (or an `ESCALATE`).
3. **Preserve the run_agent boundary and terminal shape.** Carry an `AgentState`
   (`round`, `spent_usd`, `last`, `trace`, `call_counts`) across events and
   return `terminal_result(status, state, output=...)` so local, Temporal, and
   CMA `app` nodes are indistinguishable upstream. The CMA session log is the
   durability substrate for that subtree alone — consistent with the parent's
   "history is the source of truth" invariant ([SPEC §2 invariant 6](../SPEC.md#2-invariants-normative)),
   since the parent only records "started CMA session `<id>`, received terminal
   value."

### The driver (as built)

The real loop lives in `drive_cma_agent_loop` and is driven by `CMAAgentEnv`'s
`run_agent`. Condensed (the committed code carries the full STRICT/DEV branching
and accounting):

```python
async def drive_cma_agent_loop(*, input, cfg, session, call_tool,
                               granted=None, contracts=None, state=None,
                               session_cid="cma"):
    state = state or AgentState(last=input)
    unconstrained = granted is None
    granted_set = set(granted or [])
    try:
        async for ev in session.events():
            if ev.is_error:
                return finish("controller_error", reason=ev.reason)
            if ev.is_terminal:
                state.charge(cfg.think_cost)
                return finish("done", output=ev.output)
            # ev.is_custom_tool_use — the model chose a tool this round:
            if state.round >= cfg.max_rounds:    return finish("max_rounds")
            if precheck_controller(state, cfg):  return ...           # think budget
            state.charge(cfg.think_cost)
            cost = action_cost(RoundAction(Decision.CALL, {"tool": ev.tool, "input": ev.input}))
            if would_exceed_budget(state, cost, cfg.budget): return finish("over_budget")
            # grant + approval, then maxCalls — STRICT denial => tool_error + finish("denied");
            # DEV denial => record prodGap and proceed (warn-but-allow), exactly as the local loop:
            if (d := authorize_call(ev.tool, unconstrained=unconstrained,
                                    granted_set=granted_set, contracts=contracts)):
                ... # STRICT: await session.tool_error(ev.call_id, d.reason); return finish("denied", d.reason)
            if (d := charge_tool_call(state, ev.tool, contracts)):
                ... # same STRICT/DEV handling
            out = await call_tool(ev.tool, ev.input, f"{session_cid}-call-{state.round}")
            state.charge(cost); state.last = out
            state.record(TraceEntry(decision="call", ref=ev.tool, cost=cost))
            state.round += 1
            await session.tool_result(ev.call_id, out)
        return finish("controller_error", reason="session ended without terminal output")
    finally:
        await session.cancel()   # terminate a losing-race / abandoned session
```

`CMAAgentEnv.run_agent` resolves the loop policy (with `app_config` budget/
maxRounds overrides), builds the manifest-only custom-tool surface, calls
`client.create_session(agent=..., environment=..., session_cid=cid, input=value)`,
and hands a `call_tool` closure (name → bound hand) to the driver. The returned
`terminal_result(...)` is byte-identical to the local/Temporal backends for the
same scenario — the parity test asserts exactly that.

## Status of the open obligations

What the v1 implementation settles, and what is deliberately deferred:

- **Per-tool-call idempotency keys — addressed.** Each call gets a deterministic
  `{session_cid}-call-{round}` cid, mirroring the Temporal `callHand` discipline
  ([SPEC §8.5](../SPEC.md#85-idempotency-keys)). (There is no documented
  session-create idempotency key in the CMA HTTP API, so session-create dedup on
  replay remains the adapter's concern — e.g. reusing a known session id.)
- **Cancellation — addressed; race admission — inherited.** The driver always
  terminates the session in a `finally` (`cancel()` → `user.interrupt`), so a
  losing `race`/`hedge`/`quorum` branch or any early return stops producing side
  effects ([SPEC §8.3](../SPEC.md#83-racehedgequorum)). The existing IR-level race
  admission rules for `app` apply unchanged (this is a `run_agent` backend, not a
  new node).
- **Budget — framework-authoritative; CMA usage is observability.** The same
  pre-action `AgentState.spent_usd` guard runs as in the local/Temporal loops, so
  the run stops before overspend by the framework's cost model. CMA's cumulative
  token `usage` is carried through `CMAEvent.usage` for observability but is **not
  yet** reconciled into the USD budget as the authority. A token/session-hour →
  USD cost model and post-idle usage reconciliation are deferred.
- **Human gates — partial.** Approval-required tools still force the loop to stop
  (a denial → STRICT `denied`/`tool_error`), so they cannot be silently called
  ([SPEC §7.3](../SPEC.md#73-approval-gating-new--required)). Mapping a durable
  `human_gate(...)` signal/wait ([SPEC §8.6](../SPEC.md#86-human-gate)) onto CMA's
  `user.tool_confirmation` permission flow *inside* the CMA loop is deferred;
  `human_gate` remains a framework-level node outside the CMA subtree.
- **Observability / projection — addressed for parity.** The driver returns a
  real `terminal_result` with an `AgentState.trace` of `TraceEntry` per call, so
  the parent projection records cost/status/trace exactly as it does for the local
  backend. The trace matches local-loop richness; richer content-addressed refs
  per [SPEC §10.1](../SPEC.md#101-trace-richness) (and a CMA-session-id projection
  attribute) are a follow-on.
- **Deferred surface.** v1 projects tool calls only — `sub`-flow controller
  decisions are not exposed as CMA custom tools yet. A **Temporal-side** CMA
  backend (running a CMA session from an activity, rather than the local-env
  driver) is also future work; today CMA execution rides the in-memory `Env`
  while the parent flow may still be local or Temporal.
- **Not verified against live CMA.** The HTTP adapter is exercised only by unit
  tests + `httpx.MockTransport`; it has never talked to a real session.

## Caveats

- CMA is beta and version-pinned (`managed-agents-2026-04-01`); a backend is
  beta-coupled. **Custom tools** are available in the beta; **MCP tunnels** are
  research preview.
- CMA's **built-in toolset is enabled by default** when included — a
  manifest-only surface requires omitting it (or `default_config.enabled:
  false`). Custom tools **pause the session** until your app returns a result.
- Session usage is **cumulative and must be fetched** from session state;
  checkpoints are retained for a limited window (≈30 days after last activity).
- CMA retains conversation/sandbox state server-side and is **not eligible for
  Zero Data Retention or HIPAA BAA** — material to the safety story in
  [capabilities-and-safety.md](../capabilities-and-safety.md).
- Pricing is per session-hour plus tokens, unlike the self-hosted Temporal path.

## Bottom line

Use CMA as a *tool / sub* today (framing 2): clean, immediate, with the Sub
mirror doing real work. Do **not** treat it as a drop-in for the Temporal
runtime (framing 3): it is a competing control plane, not an `Env`. The only
principled "third runtime" is framing 4 — **a CMA backend for the `app` node**,
a third implementation of the `run_agent` seam, with the capability manifest
projected as CMA custom tools and every call routed through the existing gating
helpers. **That is what shipped** (`CMAAgentEnv` / `drive_cma_agent_loop` /
`Agent.run_on_cma`, with an experimental `AnthropicCMAClient` behind the `cma`
extra): it buys CMA's durability without surrendering the invariants the
framework exists to enforce, with the budget guard, cancellation, idempotency
cids, and trace already in place. The deferred items above (CMA-usage→USD budget
reconciliation, human gates inside the CMA loop, a Temporal-side backend, richer
trace refs, and — above all — verification against a live CMA endpoint) are what
stand between this v1 and production use.
