# Cross-Run Brain-Call Batching (QoS + Batch API)

**Status:** plan. **Engine:** Temporal first; DBOS trails (see table). **Date:** 2026-06-21.

## What this is

Today every `think` resolves through one seam — `WorkerContext.llm`, the
`LlmCaller` invoked from `invokeBrain` (`execution/effects.py`). It makes one
provider call and blocks until the reply returns. This plan adds a layer
*behind that seam* that transparently collects brain calls **across independent
in-flight runs** and dispatches them at a chosen quality-of-service tier —
including the provider async **Batch API** (Anthropic Message Batches, OpenAI
Batch), which trades latency for ~50% cost on work that isn't latency-sensitive.

Flows do not change. `think` does not change. The IR gains exactly **one**
capability flag; everything else is dispatch.

### Relationship to the existing debounce collator

This is **not** `execution.debounce`. The two batch at different layers and are
complementary (cf. `docs/dispatch-boundary.md`):

| | Debounce collator | Brain-call batching (this doc) |
|---|---|---|
| Collapses | *flow-run submissions* into one run | *brain calls* across many runs into one provider batch |
| Granularity | whole flow | one `think` step |
| Output | one `FlowWorkflow` over `list[item]` (fan out with `each`) | N replies fanned back to N suspended runs |
| Keyed by | submission `key` | `(provider, qos, principal)` |

Debounce decides *when a batch of inputs exists*; this decides *how the brain
calls inside already-running flows are dispatched*.

## The IR / dispatch split

Two new concepts, deliberately on opposite sides of the dispatch boundary.

- **`batchable` — IR capability (frozen).** A correctness fact about the call
  site: is this `think` an independent one-shot completion, or a step whose
  reply the next step depends on (an agent loop, a multi-round conversation)?
  Only the author knows, and it travels with the flow. Lives on `Ann`
  (`ir.py`), serialized exactly like `cache`. `think(..., batchable=True)`; a
  `Brain` may declare a default that the call site overrides. It is a
  *capability*, never a policy — it sets the **floor** of how low on the QoS
  ladder a call may go.

- **`qos` — dispatch policy (live).** Where, within the allowed range, the call
  actually runs. Cost/latency/load policy, resolved at dispatch. Not in the IR.

The two compose without overlap: `batchable` sets the floor, `qos` picks within
`[PRIORITY .. floor]`.

## The QoS ladder

```
PRIORITY   -> sync API, priority tier      (premium $, lowest latency)
STANDARD   -> sync API, default
FLEX       -> sync API, degraded tier       (cheaper, slower; OpenAI service_tier="flex")
----------- async boundary -----------
BATCH      -> Batch API                     (~50% off, <=24h)
```

The top three rungs are **synchronous** — they change only cost/latency/rate
limit, not blocking semantics, so any call may move among them, and the choice
can be made *live inside the activity* (non-determinism is fine there). Only
**BATCH** crosses into async and changes workflow control flow; that crossing is
what `batchable` gates. Clamp: `if not batchable: floor = FLEX`.

The three sync rungs are a single request field (Anthropic priority tier,
OpenAI `service_tier`). Only BATCH needs new machinery.

## Dispatch resolution

A `resolve_qos` seam on `WorkerContext`:

```
resolve_qos(brain, node_ann, principal, load=None) -> QoSTier
```

Precedence: **author hint < deploy default < runtime**. Day one it reads
**principal + author hint**; the `load`/backpressure input is deferred. "User
opts into priority" and "operator demotes under load" are the *same* mechanism
reading different inputs.

**Replay safety.** The *async-or-not* outcome must be deterministic, so it is
resolved **once at the brain step's first execution and recorded** (side-effect
/ short activity); replay reads the tier from history and takes the same branch.
Sync-tier dialing (PRIORITY/STANDARD/FLEX) stays live inside the activity since
it never changes control flow.

## Topology: a collector workflow, not in-process

BATCH dispatch uses a durable **`BatchCollector` workflow**, mirroring
`DebounceCollector` inverted. In-process coalescing was rejected for BATCH: it
would hold an `invokeBrain` activity open for the window *plus* batch turnaround
(up to 24h) — thousands of parked pending-activity records. A workflow
rendezvous makes the wait a durable timer/signal, survives worker restarts, and
keeps batch state durable by construction.

(In-process gather remains correct for the *sync* rungs — that is the Path A
coalescer, delivered as a byproduct in M1.)

### `BatchCollector`

Reuses the debounce structure almost verbatim:

- keyed `batch:{provider}:{qos}:{principal_key}` — one batch runs as one
  principal (as in debounce);
