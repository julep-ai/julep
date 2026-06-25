# Sessions — long-lived, keep-messaging agents

A **flow** is a one-shot arrow: it consumes one input, runs the frozen IR to completion, and returns one value. A **session** is its long-lived counterpart — you open it once, keep sending it messages, and stream its events back, while it threads state across turns. Sessions run on the **same** frozen-IR control plane as flows (same interpreter, same capability/budget guards, same projection), on three backends: in-memory **local**, durable **Temporal**, and Anthropic **CMA** (Claude Managed Agents).

> The design rationale (a session is the recv-guarded `Op.LOOP` — the unbounded, await-guarded sibling of `iter_up_to`; cata-inside / ana-outside) lives in the design spec: [`docs/superpowers/specs/2026-06-23-upgradeable-sessions-design.md`](superpowers/specs/2026-06-23-upgradeable-sessions-design.md). The durable carrier store is [`design/durable-session-store.md`](design/durable-session-store.md).

## The shape of a turn

A session is a **turn** run in a loop. Each turn:

1. **`recv`** — block for the next message on an input channel,
2. run an ordinary flow (think/call/tools — the full authoring surface),
3. **`emit`** — push zero or more events to the output channel,
4. thread a typed **carrier** (e.g. the conversation history) to the next turn.

The carrier is the whole point: it is how a session *remembers*. It is the loop-carried state, threaded turn→turn, and persisted across history truncation on the durable backend.

## Authoring a session

Three surfaces, all compiling to the **same** `Op.LOOP` IR:

### `scan` — explicit typed carrier (the primitive)

`scan(step, init)` where the step is a flow `(carrier, msg) → (carrier', output)`:

```python
from composable_agents import scan, think

# turn: fold the new message into the running transcript, reply, thread the transcript
chat = scan(turn_flow, init=[])     # init carrier = empty history
```

The step returns a 2-tuple `(next_carrier, output)`; the loop splits it, threads `next_carrier`, and emits `output`.

### `loop` — carrier-is-body-value (lower-level)

`loop(body, ...)` threads the body's return value as the next carrier; `emit(...)` is a **carrier-transparent tap** (it forwards its input unchanged and sends the payload to the output channel). Use `loop` when the carrier and the emitted value are the same shape.

### `@session` — straight-line coroutine sugar (experimental)

Write the loop as a normal `async` function; it is AST-lifted into the same `Op.LOOP`:

```python
from composable_agents import session

@session
async def chat(s):
    history = []
    while True:
        msg = await s.recv()
        reply = await think_reply(history, msg)   # a real call
        await s.emit(reply)
        history = history + [msg, reply]           # lifted into the typed carrier
```

The compiler lifts every loop-carried local referenced across the `recv` boundary (including `+=`) into the carrier. When it cannot prove liftability (multiple `recv` per turn, closure capture, exotic control flow), it raises `SessionCompileError` telling you to declare the state explicitly with `scan` — it never silently miscompiles.

### Validation rules (enforced at construction)

`loop()`/`scan()` run the session validators and raise `SessionValidationError` on:

- **recv-guard** — every path through the turn must pass through exactly one `recv`, and no `emit` may precede it (a loop must consume input to make progress).
- **sequential-position fence** — `recv`/`emit`/`LOOP` are forbidden under `par`/`each`/`race` (no turn linearization there); `alt` is fine.
- **placement** — `LOOP` only at a session root (never inside `eval_plan`, an `app`/`sub` capability, or another `LOOP`). An ordinary flow containing `recv`/`emit`/`LOOP` is rejected at deploy (`target="flow"`).

## Opening and driving a session

`agent.open(...)` is the session sibling of `arun`/`deploy`, returning a `SessionHandle`:

