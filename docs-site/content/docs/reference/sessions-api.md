---
title: "Sessions API"
description: "The sessions API: scan/loop/@session, handles, events, and the durable store."
---

Open a session once, keep sending messages, and stream `SessionEvent`s until `Closed`. A session is a root `Op.LOOP`: one turn blocks on `recv`, runs ordinary IR, emits outputs, and threads a carrier to the next turn. For the user guide, see [Sessions](/docs/guides/sessions).

```python
from julep import Agent, arr, recv, register_pure, scan, seq

def turn(value: dict) -> tuple[list[str], dict[str, object]]:
    history = [*(value["carrier"] or []), str(value["msg"])]
    return history, {"seen": history, "reply": f"ack:{value['msg']}"}

register_pure("docs.sessions.turn", turn)
chat = scan(seq(recv("in"), arr("docs.sessions.turn")), init=[])
handle = await Agent("test-model", llm=None).open(session=chat, backend="local")
await handle.send("hi", idempotency_key="turn-1")
```

## Imports

```python
from julep import (
    Channel, HUMAN_CHANNEL, LocalSessionHandle, Session, SessionCompileError,
    SessionEvent, SessionHandle, drive_session, emit, human_gate, loop, recv,
    scan, session,
)
from julep.execution.cma_session import CMASessionHandle
from julep.execution.session_store import InMemorySessionStore, SessionStore
```

Temporal symbols are lazy exports and require `temporalio`:

```python
from julep import HAVE_TEMPORAL
from julep.execution import SessionInput, SessionWorkflow, TemporalSessionHandle
```

## Authoring

### `recv`

```python
def recv(channel: str, *, timeout_s: Optional[int] = None) -> Node
```

Reserved `__recv__` leaf. The harness turns it into a blocking channel receive.

Parameters: `channel` is the session channel name; `timeout_s` stores a seconds timeout on `Ann.timeout`.
Returns: `Node`.
Raises: no direct session-specific exception. Session validation later rejects undeclared channels, flow-target usage, parallel placement, emit-before-recv paths, and multiple receives per turn.
Example: `scan(seq(recv("in", timeout_s=30), arr("docs.sessions.turn")), init=[])`.

### `emit`

```python
def emit(channel: str, value: Optional[str] = None) -> Node
```

Reserved `__emit__` leaf. The harness appends a deterministic, sequenced output record.

Parameters: `channel` is the output channel; `value` is an optional literal payload. If omitted, `emit` emits and forwards its input.
Returns: `Node`.
Raises: no direct session-specific exception. Validation rejects emit-before-recv paths, flow-target usage, parallel placement, and undeclared channels.
Example: `loop(seq(recv("in"), emit("out")), init=None)`.

### `human_gate` and `HUMAN_CHANNEL`

```python
HUMAN_CHANNEL = "human"
def human_gate(*, prompt: Optional[str] = None, timeout_s: Optional[int] = None) -> Node
```

Reserved `__human_gate__` leaf. In Temporal it waits for `submitHuman`; it is the back-compatible human-channel form of `recv(HUMAN_CHANNEL)`.

Parameters: `prompt` is optional prompt text; `timeout_s` stores a seconds timeout on `Ann.timeout`.
Returns: `Node`.
Raises: no direct session-specific exception.
Example: `human_gate(prompt="approve?")`; channel equivalent: `recv(HUMAN_CHANNEL)`.

### `scan`

```python
def scan(
    step_flow: Node,
    init: object,
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any]
```

Builds a split-output root `Op.LOOP`. Each turn receives `{"carrier": carrier, "msg": message}`. The body must return `(next_carrier, output)`; the runtime threads `next_carrier` and emits `output` on `out_channel`.

Parameters: `step_flow` is the finite turn flow; `init` is the initial carrier; `in_channel` and `out_channel` are default handle channels; `state_schema` serializes as `stateSchema`.
Returns: `Session[Any, Any]`.
Raises: `SessionValidationError` for blocking session diagnostics.

