# Langfuse integration — design

**Date:** 2026-06-22
**Status:** Design approved; ready for implementation plan
**Scope:** Passive observability export of `composable_agents` runs into Langfuse — run/DAG traces, LLM generations (token usage / cost / model), and the cost+latency dashboards Langfuse derives. **Not** prompt management, datasets, or evals.

---

## 1. Goal

Export every `composable_agents` run to Langfuse so an operator can see, per run:

1. **Run/DAG trace** — the activation tree (which nodes ran, causal order, success/failure, timing).
2. **LLM generations** — each model call as a Langfuse *generation* with served model, token usage, and cost.
3. **Cost + latency dashboards** — derived by Langfuse from the generation data above; no extra integration beyond getting model + tokens + real timestamps flowing.

Out of scope (deliberately): prompt management, prompt versioning, datasets, scores/evals, and any path where Langfuse *drives* the application. This is one-directional export.

## 2. Decisions (locked during brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| Export route | **OTLP-native** (Approach A) | Reuses the existing projection→OTel exporter; smallest dependency (OTLP exporter, no vendor SDK); vendor-neutral; determinism boundary already solved. |
| Placement | **`composable_agents` core, new `langfuse` extra**, next to `execution/otel.py` | Reusable by any downstream consumer (mem-mcp included); guarded optional import like the existing `otel` extra. |
| Backends covered | **Temporal** + **local/facade** | (DBOS deferred — design stays sink-shaped so DBOS is trivial later.) |
| Multi-attempt fidelity | **Final generation + compact attempt list** | One generation per activation (served model); prior failed/fallback attempts summarized in `attrs`. Cost still sums correctly; minimal export plumbing. |
| Batch generations | **In scope** | The brain-batching path bypasses `acompletion` and discards usage today; covering it avoids a permanent blind spot in batched runs. |

### Rejected approaches

- **Approach B — native Langfuse SDK via `ProjectionSink` adapter.** Richest fidelity, but adds a vendor SDK to a core extra, couples to the SDK shape, and re-implements the span-tree/parent-link logic `otel.py` already has. The extra fidelity (sessions/users/scores) isn't bought by the chosen goals.
- **Approach C — hybrid (OTLP default + documented SDK path).** Over-builds a second path we don't need yet. The vendor-neutral *capture* work (the valuable part of C) is folded into Approach A regardless.

## 3. Architecture

Three stages, with the projection as the vendor-neutral carrier in the middle. Nothing Langfuse-specific touches workflow / determinism-sensitive code; the only core change is making the projection *generation-aware*, which benefits every sink (OTel, Logfire, Postgres), not just Langfuse.

```
  LlmCaller (llm.py)              Projection (core, vendor-neutral)         Export (langfuse extra, outside workflow)
  ─────────────────              ─────────────────────────────────         ──────────────────────────────────────
  acompletion(...).usage ──┐
   model/provider/tokens    │
   wall-clock start/end     │
                           ▼
   LlmResult{reply, meta} ──► invokeReasoner / interpreter boundary
                                     │
                                     ▼
                         ProjectionEmitter.did(
                             cost=meta.cost,
                             attrs={model, usage, started_at,
                                    ended_at, llm_attempts, io_refs?})
                                     │  (Planned/Did/Failed stream; logical ts untouched)
                                     ▼
                            to_otel_spans → SpanData(+attrs,+cost,+value_ref,+event_ids)
                                                     │
                                                     ▼
                                            export_spans(tracer=langfuse, run_id=…)
                                                     │  OTLP/HTTP + basic-auth, stable derived IDs
                                                     ▼
                                            Langfuse (trace → spans → generations,
                                                      cost/latency dashboards)
```

**Determinism boundary.** The projection `ts` is a *logical counter* by design (`ProjectionEmitter`, `projection.py:271`) so replay is deterministic. Real wall-clock start/end are captured in the *activity* (the non-deterministic side) and carried in `attrs` — the exporter uses those, never the logical `ts`. Export always runs **outside** the workflow.

## 4. Components

### 4.1 Capture — typed result envelope (replaces the `AttemptRecord` hook)

**Problem (found in Codex review):** the original plan threaded usage via the `on_attempt` global callback (`effects.py:287`) and `AttemptRecord` (`resilience.py:139`). That record has no activation identity (no `cid`/`node`/`run_id`/timing), so there is no reliable way to bind it to the exact `Did` emitted later by `interpreter.interpret()`. And `complete_reasoner` returns only the parsed reply (`llm.py:267`), discarding the completion object that holds `.usage`.

