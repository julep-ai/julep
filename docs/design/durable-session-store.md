# Keeping agent state/trace within Temporal limits

> Status: revised 2026-06-08 after an adversarial review by codex (gpt-5.5), then
> implemented 2026-06-09. Migration steps 1, 3, and 4 are now shipped (codec +
> blob-durability contract via `execution/blobstore.py` + `execution/codec.py`; the
> gated `SessionStore` via `execution/session_store.py` + the `loadState` /
> `commitState` / `putBlob` activities and the `AgentWorkflow` `state_cursor` seam;
> default-off context fidelity via `trace_content_refs`). Step 2 is assessed below
> (see "Step 2 — event-count assessment"). Companion to `algebra.hs` (the `Session`
> abstraction) and the Temporal harness (`composable_agents/execution/harness.py`).
> The raw review findings are reproduced in the appendix.

## Thesis (revised)

The agent harness currently carries the **full, monotonically-growing `AgentState`** across
the Temporal wire: into continue-as-new (`state=state.to_json()`, `harness.py:752`) and
into the reasoner activity every round (`{"input": state.last, "trace": [...]}`,
`harness.py:649`). That overflows Temporal's payload/history limits for any non-trivial
agent.

The fix is **one mechanism, not two**: a **claim-check Payload Codec** (Temporal External
Storage) offloads large payloads transparently, and the **continue-as-new already in the
harness** (`should_continue_as_new`, `agent_loop.py:290`) bounds history *event count*.
Together they keep us inside the limits.

A first-class **`SessionStore`** — the algebra's `Session`, externalized and queryable — is
a **separate, optional** decision justified by *queryability, cross-runtime sharing, and
explicit lifecycle ownership*, **not** by Temporal byte limits. An earlier draft of this
note framed it as size-necessary; it is not. Build it only if those product reasons earn it.

The non-negotiable part is a **blob-durability contract**: the instant you offload anything
referenced by workflow history, replay-safety depends on those blobs being content-
addressed, immutable, retained, and integrity-checked. That contract is mandatory whichever
mechanism you choose.

## The constraint

Temporal limits (current, 2026):

- **Single payload: 2 MB hard error.** Applies to every workflow input, activity arg/return,
  **and continue-as-new arguments**. (A server-side *warning* is logged below the hard
  limit — default ~256 KB on self-hosted; not a Cloud-surfaced threshold, so don't design
  to it.)
- **gRPC message / history transaction: 4 MB.** The whole request — all payloads + command
  metadata in one Workflow Task — must fit.
- **History: 50 MB / 51,200 events** hard; perf sweet-spot < 10k events. Replay cost is
  linear in event count.

Temporal's own guidance: offload large payloads to an object store, pass references (the
*claim-check* pattern) — built into the SDKs as External Storage, or rolled by tool with a
custom Payload Codec.

## What actually overflows today

| Site | Carries | Anchor | Bloat axis |
|---|---|---|---|
| continue-as-new input | the whole `AgentState` (`trace` + `last` + `call_counts`) | `harness.py:752` | bytes (per-payload) + re-persisted into the new run's first history event |
| reasoner activity input, every round | `{"input": state.last, "trace": [...]}` | `harness.py:649` | bytes; trace count grows |
| tool-call result → `state.last` | an arbitrary tool output | `harness.py:702` (call path; `:733` is the sub path) | bytes (a single big value blows 2 MB in one round) |
| terminal result | `output` **+ full `trace`** | `agent_loop.py:295` (`terminal_result`) | bytes at completion — never seen by a CAN-time store |
| `FlowWorkflow` (sibling path) | activity/child events, **no continue-as-new** | `harness.py:447` | event *count* — codec shrinks bytes, not count |

Two things to note from this table that the earlier draft got wrong:

- **`state.last` is not "already a pointer."** A transparent codec decodes *before*
  application code, so the workflow sees the full logical value at `harness.py:702`; only
  the wire/history representation is a pointer. That's fine — in-memory size is RAM, not the
  Temporal constraint — but it means the codec, not any in-loop cleverness, is what keeps
  the *wire* small.
- **`SessionStore`-at-continue-as-new does not shrink the per-round reasoner input**
  (`harness.py:649`) or the terminal result (`agent_loop.py:295`). Only the codec (bytes)
  or a cursor/summary-based prompt path touches those. So the codec is load-bearing; the
  store is not a substitute for it.