```python
def count_turn(value: dict) -> tuple[int, dict[str, object]]:
    n = int(value["carrier"] or 0) + 1
    return n, {"turn": n, "echo": value["msg"]}

register_pure("docs.sessions.count_turn", count_turn)
counter = scan(seq(recv("in"), arr("docs.sessions.count_turn")), init=0)
```

### `loop`

```python
def loop(
    body: Node,
    *,
    init: object,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any]
```

Builds a root `Op.LOOP` without split-output handling. The body result becomes the next carrier; use `emit(...)` inside `body` for output side effects.

Parameters: `body` is the finite turn flow; `init` is the initial carrier; `in_channel`, `out_channel`, and `state_schema` are stored on the session/loop node.
Returns: `Session[Any, Any]`.
Raises: `SessionValidationError` for blocking session diagnostics.
Example: `loop(seq(recv("in"), emit("out")), init=None)`.

### `@session`

```python
def session(
    func: Optional[Callable[..., Any]] = None,
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any] | Callable[[Callable[..., Any]], Session[Any, Any]]
```

Experimental coroutine sugar. The decorated object must be `async def` with exactly one parameter, simple pre-loop assignments, and a final `while True`. The loop body must start with `msg = await s.recv()`, contain exactly one awaited `recv`, exactly one awaited `emit`, and stay straight-line.

Parameters: `func` is the async function; `in_channel`, `out_channel`, and `state_schema` configure the generated session.
Returns: `Session[Any, Any]`.
Raises: `SessionCompileError` when the function is not liftable; `SessionValidationError` if the generated loop is invalid.

```python
@session
async def counted_echo(s):
    count = 0
    while True:
        msg = await s.recv()
        count += 1
        await s.emit({"turn": count, "echo": msg})
```

### `drive_session`

```python
async def drive_session(
    session: Session[I, O],
    *,
    inputs: Iterable[I],
    max_turns: int = 1000,
    env: Optional[InMemoryEnv] = None,
) -> tuple[object, list[O]]
```

Runs a session over finite in-memory inputs and returns the final carrier plus emitted outputs from `session.out_channel`.

Parameters: `session` is the session to interpret; `inputs` are queued on `session.in_channel`; `max_turns` caps consumed messages; `env` optionally supplies effect handlers.
Returns: `tuple[object, list[O]]`.
Raises: `JulepError` if more than `max_turns` messages are supplied; interpreter errors from the turn body.
Example: `carrier, outputs = await drive_session(counter, inputs=["a", "b"])`.

## Values And Events

### `Channel`

```python
class Channel(Generic[T]):
    def __init__(self, name: str, payload: Optional[JSONSchema] = None) -> None
    async def recv(self) -> T
    def append(self, value: T) -> None
    def emit(self, value: object) -> None
    def drain(self) -> list[object]
```

Typed in-memory FIFO plus outbound buffer.

Parameters: `name` is the channel name; `payload` is optional JSON Schema metadata.
Returns: `recv()` returns the next inbound value; `drain()` returns and clears outbound values.
Raises: no session-specific exception.
Example: `channel.append("a"); assert await channel.recv() == "a"; channel.emit("ok"); assert channel.drain() == ["ok"]`.

### `Session`

```python
@dataclass
class Session(Generic[I, O]):
    body: Node
    init: object
    in_channel: str
    out_channel: str
```

Dataclass for a root `Op.LOOP`, initial carrier, and default channels.

Returns: dataclass instance.
Raises: no constructor-specific exception; prefer `scan`, `loop`, or `@session` so validation runs.
Example: `assert counter.in_channel == "in"`.

### `SessionEvent`

