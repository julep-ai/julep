---
title: "Sessions"
description: "Long-lived keep-messaging agents: open once, send messages, stream events, thread a typed carrier across turns."
---

A **flow** is a one-shot arrow: it consumes one input, runs the frozen IR to completion, and returns one value. A **session** is its long-lived counterpart — you open it once, keep sending it messages, and stream its events back, while it threads state across turns.

Sessions run on the same frozen-IR control plane as flows (same interpreter, same capability/budget guards, same projection), on three backends: in-memory **local**, durable **Temporal**, and Anthropic **CMA** (Claude Managed Agents).

## Quick start

The script below needs no provider key, no Temporal server, and no CLI config. It opens a local session, sends two messages, streams the events, and prints the carried state.

Install the package:

```bash
python -m pip install --pre julep
```

From a repository checkout, use the editable form instead:

```bash
python -m pip install -e .
```

Create and run the script:

```bash
cat > quickstart_sessions.py <<'PY'
from __future__ import annotations

import asyncio
from typing import Any

from julep import Agent, SessionEvent, arr, recv, register_pure, scan, seq


def step(value: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    history = list(value["carrier"] or [])
    msg = str(value["msg"])
    next_history = [*history, msg]
    return next_history, {"reply": f"ack:{msg}", "seen": next_history}


register_pure("quickstart.session_step", step)

chat = scan(
    seq(recv("in"), arr("quickstart.session_step")),
    init=[],
    in_channel="in",
    out_channel="out",
)


async def main() -> None:
    agent = Agent("local-demo", llm=None)
    handle = await agent.open(session=chat, backend="local")
    events = handle.events()

    await handle.send("hello", idempotency_key="turn-1")
    await handle.send("again", idempotency_key="turn-2")

    for _ in range(6):
        event: SessionEvent = await events.__anext__()
        if event.is_turn:
            print(f"turn:{event.turn}")
        elif event.is_emit:
            print(f"emit:{event.channel}:{event.seq}:{event.payload}")
        elif event.is_error:
            print(f"error:{event.reason}:{event.fatal}")

    state = await handle.state()
    print("carrier:", state["carrier"])
    print("pending:", state["pending"])

    await handle.close("done")
    closed = await events.__anext__()
    print(f"{closed.kind}:{closed.reason}")


if __name__ == "__main__":
    asyncio.run(main())
PY

python quickstart_sessions.py
```

Expected output:

```text
turn:started
emit:out:1:{'reply': 'ack:hello', 'seen': ['hello']}
turn:done
turn:started
emit:out:2:{'reply': 'ack:again', 'seen': ['hello', 'again']}
turn:done
carrier: ['hello', 'again']
pending: {'in': 0}
closed:done
```

The `recv("in")` leaf receives one inbound message and passes `{"carrier": current_carrier, "msg": message}` to the next node. `scan(...)` expects the turn body to return `(next_carrier, output)`; it stores `next_carrier` for the next turn and emits `output` on `out_channel`.

## The shape of a turn

Each turn in a session:

1. **`recv`** — block for the next message on an input channel,
2. run an ordinary flow (think/call/tools — the full authoring surface),
3. **`emit`** — push zero or more events to the output channel,
4. thread a typed **carrier** (e.g. the conversation history) to the next turn.

The carrier is how a session remembers. It is the loop-carried state, threaded turn→turn, and persisted across history truncation on the durable backend.

## Authoring a session

Three surfaces, all compiling to the same `Op.LOOP` IR.

### `scan` — explicit typed carrier (the primitive)

`scan(step, init)` where the step is a flow `(carrier, msg) → (carrier', output)`:

```python
from julep import arr, recv, scan, seq

chat = scan(
    seq(recv("in"), arr("my_module.turn_step")),
    init=[],
    in_channel="in",
    out_channel="out",
    state_schema={"type": "array"},
)
```

`scan(step_flow, init, *, in_channel="in", out_channel="out", state_schema=None)` wraps the turn body in a root `Op.LOOP` and marks the result as split: `(carrier, output)`. The step returns a 2-tuple `(next_carrier, output)`; the loop splits it, threads `next_carrier`, and emits `output`.

### `loop` — carrier-is-body-value (lower-level)

`loop(body, *, init, in_channel="in", out_channel="out", state_schema=None)` threads the body's return value as the next carrier. `emit(channel)` appends its input to `channel` and forwards that input unchanged (a carrier-transparent tap). `emit(channel, value="ready")` emits the literal value instead. Use `loop` when the carrier and the emitted value are the same shape.

### `@session` — coroutine sugar (experimental)

