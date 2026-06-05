# Design note: Claude Managed Agents as a runtime

**Status: proposal / design sketch — not implemented.** This explores whether
Anthropic's hosted *Claude Managed Agents* (CMA) runtime can sit alongside the
in-memory and Temporal runtimes. It concludes that CMA is a *competing control
plane*, so the only honest "third runtime" framing is a CMA backend for the
`app` node — driving the agent loop's controller while the framework stays the
capability and budget authority. It references [SPEC.md](../SPEC.md),
[concepts.md](../concepts.md), and [deploy-temporal.md](../deploy-temporal.md).

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

### Sketch (schematic — real helper signatures)

```python
class CMAAgentEnv(Env):
    async def run_agent(self, controller, value, cid, app_config):
        spec = self._resolve_agent_spec(controller)        # grants + contracts + budget
        state = AgentState(last=value)
        session = await self._cma.create_session(
            agent=self._manifest_as_custom_tools(spec),     # custom tools = manifest, no builtins
            environment=self._environment,
            idempotency_key=cid,                            # dedupe session create on replay
        )
        async for ev in session.events(value):
            if ev.is_custom_tool_use:
                denial = authorize_call(
                    ev.tool,
                    unconstrained=spec.unconstrained,
                    granted_set=spec.granted,
                    contracts=spec.contracts,
                ) or charge_tool_call(state, ev.tool, spec.contracts)
                # budget is a distinct guard; cost estimation is an open problem (below)
                if denial:
                    await session.tool_error(ev, denial.reason)
                    continue
                result = await self._call_hand(ev.tool, ev.input, cid=ev.call_id)
                state.charge_tool(ev.tool)
                await session.tool_result(ev, result)
            elif ev.is_terminal:
                return terminal_result("done", state, output=ev.output)
        return terminal_result("controller_error", state, reason="session ended without output")
```

## Open obligations (unsolved by the sketch)

These are the parts that need real design before this is buildable, not just
wiring:

- **Per-tool-call idempotency keys.** A session-level `idempotency_key` is not
  enough; contracts that require idempotency need a deterministic per-call key
  ([SPEC §8.5](../SPEC.md#85-idempotency-keys)) derived from the event, mirroring
  the `cid` discipline in the Temporal `callHand`.
- **Cancellation and race admission.** `race`/`hedge`/`quorum` cancel losers
  ([SPEC §8.3](../SPEC.md#83-racehedgequorum)). A long-running CMA session used in
  a losing branch must be *interrupted/terminated*, or it keeps producing side
  effects after the parent settles. (Today `app` inside a race is already
  constrained; this backend must honor the same admission rules.)
- **Budget reconciliation.** Framework budget is `AgentState.spent_usd` checked
  *before* each action; CMA reports cumulative token/runtime usage that must be
  *fetched* from session state. The backend needs a policy to estimate or poll
  CMA spend and stop before overspend, plus a cost model converting
  session-hours + tokens into the framework's USD accounting.
- **Human gates.** `human_gate(...)` is a durable signal/wait with an explicit
  timeout output ([SPEC §8.6](../SPEC.md#86-human-gate)). It must map onto CMA's
  permission-policy confirmations / custom-tool pauses, and approval-required
  tools must still force `ESCALATE`.
- **Observability / projection.** If the loop internals are opaque, what
  projection records cost, status, denial, cancellation, and the terminal trace?
  The returned trace must satisfy the trace-richness requirements
  ([SPEC §10.1](../SPEC.md#101-trace-richness)) rather than being fabricated or
  missing content-addressed refs.

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
helpers. That buys CMA's durability without surrendering the invariants the
framework exists to enforce — provided the open obligations above (idempotency
keys, cancellation, budget reconciliation, human gates, projection) are solved.
