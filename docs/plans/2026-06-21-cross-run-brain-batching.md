# Cross-Run Reasoner-Call Batching (QoS + Batch API)

**Status:** plan. **Engine:** Temporal first; DBOS trails (see table). **Date:** 2026-06-21.

## What this is

Today every `think` resolves through one seam — `WorkerContext.llm`, the
`LlmCaller` invoked from `invokeReasoner` (`execution/effects.py`). It makes one
provider call and blocks until the reply returns. This plan adds a layer
*behind that seam* that transparently collects reasoner calls **across independent
in-flight runs** and dispatches them at a chosen quality-of-service tier —
including the provider async **Batch API** (Anthropic Message Batches, OpenAI
Batch), which trades latency for ~50% cost on work that isn't latency-sensitive.

Flows do not change. `think` does not change. The IR gains exactly **one**
capability flag; everything else is dispatch.

### Relationship to the existing debounce collator

This is **not** `execution.debounce`. The two batch at different layers and are
complementary (cf. `docs/dispatch-boundary.md`):

| | Debounce collator | Reasoner-call batching (this doc) |
|---|---|---|
| Collapses | *flow-run submissions* into one run | *reasoner calls* across many runs into one provider batch |
| Granularity | whole flow | one `think` step |
| Output | one `FlowWorkflow` over `list[item]` (fan out with `each`) | N replies fanned back to N suspended runs |
| Keyed by | submission `key` | `(provider, qos, principal)` |

Debounce decides *when a batch of inputs exists*; this decides *how the reasoner
calls inside already-running flows are dispatched*.

## The IR / dispatch split

Two new concepts, deliberately on opposite sides of the dispatch boundary.

- **`batchable` — IR capability (frozen).** A correctness fact about the call
  site: may this single reasoner call be durably deferred and resumed later without
  changing user-visible semantics? It is still a one-shot provider request; it is
  not an online agent/controller loop or a multi-round conversation. A downstream
  `seq` step may absolutely depend on the reply — the point is that the workflow
  may suspend at this leaf until the reply arrives. Lives on `Ann` (`ir.py`),
  serialized exactly like `cache`: `think("b", ann=Ann(batchable=True))`.
  Omitted means `False`.
  The `@flow` frontend may expose sugar such as
  `think("b", value, batchable=True)`, but that sugar must fold into `Ann`.
  Reasoner-level defaults are deferred for v1; the call site is explicit. It is a
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
resolve_qos(reasoner, node_ann, principal, load=None) -> QoSTier
```

Precedence: **author hint < deploy default < runtime**. Day one it reads
**principal + author hint**; the `load`/backpressure input is deferred. "User
opts into priority" and "operator demotes under load" are the *same* mechanism
reading different inputs.

**Replay safety.** The *async-or-not* outcome must be deterministic, so it is
resolved **once at the reasoner step's first execution and recorded** (side-effect
/ short activity); replay reads the tier from history and takes the same branch.
Sync-tier dialing (PRIORITY/STANDARD/FLEX) stays live inside the activity since
it never changes control flow.

Keep the request shape small:

```
@dataclass(frozen=True)
class ReasonerDispatch:
    qos: QoSTier = QoSTier.STANDARD
    batch_id: str | None = None