Write the loop as a normal `async` function; it is AST-lifted into the same `Op.LOOP`:

```python
from julep import session

@session
async def chat(s):
    history = []
    while True:
        msg = await s.recv()
        reply = await think_reply(history, msg)   # a real call
        await s.emit(reply)
        history = history + [msg, reply]           # lifted into the typed carrier
```

The compiler lifts every loop-carried local referenced across the `recv` boundary (including `+=`) into the carrier. The lifted function must be `async def`, accept exactly one parameter, end with one `while True`, assign the first loop statement from `await s.recv()`, call `await s.emit(...)` exactly once, and avoid other awaits or non-trivial control flow in the loop body.

When the compiler cannot prove liftability (multiple `recv` per turn, closure capture, exotic control flow), it raises `SessionCompileError` telling you to declare the state explicitly with `scan` — it never silently miscompiles.

### Validation rules

`loop()`/`scan()` run the session validators and raise `SessionValidationError` on:

- **recv-guard** — every path through the turn must pass through exactly one `recv`, and no `emit` may precede it (a loop must consume input to make progress).
- **sequential-position fence** — `recv`/`emit`/`LOOP` are forbidden under `par`/`each`/`race`/`hedge`/`quorum`; `alt` is fine.
- **placement** — `LOOP` only at a session root (never inside `eval_plan`, an `app`/`sub` capability, or another `LOOP`). An ordinary flow containing `recv`/`emit`/`LOOP` is rejected at deploy (`target="flow"`).

The IR uses reserved native tools: `recv(...)` lowers to `__recv__`, and `emit(...)` lowers to `__emit__`. The root loop declares its `ChannelRef`s in `channels`.

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

`SessionHandle` is the unified surface across all three backends.

`send(...)` returns `{"seq": <int>, "channel": <name>}`. Reusing the same `idempotency_key` with the same payload returns the original ack; reusing it with a different payload raises.

For lower-level test code, open the local backend directly:

```python
from julep import LocalSessionHandle

handle = await LocalSessionHandle.open(chat, channel_capacity=100)
```

### `SessionEvent`

`events()` yields a normalized event and ends **only** on `Closed` (not when a turn completes). The per-turn order on both local and Temporal backends is:

```text
turn started
emit
turn done
```

| kind | meaning |
|---|---|
| `Emit(channel, seq, payload)` | a value the turn emitted |
| `Turn(started \| done)` | turn boundary markers |
| `Error(reason, fatal)` | `fatal=False` surfaces a recoverable turn failure and continues; `fatal=True` tears down |
| `Closed(reason)` | the single terminator |

`SessionEvent` has `kind`, `channel`, `seq`, `payload`, `turn`, `reason`, and `fatal` fields, plus convenience predicates:

```python
async for event in handle.events():
    if event.is_emit:
        render(event.channel, event.seq, event.payload)
    elif event.is_turn:
        mark(event.turn)          # "started" or "done"
    elif event.is_error:
        log(event.reason, event.fatal)
    elif event.is_closed:
        break
```

`events()` is single-consumer per handle. Delivery is effectively-once: the Temporal handle yields first, then lazily acks the previously-delivered `seq`, so a consumer crash cannot drop an event. On the local backend, delivered emit records are evicted from `state()["emitted"]` as the event stream advances; use `state()` for inspection and debugging.

## Backends

| Backend | Runtime | Carrier / durability | Use it for |
|---|---|---|---|
| **local** | in-memory `LocalSessionHandle` | threaded in-process | tests, local dev, the inner loop |
| **temporal** | durable `SessionWorkflow` | carrier persisted via `SessionStore` (cursor = segment), survives `continue_as_new`; `send` is a Temporal **Update** (acks, or rejects `ChannelFull`) | production: crash-safe, replayable, long-lived |
| **cma** | one Anthropic managed-agent session per turn | **no framework carrier** — the hosted session is fresh each turn; resend transcript for memory | hosted models / tool-use via Anthropic's managed runtime |

All three enforce the same guards: a session is deployed through `target="session"` (capability deny-by-default, `maxCalls`, budget, pure pins), and the durable backend enforces them at runtime exactly like a deployed flow.

### Local

```python
handle = await agent.open(
    session=chat,
    backend="local",
    channel_capacity=100,
)
```

### Temporal

Install the Temporal extra:

```bash
python -m pip install --pre 'julep[temporal]'
```

Open through the facade with a connected Temporal client and a worker polling the same task queue:

