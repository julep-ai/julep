# Long-lived sessions for `composable_agents` — design

**Date:** 2026-06-23
**Status:** Design converged in brainstorming; reviewed by Codex three times (1st: 7 findings folded in; 2nd: recv-guard / truncation / fence / placement / lifecycle / backpressure tightened to checkable rules; 3rd: all six confirmed closed, plus output-buffer retention + `EVAL_PLAN`-in-`LOOP` fixed). **Post-build reconciliation (2026-06-23):** M1 (local/in-memory core) landed on `main`; §6 durability rewritten to build on the **pre-existing** `execution/session_store.py` (`SessionStore` cursor-CAS + `ClaimCheckCodec` + `BlobStore`) rather than reinvent it — see §6, §10, §12
**Scope:** A first-class **session** primitive — a long-lived, keep-messaging-it agent with a streaming event surface — added to `composable_agents` *as a layer around the existing flow IR*, not a new runtime. Builds the **turn-based** core now, with a pre-built channel + scope substrate so a later **reactive/actor** upgrade is additive. Unifies three mechanisms that exist today but don't compose: `human_gate` (signal-wait), `continue_with`/`run_chained` (the continuation trampoline), and `CMASession.events()` (the live event stream).

---

## 1. Goal

Today a flow is a **one-shot arrow** `a → b`: `interpret` (`execution/interpreter.py`) folds a finite IR tree to a single value. "Staying alive" is faked three different, non-composing ways:

- **`human_gate`** (`ir.py` `HUMAN_GATE_TOOL`, `derived.py`) — an internal `await`, lowered to a Temporal signal + `wait_condition` (`execution/harness.py` `_await_human`/`submitHuman`/`openGates`). Resumes in place, but it is one gate keyed by one `cid`, not an input port you keep posting to.
- **`continue_with` / `run_chained`** (`continuation.py`) — a top-level trampoline (Temporal `continue_as_new`). The carrier is an **untyped** `{"__continue__": v}` dict, and continuation drops the inbox.
- **`CMASession`** (`execution/cma.py`) — a live `events()` stream + `tool_result`/`cancel`, but only on the CMA backend, disjoint from the durable-flow side.

The goal: one algebraic object — a **session** — that subsumes all three, so a user can open a long-lived agent, keep sending it messages, and stream its events, on the same local/CMA/Temporal backends as `run_agent`.

## 2. The algebra (why the design is shaped this way)

A flow is the **initial algebra** `μF` of the finite polynomial functor `F` whose summands are the existing ops (`IDENT | ARR | PRIM | SEQ | PAR(merge) | ALT | EACH | ITER_UP_TO | EVAL_PLAN | APP`). `interpret` is a **monadic catamorphism**: fold the tree to one value, effects behind `Env`.

A long-lived session is the **categorical dual** — the **final coalgebra** `νG` (equivalently the free monad) of an *interaction functor*:

```
G X  =  Done(a)            -- terminate with a value
      | Await(i → X)        -- block for the next message, resume with it
      | Yield(o, X)         -- emit an event, keep going
```

Equivalently a **Mealy machine** over an `Event` sum with a `Cmd` output. The state carrier is **ArrowLoop** (the *trace* of the category) — feedback of a typed `d`-channel — made **productive/causal** by guarding the feedback with the `Await` (`recv`). The unrestricted, instantaneous knot (`mfix`-style) is **forbidden**: it is unsound in a strict, effectful, replay-deterministic, content-hashed setting. Only delay-guarded loops are legal. `ITER_UP_TO` is the *bounded* guarded trace; a **session is the unbounded, `recv`-guarded trace**.

The three existing mechanisms are three projections of this one object: `human_gate` = `Await`, `CMASession.events()`/projection `DID` = `Yield`, `run_chained` = the anamorphism (the unfold), already present but at whole-flow granularity with an untyped carrier.