```

Widen the canonical `LlmCaller` one time to accept this as a final optional
argument:

```
(reasoner, value, principal, transcript, dispatch) -> reply
```

`configure(...)` adapts legacy 2/3/4-argument callers to `ReasonerDispatch()` so
existing users keep working. Sync rungs pass `dispatch.qos` down to
`complete_reasoner(...)`, where provider-specific request fields are set. The BATCH
rung does **not** reach `complete_reasoner` through this path; it enters the
collector/poller machinery below.

## Topology: a collector workflow, not in-process

BATCH dispatch uses a durable **`BatchCollector` workflow**, mirroring
`DebounceCollector` inverted. In-process coalescing was rejected for BATCH: it
would hold an `invokeReasoner` activity open for the window *plus* batch turnaround
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
  `ReasonerCall(reasoner, value, principal, transcript, cid, reply_to=run_id)` — the
  run submits the *neutral* form, so no rendering happens in workflow code;
- fires on quiet / `max_items` / `max_wait` (the same fire loop), `max_items` a
  hard cap, surplus carried via `continue_as_new`;
- on fire, the collector **starts a detached child `BatchPoll` workflow** for
  that batch and immediately continues collecting (`continue_as_new`) — it never
  awaits the poll inline. A BATCH job can take up to 24h to finish; if flush+poll
  ran in the collector, `submit` signals arriving during the poll would queue
  behind it, their runs would sit until `node.timeout` and promote to sync, and
  sustained traffic would effectively disable the BATCH rung. The child owns
  flush + poll + result routing; `batch_id` lands in *its* history before the
  poll loop, so a crash resumes polling by id;
- the child routes each result home by **`custom_id`** (see Providers — the cid
  alone is not unique across runs).

### Reasoner-step rendezvous

Reuses the human-gate machinery (`harness.py` — `submitHuman` + `wait_condition`),
inverted and automated. The BATCH branch:

1. **an activity** does the signal-with-start against the collector
   (`client.start_workflow(..., start_signal="submit")`, exactly as
   `submit_debounced` does). Workflow code *cannot* signal-with-start — it can
   only signal an already-running external workflow — so the create-or-join must
   sit behind an activity, consistent with every other effect going through one;
2. `wait_condition(custom_id in self._reasoner_inbox, timeout=node.timeout)`;
3. the child `BatchPoll` workflow signals each `reply_to` with
   `submitReasonerResult(custom_id, reply)` via an external-workflow handle (a
   workflow *can* signal an existing workflow).

The inbox is keyed by `custom_id`, and the signal handler **ignores a result
for a `custom_id` the step has already resolved** (e.g. after a reactive
promote) — and the child tolerates signal-delivery failure to a closed run — so
a late batch completion can neither clobber an advanced step nor fail the poll.

Implementation boundary: make this a Temporal-only activity such as
`submitReasonerBatch`, not a backend-neutral effect in `effects.py`. It receives a
serializable `SubmitReasonerBatchInput` and uses a small worker-installed
`BatchDispatchContext` containing only the Temporal client, task queue, and
collector defaults (`quiet_s`, `max_items`, `max_wait_s`). `build_worker(...)`
already receives the client, so it is the right place to install this context.
DBOS does not register this activity in v1; DBOS clamps BATCH to STANDARD until
it has its own durable suspend/collector equivalent.

### Result routing — signal-back

Push: `FlowWorkflow` exposes its id and a `submitReasonerResult` signal; the
collector signals each originating run. Chosen over a shared result store
(pull + polling) because it reuses the human gate and is cheaper.

## Providers

Lift **both** message rendering *and response parsing* out of `complete_reasoner`
into shared helpers (`_messages`, `_response_format`, `rendered_reasoner_for`, and
**`_parse_reply`**) so sync and batch produce identical *replies*. For
`reply_schema` reasoners `complete_reasoner` doesn't just build messages — it unwraps
the response into the parsed JSON object (or prompt-fallback JSON) that
downstream `think` steps expect; the batch adapter must run the same parser on
each entry, or structured steps receive the wrong shape. A `BatchProvider`
adapter per provider, selected from `reasoner.model` via `_split_model` (`llm.py`):

- **Anthropic** — inline `requests=[Request(custom_id=…, params=…)]`; poll
  `processing_status == "ended"`; stream `.results(id)`. One batch may mix models.
- **OpenAI** — upload JSONL (`purpose="batch"`) → `batches.create(input_file_id,
  endpoint, completion_window="24h")`; poll `status == "completed"`; parse
  `output_file_id`. **OpenAI requires one model per input file**, so the OpenAI
  adapter **sub-splits a partition's items by `reasoner.model` into one file/batch
  per model** at flush. This stays out of the collector key — `model` is *not* a
  partition key (the principle holds); the per-model split is an adapter-local
  concern.

**`custom_id = {run_id}:{cid}`**, not `cid` alone. The activation cid
(`node_id@counter`, e.g. `think@1`) is unique only *within* a run; two runs of
the same frozen flow at the same `think` produce the same cid and would collide
in one shared batch, misrouting replies. Prefixing the run id makes it globally
unique and pins each reply to the right `reply_to`. Results are unordered on
both providers — always key by `custom_id`.

## Promote (two layers)

- **Predictive (primary).** The window is `min(qos_window, node.timeout)`. If
  `timeout_s` < the batch's minimum viable window, `resolve_qos` never returns
  BATCH — the call resolves to FLEX/STANDARD up front. No wasted wait.
- **Reactive (backstop).** If it did enter BATCH and the `wait_condition` times
  out, fall through to the normal `invokeReasoner` activity (sync), recording
  `promoted, reason=batch_timeout`. Both are deterministic branches.

## Errors / expiry

A per-entry provider error or `expired` result **promotes the call to the sync
`invokeReasoner` activity** — the same path as a reactive timeout. This is the
concrete meaning of "route into the existing resilience path": the
fallback/retry/circuit-breaker logic lives *inside* `make_resilient_llm_caller`,
reached only via `invokeReasoner` → `_CTX.llm`. A bare error signal has no
resilience hook, so re-entering `invokeReasoner` *is* the mechanism — not a new
handler. The cost: a flaky provider can quietly turn a "bulk" call into a sync
one (accepted). Whole-batch failure fails the child poll workflow loudly and
signals every `reply_to` an error. Dedup on `custom_id`.

## Observability

Two sinks, and the projection is the subtle one. The in-workflow **derived
projection** is driven by the interpreter's `Result` envelope from
`env.invoke_reasoner` — *not* by the worker-side `AttemptRecord`. So to make a
successful batched `think` explainable, `batch_id` + `tier` must ride back in a
framework envelope, then be unwrapped immediately by the interpreter:

```
{"__ca_meta__": {"tier": "BATCH", "batch_id": "..."}, "reply": actual_reply}
```

Only `actual_reply` flows downstream and is stored as the `Did.value`; the
metadata becomes `Result.attrs` on that `Did` event. This keeps structured reasoner
replies untouched. The unwrapping helper must handle both framework envelopes:
preserve today's summary unwrap, then strip `__ca_meta__` into attrs before the
reply enters user flow data. Extending `AttemptRecord` alone only feeds the
worker/OTel sink and leaves the projection blind. Carry batch attribution through
both — `Result.attrs` (for the projection) and `AttemptRecord` (for OTel) — to
preserve the explain-every-step guarantee.

## Engine support

| Concern | Temporal | DBOS |
|---|---|---|
| `Ann.batchable` (IR) | ✅ M0 | ✅ (IR is engine-neutral) |
| `resolve_qos` seam + recorded tier | ✅ M0 | trails |
| `LlmCaller` `ReasonerDispatch` argument | ✅ M1 | trails |
| Sync rungs (priority/standard/flex via request field) | ✅ M1 | trails |
| Sync coalescer (Path A, gather) | ✅ M1 | trails |
| `submitReasonerBatch` Temporal activity + client context | ✅ M2 | trails |
| `BatchCollector` + rendezvous (BATCH rung) | ✅ M2 | trails — needs DBOS equivalent of signal-with-start collector + durable suspend (cf. `dbos.Debouncer`) |
| Promote / errors / expiry | ✅ M3 | trails |
| OpenAI `BatchProvider` | ✅ M4 | trails |
| Backpressure input to `resolve_qos` | later | later |

DBOS trails because the collector is workflow-shaped (as `execution.debounce`
is Temporal-only today); the DBOS port mirrors `dbos.Debouncer` + a durable
reasoner-step suspend.

## Milestones

- **M0** — `Ann.batchable` + `resolve_qos` seam + recorded QoS step; BATCH
  no-ops to STANDARD. Proves the branch + recording with no new infra.
- **M1** — `ReasonerDispatch` on `LlmCaller`, shared renderer + `BatchProvider`
  interface + sync coalescer. Ships Path A (in-process micro-batching) as a real
  deliverable, no durability risk.
- **M2** — `submitReasonerBatch` activity + `BatchCollector` + rendezvous +
  Anthropic Batch API. The BATCH rung.
- **M3** — promote (predictive + reactive), per-entry errors, expiry.
- **M4** — OpenAI `BatchProvider`. *(Later: FLEX/PRIORITY rungs hardening,
  backpressure input.)*