```python
from temporalio.client import Client

client = await Client.connect("localhost:7233")
handle = await agent.open(
    session=chat,
    backend="temporal",
    client=client,
    session_id="support-session-42",
    task_queue="support-sessions",
    history_threshold=10_000,
    channel_capacity=100,
)
```

`backend="temporal"` starts `SessionWorkflow` and returns `TemporalSessionHandle`. Its `send(...)` method is a Temporal Update named `send`; the workflow also exposes `close`, `ack`, and `ack_events` updates plus `events`, `open_receives`, and `state` queries.

Run a worker with a `WorkerContext` that includes a session store. `InMemorySessionStore` is process-local and useful for development/tests; replace it with a durable `SessionStore` implementation for production:

```python
from julep.execution.activities import WorkerContext
from julep.execution.session_store import InMemorySessionStore
from julep.execution.worker import run_worker


async def serve() -> None:
    await run_worker(
        task_queue="support-sessions",
        session_store=InMemorySessionStore(empty_value=[]),
        llm=my_llm,
        mcp_call=my_mcp,
    )
```

For a container entrypoint, expose a `WORKER_CONTEXT_FACTORY=module:attr` factory that returns `WorkerContext` and run:

```bash
python -m julep.cli worker \
  --address localhost:7233 \
  --namespace default \
  --task-queue support-sessions \
  --health-port 8080
```

Temporal sessions enforce capability grants, `maxCalls`, pure pins, and cost budgets across turns. The Temporal backend rejects token and wall-clock budget dimensions — it currently enforces only the `cost` dimension.

### CMA

Install the CMA extra:

```bash
python -m pip install --pre 'julep[cma]'
```

Open through the same facade:

```python
handle = await agent.open(
    session=chat,
    backend="cma",
    client=cma_client,
)
```

`CMASessionHandle` is `SessionHandle`-compatible, but it creates one hosted CMA session per inbound turn and does not thread the framework carrier between turns. If the hosted model needs prior context, resend the running transcript in each message.

> **Statefulness across backends.** Local and Temporal thread the carrier natively; CMA does not (it opens a fresh hosted session per turn), so a CMA driver that needs memory resends the running transcript. See [`examples/session_demo.py`](https://github.com/julep-ai/julep-v2/blob/main/examples/session_demo.py) for the same stateful conversation on all three backends.

## From the CLI

The `julep` verbs open a local `SessionHandle` over a selected agent:

```bash
julep chat support-agent                       # REPL: type a line, stream Turn/Emit back, exit on Closed
julep trigger support-agent '{"text": "hi"}'   # one-shot: send one event, render the reply
julep trigger support-agent '{"text": "hi"}' --channel in
julep listen support-agent --forward-to https://example.com/hook   # forward emitted events to a URL
```

`julep chat` and `julep listen` currently support `--env local`. `julep trigger` accepts only the `in` channel. See [using the CLI](/docs/guides/using-the-cli).

## Testing without a live handle

Use `drive_session(...)` when you want a bounded, in-memory fold over known inputs:

```python
from julep import drive_session

carrier, outputs = await drive_session(chat, inputs=["a", "b"], max_turns=2)
```

It returns the final carrier and all emissions from the session `out_channel`; it raises if more than `max_turns` messages are supplied.

## Worked example

[`examples/session_demo.py`](https://github.com/julep-ai/julep-v2/blob/main/examples/session_demo.py) drives a real `anthropic:claude-haiku-4-5` stateful conversation (plant a codeword on turn 1, recall it on turn 2 via the threaded carrier) on all three backends:

```bash
set -a; source .env; set +a            # ANTHROPIC_API_KEY (keys are not shell-exported)
uv run --extra dev --extra providers python examples/session_demo.py local
uv run --extra dev --extra providers python examples/session_demo.py temporal
uv run --extra dev --extra providers --extra cma python examples/session_demo.py cma
```

> **Deploying a session worker remotely:** session pures are content-addressed over their source, so the worker must register pures from the exact same source file the deploy pins from — bake the session module into the worker image, or you will hit `PureDriftError`.

## See also

- [Concepts](/docs/concepts/model) — the shape lattice and three planes sessions reuse.
- [Authoring flows](/docs/guides/authoring-flows) · [Using the CLI](/docs/guides/using-the-cli) · [Deploy to Temporal](/docs/deploy/temporal)
- [Sessions API reference](/docs/reference/sessions-api)
- Design: [durable session store](/docs/internals/durable-session-store) · [agent loop as turn](/docs/internals/agent-loop-as-turn) · [CMA runtime](/docs/internals/cma-runtime)

<!-- ported-by ca-docs-site: guides/sessions -->