## 3. Decisions (locked in brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| Interaction model now | **Turn-based** (strictly alternating `recv`/work/`emit`) | Covers ~all "keep messaging a live agent" use cases; deterministic with no new concurrency. |
| Future-proofing | **Pre-build the channel + scope substrate** | Reactive/actor upgrade becomes *additive* (widen sums, lift restrictions, implement cancel) instead of a rewrite. |
| Core factoring | **Session wraps flow** — cata inside, ana outside | A *turn* is an ordinary flow; `interpret` is reused verbatim; the session is a thin driver generalizing `run_chained`. |
| Loop representation | **`Op.LOOP` as an `AGENT`-shaped IR boundary** | Keeps the loop inside the content-hashed tree (analyzer/projection/replay keep working) while `surface_shape` stays decidable — opaque like `APP`. (Codex #3.) |
| State carrier | **Explicit, typed** (the ArrowLoop `d`-channel) | Rides `continue_as_new` as plain data; replaces the untyped `{"__continue__": …}` sentinel. |
| Concurrency fence | **`recv`/`emit`/`LOOP` are sequential-position only** | Under `par`/`each`/`race`/`alt` there is no turn linearization (Codex #1). Validation forbids it; `recv` is a scheduling barrier. |
| Delivery | **FIFO-by-seq per channel; `recv`/`emit` non-retryable; `emit` carries a seq/idempotency key** | At-least-once transport becomes effectively-once; no duplicate events under retry (Codex #4, #6). |
| Durability across truncation | **`continue_as_new` carries `(typed state, channel buffers, seq cursors)`** | The current path drops the inbox; buffers must be durable and ordered (Codex #2). |

### Rejected / deferred
- **Reactive/actor now** (messages interrupt in-flight work) — deferred; only its *types* are pre-built (see §9).
- **Loop in the driver only, not in the IR** — rejected; forfeits the "the tree is the only thing everyone agrees on" invariant (`ir.py:3`).
- **Implicit carrier** (suspended-stack state, no declared type) — rejected as the primitive; offered only as compile-to-typed-carrier sugar (§5).

## 4. Architecture — catamorphism inside, anamorphism outside

```
   SESSION (the unfold / anamorphism)          ── new, thin ──
   ┌─────────────────────────────────────────────────────────┐
   │  s0 ─▶ recv(ch_in) ─▶ ┌──────────────────────┐ ─▶ emit ─▶│─▶ ch_out
   │   ▲                   │  one TURN = a flow    │  (state)  │
   │   └────── loop carrier (typed s) ◀── interpret(...) ◀─────┘
   └─────────────────────────────────────────────────────────┘
                            ▲
                            │  catamorphism — UNCHANGED
                 execution/interpreter.py::interpret
```

- **Inner (untouched):** a turn is a finite flow tree, folded by `interpret`. Determinism, content-hashing, contracts, projection — all unchanged.
- **Outer (new):** a driver `drive_session` (generalizing `continuation.run_chained`) does `recv → interpret(turn) → emit*`, threads the typed carrier, parks on the next `recv`.

## 5. IR surface (minimal)

1. **`Op.LOOP`** — the unbounded, `recv`-guarded sibling of `ITER_UP_TO`. Carries `body` (the turn flow) and a **typed state schema** for the carrier. **`surface_shape(LOOP) = AGENT`** — an opaque boundary like `APP`, so shape analysis stays decidable. **Placement (v1):** `LOOP` is permitted **only at a session root** — never inside `EVAL_PLAN`, never as an `APP`/`sub` capability, never under another `LOOP`. `FlowWorkflow` **rejects** a frozen artifact that contains `LOOP` (it has no channel machinery and would hang — Codex 2nd-pass); only `SessionWorkflow` runs it. Nested sessions are deferred (§9). Productivity is enforced by the recv-guard rule (§7.1).
2. **`__recv__` / `__emit__`** reserved native tools, beside `HUMAN_GATE_TOOL`/`SLEEP_TOOL` (`ir.py:28-33`), special-cased in `_eval_prim` exactly as those two are (`interpreter.py:306-319`). Both carry an explicit **non-retryable** contract; `__emit__` additionally carries a seq/idempotency key.
3. **`ChannelRef`** — a typed port reference modeled on `ToolRef` (`ir.py:75`): a name + a payload schema. Frozen into the manifest like tool refs.
4. **`recv(ch)` / `emit(ch, x)`** leaf constructors in `derived.py`, beside `human_gate`/`delay`. **`human_gate(prompt)` becomes sugar for `recv` on a built-in `"human"` channel.**

**Authoring surface (`define` / `typed`).** The primitive is the explicit typed carrier:

```python
@flow
def turn(state: ChatState, msg: UserMsg) -> tuple[ChatState, AgentReply]:
    reply = think("assistant")(render(state, msg))
    return state.append(msg, reply), reply

chat: Session[UserMsg, AgentReply] = scan(turn, init=ChatState.empty())
```

`@session` coroutine sugar compiles to `Op.LOOP` + `__recv__`/`__emit__`; loop-carried locals are **lifted into the typed carrier** by the compiler (same "DSL emits IR" path used elsewhere):

```python
@session
async def chat(s):
    state = ChatState.empty()           # lifted into the LOOP state schema
    while True:
        msg = await s.recv()
        reply = await think("assistant")(render(state, msg))
        await s.emit(reply)
        state = state.append(msg, reply)
```

> **Carrier-lifting is a known risk (Codex MAJOR #5).** v1 ships the explicit `scan`/`loop` primitive as the *supported, enforced* surface. The coroutine sugar is gated behind the compiler being able to prove which locals cross a `recv` boundary and lift them into the declared state schema; until that analysis is solid, the sugar is opt-in/experimental and the typed schema on `Op.LOOP` is the source of truth.

## 6. State & durability — built on the existing `SessionStore`

> **Reconciliation (2026-06-23): this section originally designed durability from scratch. It now builds on `composable_agents/execution/session_store.py`, which already existed on `main` (commit `007db86`) and implements exactly this substrate** — surfaced only after M1 landed. M2 *wires* the session loop to it; it does not reinvent it.

The pre-existing layer provides: `SessionStore` — `load(session_id, cursor)` / `commit(session_id, base, state, state_hash)` with **compare-and-swap on a monotonic `Cursor` for crash-recovery idempotency**, and `session_id`↔Temporal-workflow-id **1:1** (so mutual exclusion is Temporal's job); `ClaimCheckCodec` — oversize-payload offload; `BlobStore` — content-addressed, tenant-scoped. The carrier maps onto it directly:

| Spec concept | Existing mechanism |
|---|---|
| segment / epoch counter | the store's `Cursor` (no separate epoch) |
| persist carrier across `continue_as_new` | `SessionStore.commit(session_id, base, state, hash)` |
| rehydrate after truncation | `SessionStore.load(session_id, cursor)` |
| truncation-boundary dedup / idempotency | the store's **cursor compare-and-swap** (`base != head` ⇒ `CursorConflict`; a re-applied committed write returns the original cursor) |
| oversize carrier / channel buffers | `ClaimCheckCodec` + `BlobStore` (keeps the Temporal payload under limit; cf. §7.4) |

The carrier itself is serialized into an `agent_loop.AgentState`-shaped record (extended for the typed `s` + channel buffers). With that mapping fixed, the typed carrier still makes durability fall out of two mechanisms, each used where it is strong:

- **Within a turn / awaiting the next message** → `wait_condition` on the channel buffer (`harness.py:834`). Keeps history; resumes in place. (This is `human_gate`'s carrier — the suspended stack.)
- **Across history truncation (long-lived sessions)** → the session is one durable workflow that loops; at a history threshold it `continue_as_new`s. The carrier `(typed state s, per-channel buffers, seq cursors)` is **persisted via `SessionStore.commit` and rehydrated via `SessionStore.load`** at the new segment's `Cursor`; the same data also flows through the `continue_as_new` input for the hot path, with the store as the durable backstop. `continue_as_new` drops history — which is exactly why the carrier must be explicit serializable data. (This is `continue_with`'s carrier, now typed, inbox-complete, and store-backed.)

**Buffer durability is mandatory (Codex BLOCKER #2).** The current inbox is in-memory and continuation carries only input/call-counts (`harness.py:1058`), so pending messages would be lost across truncation. The session workflow must keep channel buffers as durable workflow state and include them (with seq cursors) in the continue-as-new input.

**Truncation-boundary protocol (Codex 2nd-pass BLOCKER).** `continue_as_new` is not atomic w.r.t. inbound signals/updates, so the boundary needs an explicit protocol:

1. **Epoching.** The store's monotonic `Cursor` *is* the segment index (no separate epoch). Every buffered item is keyed `(cursor, channel, seq)`.
2. **Quiesce, then continue.** Truncation is only initiated at a turn boundary — i.e. while parked in a top-level `recv` with **no turn in flight**. A `LOOP` is never truncated mid-`body`. This removes the "parked-recv-mid-turn" race: the only parked waiter at truncation is the top-level `recv`, whose buffered+unconsumed items are carried verbatim.
3. **Drain into carry.** Before `continue_as_new`, all buffered items (consumed cursor + tail) are serialized into the continuation input; the new segment rehydrates them under `epoch+1`.
4. **Dedup.** The store's **cursor compare-and-swap** makes a boundary-straddling commit idempotent — a retried committed write returns the original cursor, a stale `base` raises `CursorConflict` (`session_store.py:96`). A `send` (Temporal Update, §7.5) re-applied across the boundary, and consumers draining emits, still dedup by `(channel, seq)`; late signals addressed to the closed run are redelivered by Temporal to the new run and deduped the same way.

## 7. Concurrency, delivery, and ordering

### 7.1 Productivity — the recv-guard rule (Codex 2nd-pass BLOCKER)

"First effect is a `recv`" is not checkable on a tree with `SEQ`/`ALT`/`PAR`/`EACH`. The precise, decidable rule, checked in `validate.py` over the `LOOP` body:

> **`recv_guarded(body)` holds iff every control-flow cycle back to the loop head passes through at least one `recv`.** Because the body is itself a finite acyclic tree (the only back-edge is the implicit loop), this reduces to: **on every root-to-leaf path of `body`, there is at least one `recv` node, and no `emit` precedes the first `recv` on that path.**

- "Every path has a `recv`" ⇒ the loop cannot iterate without consuming input (no busy-spin, no unbounded emit-only history).
- "No `emit` before the first `recv` on a path" ⇒ a turn cannot emit before it has received, keeping the `recv`/`emit` alternation well-formed.
- `ALT` is path-splitting: **every** branch must independently satisfy the rule (so a conditionally-skipped `recv` is rejected). This is decidable by a single post-order walk classifying each node as *contains-recv-on-all-paths* / *emits-before-recv*.
- **`EVAL_PLAN` / `ITER_UP_TO` inside a `LOOP` body (Codex 3rd-pass):** the walk only sees static trees, so **only baked `EVAL_PLAN`** (plan statically present in the IR) is permitted inside a `LOOP` — the walk descends into the baked plan normally. The **controller / runtime-compiled** form of `EVAL_PLAN` is **rejected** inside a `LOOP` (its plan isn't visible to static validation, so productivity can't be proven). `ITER_UP_TO` bodies are walked normally (bounded + sequential), and an `ITER_UP_TO` does **not** by itself satisfy the guard for the enclosing `LOOP` — the `recv` must be reachable on the `LOOP`'s own paths.

### 7.2 Sequential-position fence (Codex BLOCKER #1, relaxed in 2nd pass)

`recv`/`emit`/`LOOP` are legal only where a turn stays linearizable:

- **Forbidden under `PAR` / `EACH` / `race`/`hedge`/`quorum` merges** — true concurrency means multiple outstanding receives with no defined order (`interpreter.py:348`).
- **Allowed under `ALT`** — branch selection is sequential and exactly one branch runs, so a conditional `emit`/`recv` is sound (Codex 2nd-pass MAJOR: the original blanket ban on `alt` rejected legitimate conditional emits). The `ALT` case must still satisfy §7.1 per-branch.
- **Allowed under `SEQ` and `ITER_UP_TO`** (bounded, sequential).

Enforced in `validate.py` alongside the whole-session degradation rule (`validate.py:426`); `recv` acts as a scheduling barrier.

### 7.3 Ordering & seq assignment

Per channel, **FIFO by server-assigned `seq`** (not arrival time) — replay-stable across `continue_as_new`. **The workflow assigns the canonical `seq`** on accepting a `send`; a client may attach an `idempotency_key` (distinct from `seq`) used only for dedup. This removes the client-vs-server ambiguity (Codex 2nd-pass MINOR).

### 7.4 Delivery — `emit` is a workflow-internal append, not an activity

`emit` does **not** call out over the network (so it cannot be retried into a duplicate, Codex MAJOR #4). It **appends to a durable, seq'd output-channel buffer in workflow state**; external consumers (`SessionHandle.events()`) drain that buffer via query/streaming. Therefore `emit` is deterministic and replay-safe by construction. `recv`/`emit` carry explicit **non-retryable** contracts and do **not** inherit the call-retry loop (`interpreter.py:320`) nor any activity `RetryPolicy` (`harness.py:269`). The transport from buffer to a remote consumer is at-least-once; consumers dedup by `(channel, seq)`, making it **effectively-once**.

**Output-buffer retention (Codex 3rd-pass).** The output buffer is bounded and drained against a per-consumer **ack cursor**: `SessionHandle.events()` acks the highest `seq` it has delivered, and the workflow evicts every item `≤` the ack cursor — so steady-state buffer size is bounded by in-flight (un-acked) events, not by session lifetime. If the buffer fills (slow/absent consumer), `emit` **parks on `wait_condition` until space frees** — durable and replay-safe, symmetric with input backpressure (§7.5) — and the high-watermark is surfaced via `state()` so a stuck/unconsumed session is observable rather than silently growing history. v1 is **single-consumer per handle**; multi-consumer fan-out (which complicates the ack cursor) is deferred (§14.5).

### 7.5 `send` and backpressure — Temporal Update, not signal

A Temporal **signal is fire-and-forget and cannot backpressure the sender**, so `send` is a **Temporal Update** (synchronous result, can reject). Per-channel bounded buffer:

- buffer has room → append, return assigned `seq` (ack);
- buffer full → reject the Update with a typed `ChannelFull` error (caller retries/backs off) — never a silent drop, never a blocked workflow.

`open_receives()` and a `capacity` field on `state()` surface buffer depth so clients can pace themselves.

## 8. Downstream API

**Runtime / consumption — the Agent facade.** A `SessionHandle` sibling of `arun`/`deploy` (`agent.py:400+`):

```python
handle: SessionHandle = await agent.open(session=chat, backend="temporal")
await handle.send(UserMsg("hi"))
async for ev in handle.events():     # streaming events
    render(ev)
snap = await handle.state()          # projection/query snapshot
await handle.close()
```

`SessionHandle` **generalizes `CMASession`** (`cma.py:77` already has `events()`/`cancel()`), unified with the Temporal side: `submitHuman` → `send`, `openGates` → `open_receives() -> [{channel, cid, seq}]` (Codex MINOR #7), `projection` → `state`. Backends: **local / CMA / Temporal**, mirroring `run_agent`.

**`SessionEvent` contract & lifecycle (Codex 2nd-pass MAJOR).** `CMAEvent` (`cma.py:46`) is a *terminating* stream — `terminal`/`error` end it — whereas a session is non-terminating, so the unification needs an explicit common contract:

```
SessionEvent = Emit(channel, seq, payload)   # a value the session emitted
             | Turn(kind: "started"|"done")  # turn boundary marker
             | Error(reason, fatal: bool)     # non-fatal (turn) vs fatal (session)
             | Closed(reason)                 # terminal — the ONLY thing that ends events()
```

- `events()` yields until `Closed`; it does **not** end on a turn completing (the key difference from CMA's `terminal`).
- `close()` → `Closed`; on the CMA backend it maps to `CMASession.cancel()`.
- A CMA `terminal` is adapted to `Turn("done")`, a CMA `error` to `Error(fatal=…)`.

**CMA backend scope.** Because a CMA managed-agent session runs to a terminal, a multi-turn `Session` on CMA is modeled as **one CMA session per turn** (open → run → terminal → adapt to `Turn("done")` → await next `recv` → reopen). This per-turn mapping is **v1.5**; v1 ships `local` + `Temporal` (natively multi-turn) only.

**CLI (`ca`).** The deferred §9 interactive surface of `docs/superpowers/specs/2026-06-22-composable-agents-cli-design.md` is **unblocked** by this primitive (it was deferred precisely because sessions didn't exist): `ca chat <agent>` opens a `SessionHandle` and REPLs send/recv against the live terminal trace; `ca listen --forward-to URL` / `ca trigger <event>` drive a session's input channel from external events. They reuse the existing selector grammar, terminal trace tree, and Langfuse deep links — no new CLI concepts. `ca run` stays the one-shot (`arun`) verb; `ca chat`/`ca listen` are the session (`open`) verbs.

## 9. The reactive upgrade path (types pre-built, machinery deferred)

Everything reactive-only exists now as an **open type**, not built code. The upgrade is: widen two sums + lift two restrictions + implement cancel.

| Seam | Turn-based now | Reactive later |
|---|---|---|
| `Event[i]` (loop wake sum) | `Msg(i)` arm only | widen: `+ EffectDone + Timer` |
| `Cmd` (session-level command output) | empty (effects happen inline in the turn flow via `Env`) | widen: `+ Spawn + Cancel` |
| `Channel` ops | `recv` (blocking take) only | add `select` / `try_recv` |
| reaction scope | each turn wrapped in a **no-op** Temporal cancellation scope | implement cancel; foundation = existing idempotency contracts (`interpreter.py:103` `_retry_attempts_for_call` / `contract_allows_retry`) |
| channel topology | external only (user ↔ session) | session ↔ session channels |

The one capability not pre-built for free is **interruption/barge-in** — turn-based has no in-flight work to cancel. Its two prerequisites already exist: cancellation *scoping* (the no-op wrapper, cheap now, brutal to retrofit) and cancellation-*safe* effects (the idempotency contracts).

## 10. Code map

**Add:**
- `session.py` — `Channel`, `Session`, `scan`/`loop` sugar, `drive_session` (the unfold; generalizes `continuation.run_chained`).
- `ir.py` — `Op.LOOP`, `__recv__`/`__emit__` reserved names, `ChannelRef`, `LOOP` state schema.
- `derived.py` — `recv`/`emit` leaves; `human_gate` re-expressed over `recv`.
- `interpreter.py` — two reserved-tool branches in `_eval_prim`; `Env.recv`/`Env.emit`; `LOOP` case in `_eval` (shape=AGENT, recv-guarded).
- `validate.py` — sequential-position fence for `recv`/`emit`/`LOOP`; `LOOP`-not-in-`eval_plan`; recv-guard productivity check.
- `shapes.py`, `transforms.py` — handle `Op.LOOP` (shape `AGENT`; transform passthrough).
- `InMemoryEnv` — channel fakes for tests.

**Reuse (do NOT reinvent — pre-existing, surfaced after M1):**
- `execution/session_store.py` — `SessionStore` (cursor-CAS) is the durable carrier persistence (§6). M2 commits/loads the carrier here.
- `execution/codec.py` — `ClaimCheckCodec` for oversize carrier/buffers.
- `execution/blobstore.py` — `BlobStore` content-addressed backing.
- `agent_loop.py` — `AgentState` / `state_fingerprint` is the shape the carrier serializes into.

**Generalize (M2):**
- `execution/harness.py` — `FlowWorkflow` → `SessionWorkflow`: N typed channel inboxes (not one `_human_inbox`); loop holding typed `s`; threshold `continue_as_new` with the carrier **persisted through `SessionStore.commit`/`load`** (cursor = segment index); `submitHuman`→`send` (Update), `openGates`→`open_receives`, `projection`→`state`. `FlowWorkflow` rejects `Op.LOOP`.
- `agent.py` — `Agent.open(...) -> SessionHandle`; `SessionHandle` generalizing `CMASession`.

**Untouched:** `interpret` core and every arrow combinator, `freeze`/content-hash, contracts core, projection core.

**Status:** M1 (`session.py`, `ir.py` Op.LOOP/ChannelRef, `interpreter.py` recv/emit/LOOP + InMemoryEnv, `validate.py` rules, `derived.py`, `shapes`/`transforms`) **already landed on `main`** (commits `e13d1fe`, `ea9ddca`, `5e8b372`) and is in green-up/review.

## 11. Codex review — findings → resolutions

| # | Sev | Finding | Resolution |
|---|---|---|---|
| 1 | BLOCKER | `recv`/`emit` under `par`/`each`/`race` has no turn linearization | §7.2 sequential-position fence in `validate.py`; `recv` is a barrier (`alt` allowed, §7.2) |
| 2 | BLOCKER | `continue_as_new` drops the in-memory inbox | §6 durable buffers + seq cursors carried in continuation input |
| 3 | MAJOR | `Op.LOOP` fights the finite-tree invariant; race/hedge/quorum are merge markers, not ops | §5 `LOOP` is an `AGENT`-shaped boundary, forbidden in `eval_plan`; `shapes`/`transforms`/`validate` updated |
| 4 | MAJOR | `recv`/`emit` would inherit retry → duplicate emits | §7 explicit non-retryable contracts; `emit` seq/idempotency key |
| 5 | MAJOR | "Typed carrier" not enforceable today (untyped sentinel) | §5 typed state schema on `Op.LOOP`; `scan`/`loop` is the enforced primitive, coroutine sugar gated on lifting analysis |
| 6 | MINOR | Ordering/backpressure unspecified | §7 FIFO-by-seq, bounded buffers, defined backpressure |
| 7 | MINOR | Signal/query surface hardcoded to human gates | §8 generalized `send` / `open_receives() -> {channel, cid, seq}` |

### Second pass (resolutions tightened from named → checkable)

| Concern | Sev | Resolution |
|---|---|---|
| recv-guard "first effect is recv" not checkable on `SEQ`/`ALT`/… | BLOCKER | §7.1 decidable `recv_guarded(body)`: every path has a `recv`, no `emit` before first `recv`, per-branch under `ALT` |
| `continue_as_new` boundary races (signal mid-continue, parked recv, cursor drift) | BLOCKER | §6 epoch + quiesce-at-turn-boundary + drain-into-carry + `(channel,seq)` dedup |
| fence over-forbids `alt` (blocks conditional emit) | MAJOR | §7.2 `alt` allowed when branches are sequential; only `par`/`each`/`race` banned |
| `LOOP` could reach `FlowWorkflow` and hang | MAJOR | §5 `LOOP` session-root-only; `FlowWorkflow` rejects it; nested sessions deferred |
| `SessionHandle` vs `CMASession` lifecycle (CMA terminates, sessions don't) | MAJOR | §8 `SessionEvent` contract; `events()` ends only on `Closed`; CMA = one session per turn, v1.5 |
| backpressure "send blocks" conflicts with fire-and-forget signals | MINOR | §7.5 `send` is a Temporal **Update** (ack/reject `ChannelFull`); server-assigned `seq` |

### Third pass (all six above confirmed CLOSED; two follow-ups from the edits)

| Concern | Resolution |
|---|---|
| `emit`'s durable output buffer had no retention policy → unbounded state | §7.4 per-consumer **ack cursor** + evict-`≤`-acked + park-on-full; high-watermark in `state()` |
| controller-form `EVAL_PLAN` inside a `LOOP` is invisible to the static `recv_guarded` walk | §7.1 only **baked** plans allowed in a `LOOP` body; controller/runtime-compiled `EVAL_PLAN` rejected there |

## 12. Milestones

**M1 — local / in-memory core — LANDED + GREEN on `main` (`e13d1fe`,`ea9ddca`,`5e8b372`,`64f82de`).** `Op.LOOP` (AGENT-shaped) + `ChannelRef` + `__recv__`/`__emit__`; `scan`/`loop` primitive; sequential-position validator + recv-guard check; `drive_session`; `InMemoryEnv` channels; `human_gate` (still a distinct leaf — recv-unification deferred). Green-up (`64f82de`) fixed: `to_json` channel-drop, freeze rejecting recv/emit, spurious FAILED span on clean close, async-test convention; added `click` to core deps. pytest 1322 passed, mypy clean.

**M1.5 — make the carrier real + enforce safety (NEXT — deferred BLOCKERs from M1 review).**
- **Carrier threading (BLOCKER).** Today `recv` discards the threaded carrier, so state doesn't thread (the accumulator test passes only via an external closure). **Decision:** a LOOP turn is the step `(carrier, msg) → (carrier', outputs)`; the LOOP **driver owns the boundary `recv`**, forms `(carrier, msg)` as the step input, and splits the step result into `(carrier', outputs)`. `drive_session` and the interpreter `Op.LOOP` case must both implement this *one* driver (resolving the "two divergent drivers" finding). `scan(step, init)` is exactly this; the `@session` coroutine's first `recv` is the boundary, loop-carried locals are the carrier.
- **Flow-vs-session target gate (BLOCKER).** `validate()` must classify a flow: `FlowWorkflow`-targeted rejects any `LOOP`/`recv`/`emit`; session-targeted requires a root `LOOP` and forbids stray `recv`/`emit`. At minimum, reject `recv`/`emit` outside a `LOOP`.
- **Enforce at build (MAJOR).** Run the session `validate()` subset inside `loop()`/`scan()` (and/or freeze) so the recv-guard/fence/placement rules actually gate, not just lint.

**M2 — durable Temporal sessions (next).** `SessionWorkflow` wired to the **existing** `SessionStore` (carrier via `commit`/`load`, cursor = segment index) + `ClaimCheckCodec` for oversize; N typed channel inboxes; `send` as Temporal Update; `open_receives`/`state` queries; `FlowWorkflow` rejects `LOOP`; `Agent.open` + `SessionHandle` on **local** + **Temporal**. This is durability *wiring*, not a new store.

**M3 — facade + CMA.** CMA backend for `SessionHandle` (one-session-per-turn, unify `CMASession`); `@session` coroutine sugar (carrier lifting); `ca chat`.

**Deferred (reactive / north-star):** `Event`/`Cmd` widening, `select`/`try_recv`, cancellation implementation, session↔session channels; `ca listen`/`ca trigger`.

## 13. Non-goals

- No new execution backend or durability layer — sessions reuse Temporal/DBOS/CMA and the existing projection plane.
- No reactive/actor semantics in v1 (no mid-turn interruption); only the seams are pre-typed.
- No change to the one-shot flow/arrow semantics or `interpret` core.
- No bundled web UI — the CLI terminal surface + Langfuse deep links remain the observability story.

## 14. Open questions (for the plan / review)

1. **Carrier lifting** — how much loop-carried-local analysis does the `@session` sugar attempt in v1.5, and what's the fallback diagnostic when it can't prove liftability? (Leaning: require explicit `scan` and emit an actionable "declare your state" error.)
2. **History-truncation threshold** — fixed event-count, size-based, or Temporal's `continue_as_new_suggested`? (The *boundary semantics* are resolved in §6; this is only the policy knob for *when* to truncate.)
3. **Channel payload typing** — reuse the JSONSchema + shape machinery (`SubContract`-style) for `ChannelRef`, or a lighter typed envelope?
4. **`state()` consistency** — is the query a pure projection snapshot (derived, like `projection`) or does it expose the typed carrier `s` directly? (Leaning: both — projection for observability, an opt-in typed `s` read for resumable clients.)
5. **Multi-consumer events** — is `events()` single-consumer per handle, or fan-out (multiple observers of one session)? Affects seq/cursor bookkeeping.