```python
@dataclass(frozen=True)
class SessionEvent:
    kind: str
    channel: Optional[str] = None
    seq: Optional[int] = None
    payload: Any = None
    turn: Optional[str] = None
    reason: Optional[str] = None
    fatal: bool = False

    @classmethod
    def emit(cls, channel: str, seq: int, payload: Any) -> "SessionEvent": ...
    @classmethod
    def turn_started(cls) -> "SessionEvent": ...
    @classmethod
    def turn_done(cls) -> "SessionEvent": ...
    @classmethod
    def error(cls, reason: str, *, fatal: bool) -> "SessionEvent": ...
    @classmethod
    def closed(cls, reason: Optional[str] = None) -> "SessionEvent": ...

    @property
    def is_emit(self) -> bool: ...
    @property
    def is_turn(self) -> bool: ...
    @property
    def is_error(self) -> bool: ...
    @property
    def is_closed(self) -> bool: ...
```

| `kind` | Fields | Meaning |
|---|---|---|
| `emit` | `channel`, `seq`, `payload` | A turn emitted a value. |
| `turn` | `turn="started"` or `"done"` | Turn boundary marker. |
| `error` | `reason`, `fatal` | Recoverable when `fatal=False`, terminal when `fatal=True`. |
| `closed` | `reason` | Single terminal event; `events()` ends after yielding it. |

Returns: classmethods return `SessionEvent`.
Raises: no session-specific exception.
Example: `event = SessionEvent.emit("out", 1, {"reply": "ok"}); assert event.is_emit`.

### `SessionHandle`

```python
class SessionHandle(Protocol):
    def events(self) -> AsyncIterator[SessionEvent]: ...
    async def send(
        self,
        value: Any,
        *,
        channel: Optional[str] = None,
        idempotency_key: Any = None,
    ) -> dict[str, Any]: ...
    async def state(self) -> dict[str, Any]: ...
    async def open_receives(self) -> list[dict[str, Any]]: ...
    async def close(self, reason: Optional[str] = None) -> None: ...
```

Backend-neutral live facade. `events()` is single-consumer. `send(...)` returns `{"seq": int, "channel": str}` and deduplicates same-key/same-payload sends. `open_receives()` returns `{"channel": str, "seq": int}` records.

Returns: see method signatures.
Raises: `JulepError` for duplicate event consumers, idempotency conflicts, and local capacity errors; backend `SessionClosed` when sending after close; Temporal update failures for workflow-side validation.
Example: `ack = await handle.send("a", idempotency_key="a"); await handle.close("done")`.

## Opening And Handles

### `Agent.open`

```python
async def open(
    self, *, session: Session[Any, Any], backend: str = "local",
    principal: Optional[dict[str, Any]] = None, client: Any = None,
    task_queue: str = "julep", policy: Any = None,
    history_threshold: Optional[int] = None, channel_capacity: Optional[int] = None,
    session_id: Optional[str] = None, environment: Any = None,
) -> SessionHandle
```

Deploys the session with `target="session"` and opens one live handle.

Parameters: `backend` is `"local"`, `"temporal"`, or `"cma"`; `client` is required for Temporal and CMA; `task_queue`, `history_threshold`, `channel_capacity`, and `session_id` are Temporal-facing; `environment` is passed to CMA; `principal` is threaded to worker effects.
Returns: `SessionHandle`.
Raises: `ValueError` for unknown backend or missing client; `ValidationError` for deploy/capability failures; `NotImplementedError` when sub-capability deployments are not auto-wired into the session worker; Temporal rejects token/wall-clock budget dimensions.
Example: `handle = await agent.open(session=counter, backend="temporal", client=client, session_id="support-session-1")`.

### `Agent.open_session`

```python
def open_session(
    self, *, session: Session[Any, Any], backend: str = "local",
    principal: Optional[dict[str, Any]] = None, client: Any = None,
    task_queue: str = "julep", policy: Any = None,
    history_threshold: Optional[int] = None, channel_capacity: Optional[int] = None,
    session_id: Optional[str] = None, environment: Any = None,
) -> SessionHandle
```

Synchronous wrapper around `Agent.open(...)` for non-local backends when no event loop is running.

Returns: `SessionHandle`.
Raises: `RuntimeError` for `backend="local"` or when called inside a running event loop; otherwise the same backend errors as `Agent.open`.
Example: `handle = agent.open_session(session=counter, backend="temporal", client=client)`.

### `LocalSessionHandle`