---

## Mechanism: the Payload Codec is the size fix

Register a custom `PayloadCodec` (or Temporal's built-in External Storage) on the worker's
data converter. On **encode** (worker/client side, before the gRPC send): any payload over a
threshold is `put_blob`'d to object storage and replaced by a small content-addressed
envelope `{"_ref": "<tenant>/<hash>", "_codec": "ext/1"}`. On **decode** (before application
code): `get_blob` resolves it back. Temporal enforces its size limits on the **encoded**
(post-codec, pointer-sized) payload, which is why this is the canonical claim check.

What it fixes, with **zero control-loop changes**:

- continue-as-new `state.to_json()` (`harness.py:752`) — offloaded; only the pointer lands
  in the new run's history.
- `callTool` return (`activities.py:155`) and `invokeReasoner` return (`activities.py:163`) — a
  large tool output or model reply never lands in history raw.
- the reasoner activity input `{"input": state.last, "trace": [...]}` (`harness.py:649`) and
  the terminal result (`agent_loop.py:295`) — shrunk on the wire.

What it does **not** fix:

- **History event count.** The codec shrinks bytes per event, not the number of events.
  That is the job of `should_continue_as_new` (`agent_loop.py:290`), already wired for
  `AgentWorkflow`. **`FlowWorkflow` (`harness.py:447`) has no continue-as-new** — a flow that
  fans out many activities/children can still approach 51,200 events. Mitigation there is
  batching or a CAN seam on the flow path; track it separately from this note.
- **In-memory size / quality.** The model still only sees `state.last` + a ref-only trace
  (the stateless-context limitation); see "Context fidelity" below.

---

## The blob-durability contract (mandatory, not optional)

The moment any payload referenced by workflow history is a pointer, **replay correctness
depends on the blob store**. "Replay rebuilds state from history" is only true if the
referenced blobs are still there and unchanged. So the codec/store MUST guarantee:

1. **Content-addressed.** The ref *is* `hash(value)` (e.g. `<tenant>/sha256:...`). Identical
   values dedupe; a ref can never silently point at different bytes.
2. **Immutable.** Blobs are write-once. No overwrite of an existing hash.
3. **Integrity-checked on read.** `get_blob` re-hashes and rejects a mismatch — a corrupted
   or substituted blob fails loudly rather than feeding the model different input on replay.
4. **Retained ≥ the workflow's history retention horizon.** A blob may be referenced by any
   history within Temporal's retention window; GC must not collect a blob still reachable
   from a non-expired history. Tie blob TTL to (or above) namespace retention.
5. **Tenant-scoped and access-controlled.** Refs are namespaced by tenant; one tenant cannot
   read another's blob by guessing a hash. Encrypt at rest if payloads are sensitive.

Without (1)–(4), a transparent codec silently makes *every* replay depend on an external
store, and a GC'd or mutated blob turns a deterministic replay into a failure or — worse — a
*different* result. This is the single biggest correctness requirement in the design.

---

## Optional: a first-class `SessionStore`

Justified by **queryability** (inspect/replay/analyze a session outside Temporal),
**cross-runtime sharing** (the same `Session` for the local / CMA / Temporal runtimes, as
`algebra.hs:140` posits), and **explicit lifecycle ownership** (making the external-store
coupling visible in the workflow input instead of hidden in the data converter). It is **not
a payload-size fix** — the codec already is. Build it if and only if those reasons hold.

If built, it carries only `(session_id, cursor)` through Temporal:

```python
Cursor = int  # monotonic version; opaque to the workflow.

class SessionStore(Protocol):
    """Durable, append-only agent state/trace keyed by session. The algebra's
    `Session` (algebra.hs:140; recall/append at :207-208), externalized."""

    async def load(self, session_id: str, cursor: Cursor) -> AgentState: ...
    async def commit(self, session_id: str, base: Cursor,
                     state: AgentState, state_hash: str) -> Cursor: ...
    # claim-check for one value; shares the codec's content-addressed object store.
    async def put_blob(self, tenant: str, value: Any) -> str: ...
    async def get_blob(self, tenant: str, ref: str) -> Any: ...   # re-hash + verify
```

**Activities** (I/O lives here — workflow code is deterministic; ambient I/O in it is
replay-unsafe, so the store is reached only through activities or SDK-supported deterministic
mechanisms):

```python
@activity.defn(name="loadState")
async def loadState(inp: LoadStateInput) -> dict[str, Any]:
    return (await _CTX.session_store.load(inp.session_id, inp.cursor)).to_json()

@activity.defn(name="commitState")
async def commitState(inp: CommitStateInput) -> Cursor:
    state = al.AgentState.from_json(inp.state)
    return await _CTX.session_store.commit(
        inp.session_id, inp.base, state, inp.state_hash)
```

`_CTX` is the existing `WorkerContext` (`activities.py:48`, configured at `:76`); add a
`session_store` field beside `llm` / `mcp_call`.

**Seam change** in `AgentWorkflow`: replace `AgentInput.state: Optional[dict]`
(`harness.py:237`) with `state_cursor: Optional[Cursor]`; rehydrate once at the top of `run`
(`harness.py:633`) via `loadState`; at continue-as-new (`harness.py:741`) call `commitState`
and carry `state_cursor=cursor`. Commit **only at the CAN boundary** — within a single run
the in-memory `AgentState` is already deterministic (rebuilt by replaying activity results),
so per-round persistence buys nothing for recovery. (Opt-in per-round `commitState`, behind
an `ExecutionPolicy` flag, only if you want the live trace queryable before a CAN boundary.)

### Invariants the `SessionStore` must hold

1. **`session_id` ↔ Temporal workflow-id is 1:1.** This is the concurrency guard. CAS by
   `(session_id, base)` alone does *not* stop two runs of the same session from both firing
   tool effects before the loser notices `base` moved; it only prevents a forked store
   revision. Binding `session_id` to the workflow id delegates mutual exclusion to Temporal's
   "one running execution per workflow id" guarantee. The store CAS then exists only for
   crash-recovery idempotency, not concurrency control.
2. **Commit idempotency is keyed by `(session_id, base, state_hash)`, atomically.** If the
   store write succeeds but the activity's completion isn't recorded, Temporal retries
   `commitState`; returning the existing cursor is correct *only* because the store can
   recognise "same state over same base" by hash and refuse to fork. This is the harness-level
   analogue of the algebra's stable-`CallId` + `Planned`-before-`Did` idempotency
   (`algebra.hs:148`, `:166`).
3. **Stored `AgentState` carries a schema/version envelope.** A future change to `TraceEntry`
   (`agent_loop.py:203`), `callCounts`, `last`, or ref encoding must not strand old sessions —
   record a version and migration rule alongside the state (`agent_loop.py:255`).

---

## Context fidelity (a quality change, separate from durability)

`TraceEntry` already carries `input_ref` / `output_ref` / `schema_ref` (`agent_loop.py:210`)
but the loop builds entries without them (`turn.py:162`, `harness.py:703`). The same claim-
check that offloads a value should populate `output_ref = <ref>`. Then the trace becomes a
genuine content-addressed log, the divergence from `algebra.hs:149`'s value-carrying
`Did CallId Name Value Value` becomes principled rather than lossy, and `invokeReasoner` can
resolve prior observations via `get_blob` instead of being limited to `state.last`.

Caveat — this changes retry semantics: if an `invokeReasoner` activity retries and a referenced
blob has changed or disappeared, the prompt (and the LLM result) changes. It is safe **only**
under the full blob-durability contract above (content-addressed, immutable, hash-verified,
tenant-scoped). Do not wire `get_blob` into the prompt path until that contract is enforced.

Scoping (2026-06-09 implementation review): trace `output_ref`s are **JSON-canonical**
content addresses — `putBlob` / `SessionStore.put_blob` serialize with
`json.dumps(sort_keys=True)`, so they are deliberately a *separate ref-space* from the wire
codec's refs (`codec.py` addresses raw Temporal `Payload` protobuf bytes). Non-JSON
observations are rejected loudly (the `TypeError` propagates) rather than silently coerced.
Revisit only if byte-lossless trace refs are ever needed.

## Migration path (revised)

1. **Codec / Temporal External Storage + the blob-durability contract.** This is the size
   fix and it is the gating correctness work. Ships the headline win (no payload-limit
   overflow) and establishes immutable, content-addressed, retained, integrity-checked blob
   semantics. Nothing below is safe without it.
2. **Confirm event-count coverage.** `should_continue_as_new` covers `AgentWorkflow`; decide
   whether `FlowWorkflow` (`harness.py:447`) needs a batching/CAN seam.
3. **Then decide on `SessionStore`** — purely on queryability / cross-runtime / ownership
   grounds, with the `session_id ↔ workflow-id` fencing, `(session_id, base, state_hash)`
   commit idempotency, and the versioned state envelope. Swap `AgentInput.state` →
   `state_cursor`.
4. **Context fidelity** — populate `*_ref`, resolve observations via `get_blob`. The only step
   that improves agent *quality*, not just durability; gated on step 1's contract.

Steps 1–2 are the real durability fix and are independently shippable. Step 3 is a product
call, not a size necessity. Step 4 is a quality improvement on top.

## Step 2 — event-count assessment (FlowWorkflow)

`should_continue_as_new` (`agent_loop.py:290`) bounds history *event count* for
`AgentWorkflow` — now reached both on the legacy in-payload path and, under the
`SessionStore`, through the `state_cursor` seam (`commitState` at the CAN boundary, then
`continue_as_new(state_cursor=cursor)`). `FlowWorkflow` (`harness.py:447`) has **no**
continue-as-new at all: a flow that fans out many activities and/or child workflows
accumulates events monotonically within one run and can approach the 51,200-event / 50 MB
history hard limit. The claim-check codec does **not** help here — it shrinks per-event
*bytes*, never the event *count*. This is a real but separate gap: it is not a payload-size
problem (the size fix is shipped) and it does not touch the agent loop. Recommendation: track
a batching-or-CAN seam on the flow path (e.g. chunk fan-out into bounded child batches, or add
a `should_continue_as_new`-style boundary to `FlowWorkflow`) as a distinct follow-up, scoped
and prioritized on observed flow fan-out, not bundled into the durable-session work.

---

## Appendix — codex review findings (gpt-5.5, 2026-06-08)

Verbatim priorities from the adversarial review that prompted this revision; retained for
traceability.

- **[P0]** Codec story was internally inconsistent: a transparent codec decodes before app
  code, so the workflow does not "see a pointer" at `state.last = out`. → fixed; "What
  actually overflows today".
- **[P0]** A codec also offloads the continue-as-new `state.to_json()` and the whole
  `InvokeReasonerInput`, so it largely subsumes the *size* rationale for `SessionStore`;
  queryability/cross-runtime survive as architecture reasons only. → fixed; thesis + "Optional".
- **[P0]** "Replay rebuilds state from history" needs immutable, retained, integrity-checked
  blobs; GC/overwrite breaks replay. → fixed; "blob-durability contract".
- **[P0]** CAS by `(session_id, base)` is incomplete for concurrent runs; needs workflow-id /
  fencing uniqueness. → fixed; invariant 1.
- **[P1]** Crash-mid-commit idempotency needs a concrete key — `(session_id, base, state_hash)`.
  → fixed; invariant 2.
- **[P1]** Per-round reasoner input (`harness.py:649`) is not shrunk by a CAN-time store. → fixed;
  table + "does not fix".
- **[P1]** Terminal result (`agent_loop.py:295`) returns `output` + full trace; CAN-time store
  never sees it. → fixed; table + codec scope.
- **[P1]** `get_blob` in `invokeReasoner` changes retry semantics. → fixed; "Context fidelity"
  caveat.
- **[P1]** Sibling `FlowWorkflow` path has no continue-as-new (event-count). → fixed; table +
  "does not fix" + migration step 2.
- **[P1]** Blob lifecycle/GC/security/tenancy missing. → fixed; contract (4)-(5).
- **[P1]** Stored `AgentState` has no schema/version envelope. → fixed; invariant 3.
- **[P2]** Temporal limit wording imprecise ("warn 256 KB" not Cloud-authoritative). → fixed;
  "The constraint".
- **[P2]** "Workflow cannot touch the store" → more precisely, ambient I/O in workflow code is
  replay-unsafe. → fixed; "Activities" note.
- **[P2]** Anchor drift: call-path `state.last=out` is `harness.py:702` (`:733` is sub);
  `callTool` return is `activities.py:155`; `recall`/`append` are `algebra.hs:207-208`
  (`:161` is `Tools`). → all corrected throughout.