**Design:**

- `complete_reasoner` (llm.py) returns an internal typed `LlmResult{reply, meta}`. The public seam shape is preserved by unwrapping `meta` at the `invokeReasoner` effect boundary; callers that only want `reply` are unaffected.
- `LlmCallMeta`:
  - `served_model: str`, `provider: str`
  - `usage: {input: int, output: int, total: int}` (from `completion.usage`)
  - `started_at: float`, `ended_at: float` — **wall-clock**, stamped in the activity
  - `attempts: list[AttemptMeta]` — `{model, provider, outcome, usage?, ms}`, built by augmenting the per-attempt `AttemptRecord`s the resilience loop already mints (`llm.py:402`) with usage
  - `cost: Optional[float]` — left `None` by default (Langfuse infers from model + tokens); populated only if the framework already knows a cost
- At the boundary, `meta` lands in `did(cost=meta.cost, attrs={...})`:
  - `model`, `usage`, `started_at`, `ended_at`, `llm_attempts` (compact list)
  - `io_refs?` — value_refs for prompt + completion, **gated behind a `capture_io` flag** (PII / payload size). Off by default.
- `ProjectionEvent.attrs` / `cost` already exist (`projection.py`) — **no event-schema change**.

### 4.2 Carry — `SpanData` enrichment

`SpanData` (`projection.py:316`) currently drops `attrs`/`cost`. Extend it with:

- `attrs: dict`, `cost: Optional[float]`, `value_ref: Optional[str]`
- `planned_event_id`, `terminal_event_id` (for stable ID derivation)

`to_otel_spans` copies these from the planned + terminal events. Span start/end come from `attrs` wall-clock when present (LLM activations); otherwise fall back to logical `ts`, flagged synthetic.

### 4.3 Export — `execution/langfuse.py` (Langfuse-specific) + small `otel.py` extension

Split of responsibility (avoids bloating the generic exporter):

- **`otel.py` (generic, stays link-based):** minimal extension only — set `SpanData.attrs` onto the OTel span, and use `attrs` wall-clock for span start/end when present. Keeps the existing multi-cause **link** model unchanged for vendor-neutral OTel backends (Jaeger/Grafana).
- **`execution/langfuse.py` (new, Langfuse-specific):** owns everything Langfuse's tree model needs — synthetic root, primary-parent nesting, the custom `IdGenerator`, and the `langfuse.*` attribute mapping + OTLP config. It consumes `to_otel_spans` output and builds the tree itself rather than going through `otel.py::export_spans`.

`export_spans` (`otel.py:63`) today creates every span as a root linked via `Link()` — no parent nesting, no trace root. The Langfuse path in `langfuse.py` instead produces:

- **Synthetic root span per run** = the Langfuse trace. Required: Langfuse creates a trace from a root span.
- **DAG → tree.** Langfuse renders a strict tree (one parent per observation) and **ignores OTel links**. Give each span a single **primary parent** — first cause in deterministic topological order, fallback = run root — as its real OTel parent for nesting. Keep non-primary causes as OTel **links** (lossless for OTel-native backends, ignored by Langfuse). Guards: deterministic topological sort, cycle detection, orphan handling.
- **Stable IDs** via a custom OTel `IdGenerator`: `trace_id = hash128(run_id)`, `span_id = hash64(cid)`. Makes Temporal history re-export **idempotent** (no duplicate observations).
- **Attribute mapping** — emit both for portability + fidelity:
  - `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`
  - `langfuse.observation.type = "generation"` for reasoner/attempt spans only (plain spans otherwise)
  - `langfuse.observation.input` / `langfuse.observation.output` (from `io_refs`, when `capture_io`)
  - `langfuse.session.id`, `langfuse.trace.name` — propagated onto **every** span (Langfuse trace-level aggregations read these per span)
- `configure_langfuse()`:
  - `TracerProvider` + `BatchSpanProcessor` + `OTLPSpanExporter`
  - endpoint `$LANGFUSE_HOST/api/public/otel/v1/traces` (HTTP/protobuf — **not** gRPC)
  - headers: `Authorization: Basic b64($LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY)`, `x-langfuse-ingestion-version: 4`
  - `force_flush()` / `shutdown()` helper so short-lived CLI/local runs flush before exit
- **pyproject extra:**
  ```toml
  langfuse = [
      "opentelemetry-exporter-otlp-proto-http>=1.20",
      "opentelemetry-api>=1.20",
      "opentelemetry-sdk>=1.20",
  ]
  ```

### 4.4 Backend wiring