- `submit` signal-with-start carries a neutral
  `BrainCall(brain, value, principal, transcript, cid, reply_to=run_id)` — the
  run submits the *neutral* form, so no rendering happens in workflow code;
- fires on quiet / `max_items` / `max_wait` (the same fire loop), `max_items` a
  hard cap, surplus carried via `continue_as_new`;
- flush + poll run in the collector's own activities — `batch_id` lands in
  history *before* the poll loop, so a crash resumes polling by id;
- routes each result home by `cid`.

### Brain-step rendezvous

Reuses the human-gate machinery (`harness.py` — `submitHuman` + `wait_condition`),
inverted and automated. The BATCH branch:

1. signal-with-start the collector with the `BrainCall`;
2. `wait_condition(cid in self._brain_inbox, timeout=node.timeout)`;
3. collector signals each `reply_to` with `submitBrainResult(cid, reply)`.

### Result routing — signal-back

Push: `FlowWorkflow` exposes its id and a `submitBrainResult` signal; the
collector signals each originating run. Chosen over a shared result store
(pull + polling) because it reuses the human gate and is cheaper.

## Providers

Lift message-building out of `complete_brain` (`_messages`,
`_response_format`, `rendered_brain_for`) into a shared renderer so the sync
caller and the batch path produce identical bodies. A `BatchProvider` adapter
per provider, selected from `brain.model` via `_split_model` (`llm.py`):

- **Anthropic** — inline `requests=[Request(custom_id=cid, params=…)]`; poll
  `processing_status == "ended"`; stream `.results(id)` by `custom_id`.
- **OpenAI** — upload JSONL (`purpose="batch"`) → `batches.create(input_file_id,
  endpoint, completion_window="24h")`; poll `status == "completed"`; parse
  `output_file_id` by `custom_id`.

`custom_id = cid` (the deterministic activation id, `effects.py`) end to end.
Batch results are unordered on both — always key by `custom_id`.

## Promote (two layers)

- **Predictive (primary).** The window is `min(qos_window, node.timeout)`. If
  `timeout_s` < the batch's minimum viable window, `resolve_qos` never returns
  BATCH — the call resolves to FLEX/STANDARD up front. No wasted wait.
- **Reactive (backstop).** If it did enter BATCH and the `wait_condition` times
  out, fall through to the normal `invokeBrain` activity (sync), recording
  `promoted, reason=batch_timeout`. Both are deterministic branches.

## Errors / expiry

Per-entry provider error or `expired` routes home as a brain error into the
run's **existing** resilience path (which may itself sync-retry). This keeps
batch failures from being a new error class — at the cost that a flaky provider
can quietly turn a "bulk" call into a sync one (accepted). Whole-batch failure
fails the collector loudly and signals every `reply_to` an error. Dedup on `cid`.

## Observability

Extend `AttemptRecord` with `batch_id` + `tier` so the derived projection still
explains every step — "served via batch {id}, tier=bulk" — preserving the
explain-every-step guarantee.

## Engine support

| Concern | Temporal | DBOS |
|---|---|---|
| `Ann.batchable` (IR) | ✅ M0 | ✅ (IR is engine-neutral) |
| `resolve_qos` seam + recorded tier | ✅ M0 | trails |
| Sync rungs (priority/standard/flex via request field) | ✅ M1 | trails |
| Sync coalescer (Path A, gather) | ✅ M1 | trails |
| `BatchCollector` + rendezvous (BATCH rung) | ✅ M2 | trails — needs DBOS equivalent of signal-with-start collector + durable suspend (cf. `dbos.Debouncer`) |
| Promote / errors / expiry | ✅ M3 | trails |
| OpenAI `BatchProvider` | ✅ M4 | trails |
| Backpressure input to `resolve_qos` | later | later |

DBOS trails because the collector is workflow-shaped (as `execution.debounce`
is Temporal-only today); the DBOS port mirrors `dbos.Debouncer` + a durable
brain-step suspend.

## Milestones

- **M0** — `Ann.batchable` + `resolve_qos` seam + recorded QoS step; BATCH
  no-ops to STANDARD. Proves the branch + recording with no new infra.
- **M1** — shared renderer + `BatchProvider` interface + sync coalescer. Ships
  Path A (in-process micro-batching) as a real deliverable, no durability risk.
- **M2** — `BatchCollector` + rendezvous + Anthropic Batch API. The BATCH rung.
- **M3** — promote (predictive + reactive), per-entry errors, expiry.
- **M4** — OpenAI `BatchProvider`. *(Later: FLEX/PRIORITY rungs hardening,
  backpressure input.)*