```python
class LocalSessionHandle:
    @classmethod
    async def open(
        cls, session: Session[Any, Any], *,
        tools: Optional[dict[str, Callable[[Any], Any]]] = None,
        reasoners: Optional[dict[str, Callable[[Any], Any]]] = None,
        subs: Optional[dict[str, Callable[[Any], Any]]] = None,
        agents: Optional[dict[str, Callable[[Any], Any]]] = None,
        planners: Optional[dict[str, Callable[[Any], Node]]] = None,
        max_calls: Optional[dict[str, int]] = None, mode: EnforcementMode | str = EnforcementMode.STRICT,
        principal: Optional[dict[str, Any]] = None, max_turns: int = 100000,
        channel_capacity: Optional[int] = None, env: Optional[_LiveLocalEnv] = None,
        manifest: Optional[Any] = None,
    ) -> "LocalSessionHandle"
```

Direct in-memory handle opener. Prefer `Agent.open(..., backend="local")` for deployment and capability checks.

Returns: `LocalSessionHandle`.
Raises: `JulepError` for max-turn exhaustion, duplicate `events()`, `ChannelFull`, or idempotency conflicts. Fatal turn exceptions emit fatal error then closed.
Example: `handle = await LocalSessionHandle.open(counter, channel_capacity=10)`.

### `TemporalSessionHandle`

```python
class TemporalSessionHandle:
    def __init__(
        self,
        wfhandle: Any,
        *,
        in_channel: str = "in",
        out_channel: str = "out",
        poll_s: float = 0.02,
    ) -> None
```

Methods match `SessionHandle`: `send`, `state`, `open_receives`, `close`, and `events`. `send` executes update `"send"`. `events()` polls query `"events"` and acks with update `"ack_events"` after yielding.

Returns: `TemporalSessionHandle`.
Raises: `JulepError` for duplicate event consumers; `TimeoutError` if `close()` does not quiesce within 30 seconds; Temporal workflow/update failures for workflow-side errors.
Example: `public = TemporalSessionHandle(client.get_workflow_handle("support-session-1"))`.

### `CMASessionHandle`

```python
class CMASessionHandle:
    @classmethod
    async def open(
        cls, *, client: CMAClient, tools: Mapping[str, Callable[[Any], Any]],
        agent: dict[str, Any], environment: Any = None,
        in_channel: str = "in", out_channel: str = "out",
        session_cid: str = "cma-session", cfg: Optional[AgentConfig] = None,
        granted: Optional[set[str]] = None, contracts: Optional[AgentContractMap] = None,
    ) -> "CMASessionHandle"
```

Handle backed by one hosted CMA session per accepted inbound turn. It does not thread the framework carrier; resend transcript yourself if the hosted model needs memory.

Returns: `CMASessionHandle`.
Raises: `JulepError` for unsupported send channels, duplicate `events()`, idempotency conflicts, missing custom-tool fields, or policy failures surfaced as fatal events.
Example: `handle = await CMASessionHandle.open(client=client, tools={}, agent={"name": "support", "tools": []})`.

## Temporal Workflow Surface

### `SessionInput`

```python
@dataclass
class SessionInput:
    session_id: str; flow_json: dict[str, Any]; manifest_json: Optional[dict[str, Any]]; init: Any
    max_call_limits: Optional[dict[str, int]] = None; call_counts: Optional[dict[str, int]] = None
    pinned_pures: Optional[dict[str, str]] = None; budget: Optional[dict[str, Any]] = None; spent: float = 0.0
    bundle: Optional[list[dict[str, str]]] = None; in_channel: str = "in"; out_channel: str = "out"
    policy: Optional[dict[str, Any]] = None; principal: Optional[dict[str, Any]] = None
    root_run_id: Optional[str] = None; segment_seq: int = 0; history_threshold: Optional[int] = None
    channel_capacity: Optional[int] = None; state_cursor: Optional[int] = None; has_carrier: bool = False; carrier: Any = None
    inbox: Optional[dict[str, list[dict[str, Any]]]] = None; out_buffers: Optional[dict[str, list[dict[str, Any]]]] = None
    ack_cursors: Optional[dict[str, int]] = None; seq_cursors: Optional[dict[str, int]] = None
    closed: bool = False; close_reason: Optional[str] = None
    idempotency_index: Optional[dict[str, dict[str, int]]] = None; idempotency_fp: Optional[dict[str, dict[str, str]]] = None
    event_log: Optional[list[dict[str, Any]]] = None; event_seq: int = 0; event_ack: int = 0
```