- **Local / facade:** `Agent` gets opt-in export. After a run, `export_run_to_langfuse(emitter.store.events(), run_id)` then force-flush.
- **Temporal:** post-run export via the existing `projection` query (MVP — live / post-run snapshot), run entirely **outside** the workflow (client-side or a small exporter process). History-tail documented as the durable re-export path for later (must recover real activity timestamps + stable IDs). Interceptor **rejected** as the riskiest (couples to SDK internals, risks dragging export toward workflow execution).

### 4.5 Batch coverage

`reasoner_batch.py` and the batch adapters (`openai_batch.py:133`, `anthropic_batch.py:125`) currently parse replies but discard provider usage. Change them to capture per-`custom_id` usage from the batch result lines and route it through the **same** `meta`/`attrs` path, so batched activations emit generations identically to sync ones. Batch latency is the submit→complete window (legitimately long) — the exporter reflects real submit/complete wall-clock rather than treating it as a stall.

## 5. Testing

### De-risk spike (do first)

A tiny script pushes one synthetic run via OTLP to a real Langfuse instance (self-hosted or cloud) and confirms:

- nested span tree renders (primary-parent nesting works)
- a generation shows tokens + cost
- derived IDs are stable on re-export (no duplicate observations)
- wall-clock latency looks right
- batch-window latency renders sanely

This pins the exact Langfuse attribute keys and retires the one real unknown before bulk implementation.

### Unit tests (pure, no network — reuse the `spans_to_dicts` pattern)

- capture: usage threaded through `LlmResult`; attempt list populated; wall-clock present
- `SpanData` enrichment carries attrs/cost/value_ref/event-ids
- DAG → tree: primary-parent selection, cycle/orphan handling, non-primary causes as links
- `IdGenerator` stability (same run_id/cid → same IDs)
- golden attribute-mapping dict (gen_ai.* + langfuse.* keys)
- batch usage capture in the batch adapters

### Verification gate

- `python -m pytest`
- `uv run mypy --strict composable_agents`

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Langfuse OTLP attribute keys drift from assumptions | De-risk spike pins exact keys against a live instance before bulk work. |
| Cost inference wrong for custom/renamed models | Emit `gen_ai.usage.*` + model; allow explicit `meta.cost` override path; don't rely solely on Langfuse's price table. |
| Re-export duplicates observations | Stable derived IDs via custom `IdGenerator` (trace = hash(run_id), span = hash(cid)). |
| Short-lived runs exit before `BatchSpanProcessor` flushes | `configure_langfuse()` exposes force-flush/shutdown; local/CLI path calls it. |
| Logical-counter timestamps leak into latency | Exporter uses `attrs` wall-clock only; logical `ts` never used for span timing. |
| Batch latency looks like a stall | Exporter uses real submit/complete wall-clock for batch generations. |

## 7. Touched files (implementation surface)

- `composable_agents/execution/llm.py` — `LlmResult`/`LlmCallMeta`, capture usage + wall-clock + attempts
- `composable_agents/execution/effects.py` — unwrap `meta` at the `invokeReasoner` boundary
- `composable_agents/projection.py` — `SpanData` fields; `to_otel_spans` carries attrs/cost/value_ref/event-ids
- `composable_agents/execution/otel.py` — minimal extension: set `attrs` on spans, use wall-clock start/end (generic link model unchanged)
- `composable_agents/execution/langfuse.py` — **new**: synthetic root + primary-parent tree, `IdGenerator`, attribute mapping, `configure_langfuse()`, `export_run_to_langfuse`
- `composable_agents/execution/reasoner_batch.py`, `openai_batch.py`, `anthropic_batch.py` — capture batch usage
- `composable_agents/agent.py` — opt-in local export hook
- `pyproject.toml` — `langfuse` extra
- `tests/…` — unit tests per §5

## 8. Appendix — Codex review incorporated

An independent Codex review (read against the real source) changed the design in five ways, all folded in above:

1. Capture moved off the global `AttemptRecord` hook (no activation identity) to a typed `LlmResult{reply, meta}` envelope.
2. Wall-clock timestamps captured in the activity — logical `ts` is unusable for latency.
3. Stable derived trace/span IDs for idempotent re-export.
4. Multi-attempt + batch coverage surfaced as explicit scope decisions (resolved: final+attempt-list; batch in scope).
5. Confirmations: synthetic root required, `proto-http` (not gRPC), `x-langfuse-ingestion-version: 4`, emit both `langfuse.observation.*` and `gen_ai.*`, propagate trace-level attrs onto every span.
