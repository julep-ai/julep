---
title: "Agent Transcripts"
description: "The transcript model and how traces are recorded."
---

> Status: shipped in 3.0.0rc4 after the mem-mcp adoption trial. Builds on
> `docs/design/agent-loop-as-turn.md` (the reified
> `Step`), `docs/design/durable-session-store.md` (claim-check codec,
> `trace_content_refs`, blob durability contract), and `ContextPolicy`
> (`julep/ir.py`).

## Thesis

The agent loop gives its controller `{input, trace, last}` — the previous
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

No duplicated durable output state. A transcript is a pure projection of
`AgentState.trace` (plus the run input), materialized at the one place values
can be hydrated — the
`invoke_reasoner` effect in the worker (`execution/effects.py`), where blob refs
resolve outside workflow history. Workflow payloads keep carrying refs; the
claim-check limits work stays intact.

```python
# julep/transcript.py (pure core, strict mypy)
def transcript_for(state: AgentStateView, policy: ContextPolicy) -> list[Turn]
# Turn = {"role": "assistant"|"tool", "ref": ToolRefJson|None, "content_ref"|"content": ...}
```

`transcript_for` is deterministic given the same state and policy. A fresh
observation can remain inline during the current process segment; durable
Temporal and DBOS runners claim-check transcript outputs before a continuation
boundary. Hydration of refs happens in the effect under the blob-durability
contract.

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

For transcript-scoped agents, system and user templates always render from the
original run input. The rendered opening ask replaces the raw first turn before
the token budget is applied. Tool-input, required-tool, and output-validation
re-asks are appended through a reserved feedback turn, also before budgeting;
neither observations nor feedback are reinterpreted as business-template input.

```python
class LlmCaller(Protocol):
    def __call__(
        self,
        reasoner: Reasoner,
        value: Any,
        principal: Optional[RunPrincipal],
        transcript: Optional[Transcript],
        dispatch: ReasonerDispatch,
        *,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> Awaitable[Any]: ...
```

The `configure`-time shim preserves legacy 2-, 3-, 4-, and 5-positional-argument
callers on rounds that do not need a surface they cannot accept. If a legacy
caller declares keyword-only `tools` (or `**kwargs`), the shim forwards native
tool definitions; otherwise a native-tool round fails with an explicit upgrade
message instead of an incidental Python keyword error.

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
| `julep/transcript.py` | create: `Turn`, `transcript_for` (pure, strict) |
| `julep/agent_loop.py` | `AgentState.summary`; transcript plan in the turn body (via `turn.py` step) |
| `julep/ir.py` / `dsl.py` | optional `ctx: ContextPolicy` on `app()` and the APP node codec (conditional-key, hash-stable) |
| `julep/execution/effects.py` | `InvokeReasonerInput.transcript`; hydration + budget + summarizer in `invoke_reasoner`; `LlmCaller` widening |
| `julep/execution/harness.py` / `dbos_backend.py` | thread the plan into `InvokeReasonerInput` for `app` rounds |
| `validate.py` / deploy pipeline | blocking diagnostics: `SUMMARY` without `summarizer`; `WHOLE_SESSION`/`SUMMARY` on an `app` without `max_tokens` |
| `docs/SPEC.md` | transcript semantics per scope; elision marker; summarizer requirement |
| tests | `transcript_for` determinism + budget edge cases; elision marker; summary persistence across `continue_as_new`; deploy diagnostic; golden corpus unmoved |

<!-- ported-by julep-docs-site: internals/agent-transcripts -->
