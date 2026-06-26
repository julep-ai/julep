---
title: "Agent Transcripts"
description: "The transcript model and how traces are recorded."
---

> Status: design draft 2026-06-10, decided with mem-mcp (option C1 of the
> adoption sketch; the C2 stopgap — caller-side assembly inside the
> `LlmCaller` — is documented at the end and is what the first mem-mcp pilot
> ships on). Builds on `docs/design/agent-loop-as-turn.md` (the reified
> `Step`), `docs/design/durable-session-store.md` (claim-check codec,
> `trace_content_refs`, blob durability contract), and `ContextPolicy`
> (`composable_agents/ir.py`).

## Thesis

The agent loop tools its controller `{input, trace, last}` — the previous
round's result plus a trace of *references*. For plan-then-act controllers
that is enough. For tool-heavy multi-round agents it is not: the model needs
to see its own working history — which tools it called with what arguments
and what came back — or it re-issues calls, contradicts earlier results, and
loses chain-of-thought continuity across rounds. mem-mcp's RECORD-execute
agent (16 tools, up to 12 rounds) is the concrete forcing case; every
adopter of `app` with more than a couple of tools will hit the same wall and
tool-roll the same transcript assembly inside their `LlmCaller`.

Transcript construction belongs in the framework because every piece of it
already does: the trace is framework state, the values behind it live behind
framework refs (`trace_content_refs` + blob store), the budget that bounds it
is a framework concept (`ContextPolicy.max_tokens`), and the segmentation
that truncates it (`continue_as_new`) is a framework decision. The
`ContextPolicy` scopes (`LOCAL` / `SUMMARY` / `WHOLE_SESSION`) already
half-promise this; today they gate *whether* context flows, not *what it
looks like*. This design makes them mean something concrete for `app`.

## Design

### The transcript is derived, not stored

No new state. A transcript is a pure projection of `AgentState.trace` (plus
the run input), materialized at the one place values can be hydrated — the
`invoke_reasoner` effect in the worker (`execution/effects.py`), where blob refs
resolve outside workflow history. Workflow payloads keep carrying refs; the
claim-check limits work stays intact.

```python
# composable_agents/transcript.py (pure core, strict mypy)
def transcript_for(state: AgentStateView, policy: ContextPolicy) -> list[Turn]
# Turn = {"role": "assistant"|"tool", "ref": ToolRefJson|None, "content_ref"|"content": ...}
```

`transcript_for` is deterministic given the same state and policy — it emits
the *plan* of the transcript with refs; hydration of refs to content happens
in the effect, under the blob-durability contract (content-addressed,
immutable, integrity-checked — already mandatory per the session-store
design).

### `ContextPolicy` semantics for `app`

- **`LOCAL`** (default): today's behavior, unchanged — `{input, trace, last}`
  with refs. Zero-cost, replay-identical.
- **`WHOLE_SESSION`**: full hydrated transcript, oldest-first, hard-bounded
  by `policy.max_tokens`. When the bound is exceeded the *oldest* turns are
  dropped and the transcript is prefixed with an explicit
  `{"role": "system", "content": "<n> earlier turns elided"}` marker — the
  model is told, never silently lied to. `max_tokens` is optional on
  `ContextPolicy` in general, but **required for this scope and `SUMMARY` on
  an `app`**: declaring either without a budget is a deploy-time blocking
  diagnostic. There is no implicit default — an unbounded transcript for
  exactly the tool-heavy agents this targets is the failure mode, not a
  fallback.
- **`SUMMARY`**: hydrated recent turns within budget plus a running summary
  of elided turns. The summary is produced by a **named summarizer reasoner
  declared in `AgentConfig`** (`summarizer: Optional[str]`); declaring
  `SUMMARY` scope without a summarizer is a deploy-time blocking diagnostic.
  No implicit default model, no silent downgrade to truncation.