Raw Temporal input. `Agent.open(..., backend="temporal")` constructs it after freeze and validation.

Returns: dataclass instance.
Raises: no constructor validation. `SessionWorkflow.run` raises non-retryable `ApplicationError(type="ValidationError")` if the workflow id differs from `session_id`, the flow is not root `Op.LOOP`, or validation fails.
Example: `SessionInput("s1", fr.flow.to_json(), manifest_to_json(fr.manifest), counter.init, policy=ExecutionPolicy().to_json())`.

### `SessionWorkflow`

```python
@workflow.defn(name="SessionWorkflow")
class SessionWorkflow:
    @workflow.run
    async def run(self, inp: SessionInput) -> Any
```

Durable Temporal workflow for root `Op.LOOP` sessions.

| Operation | Name | Payload | Return |
|---|---|---|---|
| update | `send` | `{"channel": str = "in", "value": Any, "idempotency_key": Any?}` | `{"seq": int, "channel": str}` |
| update | `close` | `{"reason": Any?}` | `{"closed": True}` |
| update | `ack` | `{"channel": str, "seq": int}` | `{"channel": str, "acked": int}` |
| update | `ack_events` | `{"eseq": int}` | `{"acked": int}` |
| query | `events` | none | event records with `eseq` |
| query | `open_receives` | none | `{"channel": str, "seq": int}` records |
| query | `state` | none | `emitted`, `ack_cursors`, `capacity`, `carrier`, `closed`, `close_reason`, `pending` |

Returns: final carrier from `run`.
Raises: `ApplicationError(type="ChannelFull")` for bounded-channel overflow; `ApplicationError(type="ValidationError")` for closed sends or idempotency conflicts; workflow failure for fatal runtime errors.
Example: `ack = await wf.execute_update("send", {"channel": "in", "value": "hi"})`.

## Durable Store

```python
class SessionStore(Protocol):
    async def load(self, session_id: str, cursor: Cursor) -> AgentState: ...
    async def commit(self, session_id: str, base: Cursor, state: AgentState, state_hash: str) -> Cursor: ...
    async def load_value(self, session_id: str, cursor: Cursor) -> Any: ...
    async def commit_value(self, session_id: str, base: Cursor, value: Any, value_hash: str) -> Cursor: ...
    async def put_blob(self, tenant: str, value: Any) -> str: ...
    async def get_blob(self, tenant: str, ref: str) -> Any: ...
class InMemorySessionStore:
    def __init__(self, blob_store: Optional[BlobStore] = None, *, empty_value: Any = None) -> None
def value_fingerprint(value: Any) -> str
```

`SessionStore` is the durable carrier/state contract. Temporal sessions use `load_value` and `commit_value` when continue-as-new persists the carrier. `InMemorySessionStore` canonicalizes JSON, treats cursor `0` as `empty_value`, dedups same-base/same-value replay, and raises `CursorConflict` for stale divergent commits. `value_fingerprint` is SHA-256 over compact sorted-key canonical JSON.

Returns: store methods return cursors, states, values, or refs as annotated; `value_fingerprint` returns hex.
Raises: `SessionStoreError` for missing cursors or hash mismatches; `CursorConflict` for stale divergent writes; `TypeError` for non-JSON values.
Example: `cursor = await store.commit_value("s1", 0, {"turn": 1}, value_fingerprint({"turn": 1}))`.

## IR And Validation