```python
handle = await agent.open(session=chat, backend="temporal")   # or "local" / "cma"

await handle.send(user_msg)                  # push a message (idempotency_key optional)
async for ev in handle.events():             # stream until Closed
    if ev.is_emit:   render(ev.payload)
    elif ev.is_error: log(ev.reason)         # fatal vs non-fatal
snapshot = await handle.state()              # carrier + projection snapshot
parked   = await handle.open_receives()      # channels currently awaiting input
await handle.close(reason="done")            # terminal; events() ends on Closed
```

`SessionHandle` is the unified surface across all three backends (it generalizes `CMASession`).

### `SessionEvent`

`events()` yields a normalized event and ends **only** on `Closed` (not when a turn completes):

| kind | meaning |
|---|---|
| `Emit(channel, seq, payload)` | a value the turn emitted |
| `Turn(started \| done)` | turn boundary markers |
| `Error(reason, fatal)` | `fatal=False` surfaces a recoverable turn failure and continues; `fatal=True` tears down |
| `Closed(reason)` | the single terminator |

Delivery is effectively-once: the Temporal handle yields first, then lazily acks the previously-delivered `seq`, so a consumer crash can't drop an event. Per-handle `events()` is single-consumer.

## Backends

| Backend | Runtime | Carrier / durability | Use it for |
|---|---|---|---|
| **local** | in-memory `LocalSessionHandle` | threaded in-process | tests, local dev, the inner loop |
| **temporal** | durable `SessionWorkflow` | carrier persisted via `SessionStore` (cursor = segment), survives `continue_as_new`; `send` is a Temporal **Update** (acks, or rejects `ChannelFull`) | production: crash-safe, replayable, long-lived |
| **cma** | one Anthropic managed-agent session **per turn** | **no framework carrier** — the hosted session is fresh each turn; resend transcript for memory | hosted models / tool-use via Anthropic's managed runtime |

All three enforce the same guards: a session is deployed through `target="session"` (capability deny-by-default, `maxCalls`, budget, pure pins), and the durable backend enforces them at runtime exactly like a deployed flow. On CMA, per-turn custom-tool servicing routes through the same enforcement plane as the one-shot CMA path.

> **Statefulness across backends.** local and Temporal thread the carrier natively; CMA does not (it opens a fresh hosted session per turn), so a CMA driver that needs memory resends the running transcript. See `examples/session_demo.py` for the same stateful conversation on all three.

## From the CLI

The `ca` verbs open a local `SessionHandle` over a selected agent:

```bash
ca chat support-agent                       # REPL: type a line, stream Turn/Emit back, exit on Closed
ca trigger support-agent '{"text": "hi"}'   # one-shot: send one event, render the reply
ca listen support-agent --forward-to https://example.com/hook   # forward emitted events to a URL
```

See [`docs/cli.md`](cli.md).

## Worked example

`examples/session_demo.py` drives a real `anthropic:claude-haiku-4-5` stateful conversation (plant a codeword on turn 1, recall it on turn 2 via the threaded carrier) on **every** backend:

```bash
set -a; source .env; set +a            # ANTHROPIC_API_KEY (keys are not shell-exported)
uv run --extra dev --extra providers python examples/session_demo.py local
uv run --extra dev --extra providers python examples/session_demo.py temporal
uv run --extra dev --extra providers --extra cma python examples/session_demo.py cma
```

> **Deploying a session worker remotely:** session pures are content-addressed over their source, so the **worker must register pures from the exact same source file the deploy pins from** — bake the session module into the worker image, or you'll hit `PureDriftError`.

## See also

- [Concepts](concepts.md) — the shape lattice and three planes sessions reuse.
- [Authoring guide](AUTHORING.md) · [CLI](cli.md) · [Deploy to Temporal](deploy-temporal.md)
- Design spec: [`superpowers/specs/2026-06-23-upgradeable-sessions-design.md`](superpowers/specs/2026-06-23-upgradeable-sessions-design.md) · durable store: [`design/durable-session-store.md`](design/durable-session-store.md)