Carriage: dotctx-authored agents derive the policy from
`Reasoner.context_scope` as today. Directly-authored `app(...)` flows have
nowhere to put it — `ContextPolicy` lives on `CallStep`/`ThinkStep` and the
serialized APP node emits only tools/subflows/budget/maxRounds — so `app()`
gains an optional `ctx: ContextPolicy`, serialized on the APP node with
conditional-key inclusion (existing flows' hashes are stable). Nothing
ambient either way.

### Where it executes

`InvokeReasonerInput` grows `transcript: Optional[list[Turn]]` (the ref-bearing
plan, produced in the workflow from `AgentState` — deterministic, cheap).
The `invoke_reasoner` effect hydrates refs via the blob store, enforces
`max_tokens` (tokenizer supplied by the worker via `WorkerContext`, a
char-heuristic default with the real count left to the `LlmCaller`), runs
the summarizer reasoner if the policy demands one, and passes the materialized
transcript to the `LlmCaller`:

```python
LlmCaller = Callable[[Reasoner, Any, Optional[RunPrincipal], Optional[Transcript]], Awaitable[Any]]
```

(Fourth argument. The `configure`-time arity shim must wrap **both** legacy
2-arg callers and principal-aware 3-arg callers — adopters who already moved
to `(reasoner, value, principal)` keep working when transcripts land. The 4-arg
form is canonical; both designs land on the same seam and sequence principal
first.)

### `continue_as_new` and summaries

A `SUMMARY`-scope agent crossing a segment boundary persists its running
summary in `AgentState` (one string field, `summary: Optional[str]` —
the single addition to state) so the next segment doesn't re-summarize from
blobs. `state_fingerprint()` covers it; the codec keeps the continuation
payload bounded as before.

### Determinism and replay

The transcript *plan* is computed in workflow code from workflow state —
deterministic and replay-safe. Hydration and summarization are activity work
with normal retry semantics; the summarizer call is recorded like any
`invokeReasoner`, so a retry re-reads the same trace refs and produces a
recorded result. Replays never re-summarize.

## The C2 stopgap (shipping path before this lands)

Until C1 lands, an adopter assembles the transcript inside their `LlmCaller`:
keep `trace_content_refs` on, fetch the run's trace entries from the blob
store keyed by the refs in `payload["trace"]`, build provider messages, and
enforce the token budget caller-side. This works (the mem-mcp pilot ships on
it) but duplicates per adopter, has no `SUMMARY` support without bespoke
plumbing, and leaks framework state shape into caller code — which is the
argument for C1, not against the stopgap.

## Non-goals

- **Cross-run memory.** The transcript is one run's working history. Durable
  memory across runs is the consumer's product (mem-mcp *is* that product).
- **Provider message-format ownership.** The framework emits a neutral
  `Turn` list; the `LlmCaller` maps it to provider wire formats.
- **Automatic transcript for `think`/`iter_up_to`.** Bounded refinement
  loops keep value-threading semantics; only `app` gets transcripts. A
  bounded loop that needs history should be an `app` with `max_rounds`
  expressed in its config.

## Touch set

| File | Change |
|---|---|
| `composable_agents/transcript.py` | create: `Turn`, `transcript_for` (pure, strict) |
| `composable_agents/agent_loop.py` | `AgentState.summary`; transcript plan in the turn body (via `turn.py` step) |
| `composable_agents/ir.py` / `dsl.py` | optional `ctx: ContextPolicy` on `app()` and the APP node codec (conditional-key, hash-stable) |
| `composable_agents/execution/effects.py` | `InvokeReasonerInput.transcript`; hydration + budget + summarizer in `invoke_reasoner`; `LlmCaller` widening |
| `composable_agents/execution/harness.py` / `dbos_backend.py` | thread the plan into `InvokeReasonerInput` for `app` rounds |
| `validate.py` / deploy pipeline | blocking diagnostics: `SUMMARY` without `summarizer`; `WHOLE_SESSION`/`SUMMARY` on an `app` without `max_tokens` |
| `docs/SPEC.md` | transcript semantics per scope; elision marker; summarizer requirement |
| tests | `transcript_for` determinism + budget edge cases; elision marker; summary persistence across `continue_as_new`; deploy diagnostic; golden corpus unmoved |

<!-- ported-by ca-docs-site: internals/agent-transcripts -->