`scan` and `loop` create `Node(op=Op.LOOP)` with `body`, optional `stateSchema`, `channels=[{"name": in_channel}, {"name": out_channel}]`, and `args={"split": True}` only for `scan`. `recv("in", timeout_s=7)` serializes as reserved `__recv__` with `channel: "in"` and `ann.timeout: 7`. `emit("out", value="ready")` serializes as reserved `__emit__` with `channel: "out"` and `args={"value": "ready"}`.

| Diagnostic | Meaning |
|---|---|
| `SESSION_RECV_IN_PARALLEL`, `SESSION_EMIT_IN_PARALLEL`, `SESSION_LOOP_IN_PARALLEL` | Channel op or loop under `par`, `each`, `race`, `hedge`, or `quorum`. |
| `SESSION_LOOP_NOT_RECV_GUARDED`, `SESSION_LOOP_EMIT_BEFORE_RECV`, `SESSION_LOOP_MULTIPLE_RECV` | Turn productivity rule failed. |
| `SESSION_LOOP_IN_EVAL_PLAN`, `SESSION_LOOP_NESTED`, `SESSION_LOOP_BAD_FIELDS` | Loop placement or fields are invalid. |
| `SESSION_CHANNEL_UNDECLARED` | `recv` or `emit` targets an undeclared channel. |
| `SESSION_LOOP_IN_FLOW`, `SESSION_RECV_IN_FLOW`, `SESSION_EMIT_IN_FLOW` | Session op compiled for a flow target. |
| `SESSION_RECV_OUTSIDE_LOOP`, `SESSION_EMIT_OUTSIDE_LOOP` | Channel op reachable outside the root loop body. |

## Errors

| Error | Import | Meaning |
|---|---|---|
| `SessionCompileError` | `from julep import SessionCompileError` | `@session` cannot be lifted. |
| `SessionValidationError` | `from julep.session import SessionValidationError` | `scan` / `loop` found blocking diagnostics. |
| `SessionTurnError` | `from julep.errors import SessionTurnError` | Turn body intentionally signals a session error. |
| `JulepError` | `from julep import JulepError` | Base framework error, including duplicate event consumers and idempotency conflicts. |
| `ValidationError` | `from julep import ValidationError` | Deploy/open-time validation or capability failure. |
| `SessionStoreError`, `CursorConflict` | `from julep.execution.session_store import ...` | Durable store errors. |

Example: `raise SessionTurnError("try again", fatal=False)` emits an error event and continues without advancing the carrier.

## Worker And CLI

Temporal workers register `SessionWorkflow` through `build_worker(...)` / `run_worker(...)`. `WorkerContext.session_store` is required for carrier persistence across continue-as-new; absent store activities raise `RuntimeError("worker has no session store configured")`.

```python
ctx = WorkerContext(session_store=InMemorySessionStore(empty_value=0), mcp_call=my_mcp_call, llm=my_llm)
worker = build_worker(client, ctx, task_queue=DEFAULT_TASK_QUEUE)
```

`WorkerServeSettings.from_env(...)` reads `WORKER_CONTEXT_FACTORY`, `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, `TEMPORAL_TASK_QUEUE`, `TEMPORAL_API_KEY`, `TEMPORAL_TLS`, `WORKER_GRACEFUL_SHUTDOWN_S`, `WORKER_MAX_CONCURRENT_ACTIVITIES`, `WORKER_MAX_CONCURRENT_WORKFLOW_TASKS`, and `WORKER_HEALTH_PORT`. `julep worker` reads that contract directly; its only flag is `--smoke-test-seconds`.

Local `julep` session commands:

| Command | Signature | Notes |
|---|---|---|
| `julep chat` | `julep chat NAME [--env local]` | stdin REPL; only local env is supported. |
| `julep trigger` | `julep trigger NAME EVENT [--channel in]` | sends one JSON-or-raw event; only `in` is accepted. |
| `julep listen` | `julep listen NAME --forward-to URL` | POSTs emitted event JSON to `URL`. |
<!-- generated by julep-docs-matrix: sessions/reference -->

<!-- ported-by julep-docs-site: reference/sessions-api -->
