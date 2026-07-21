---
title: "Python API"
description: "The full julep public API surface, grouped by purpose."
---

Start with `@flow`, `@tool` or `@pure`, `Reasoner`, and `deploy(...).dry_run(...)`.
That is the stable authoring loop for durable agent dataflows; the
lower-level IR/combinator APIs exist when you need to construct or inspect the
wire format directly. See the repository [README](/docs),
[docs index](/docs), [concepts](/docs/concepts/model), and
[SPEC](/docs/internals/specification) for the model and conformance contract.

```python
from typing import TypedDict

from julep import Reasoner, deploy, flow, pure, think, tool

class Reply(TypedDict):
    reply: str

@tool(effect="read", idempotent=True)
def lookup(ticket: str) -> dict[str, str]:
    return {"ticket": ticket, "queue": "billing", "summary": "Duplicate-charge runbook"}

@pure("prompt")
def prompt(hit: dict[str, str]) -> dict[str, str]:
    return {"queue": hit["queue"], "context": hit["summary"]}

SUPPORT_REPLY = Reasoner(
    name="support_reply",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Return JSON.",
    reply=Reply,
)

@flow
def triage(ticket: str) -> dict[str, str]:
    hit = lookup(ticket, retries=2, timeout_s=5)
    answer = think(SUPPORT_REPLY, prompt(hit), timeout_s=10)
    return hit | answer

deployment = deploy(triage, tools=[lookup], reasoners=[SUPPORT_REPLY])
result = deployment.dry_run(
    "TICKET-42",
    reasoners={"support_reply": lambda value: {"reply": value["context"]}},
)
print(result.value)
```

The package root is the public import boundary. Temporal symbols are added to
`__all__` only when `temporalio` is installed; `HAVE_TEMPORAL` and `HAVE_DBOS`
report optional runtime availability.

## Install surface

| Extra | Installs | Example |
|---|---|---|
| base | authoring, compile, pure interpreter, the `julep` console script | `pip install --pre julep` |
| `temporal` | Temporal workflows, activities, worker helpers | `pip install --pre 'julep[temporal]'` |
| `dbos` | DBOS backend on `dbos>=2.18` | `pip install --pre 'julep[dbos]'` |
| `http` | native HTTP tool calls from `callTool` | `pip install --pre 'julep[http]'` |
| `cma` | Claude Managed Agents HTTP adapter | `pip install --pre 'julep[cma]'` |
| `mcp` | MCP SDK, live snapshots, HTTP caller, PyJWT, Ed25519 auth | `pip install --pre 'julep[mcp]'` |
| `server` | FastAPI control plane, Postgres store, SSE, Temporal gateway | `pip install --pre 'julep[server]'` |
| `dotctx` | rich dotctx prompt packages with Jinja2 | `pip install --pre 'julep[dotctx]'` |
| `providers` | `any-llm` provider caller | `pip install --pre 'julep[providers]'` |
| `otel`, `langfuse` | projection span export | `pip install --pre 'julep[otel]'` |
| `store` | CAS bundle storage/signing helpers | `pip install --pre 'julep[store]'` |
| `wasm` | wasm-tier bundle-sourced pures | `pip install --pre 'julep[wasm]'` |

## Core enums and constants

| Symbol | Signature or values | Use | Raises | Example |
|---|---|---|---|---|
| `Shape` | `PIPELINE`, `DATAFLOW`, `BRANCHING`, `FEEDBACK`, `STAGED`, `AGENT` | inferred flow cost lattice | enum `ValueError` on bad value | `Shape("Pipeline")` |
| `Effect` | `READ`, `WRITE`, `EXTERNAL`, `DANGEROUS` | tool effect contract | enum `ValueError` | `Effect("read")` |
| `Idempotency` | `REQUIRED`, `NATIVE`, `BEST_EFFORT`, `NONE` | retry/race safety | enum `ValueError` | `Idempotency("native")` |
| `ContextScope` | `NONE`, `LOCAL`, `SUMMARY`, `WHOLE_SESSION` | session/transcript context read | enum `ValueError` | `ContextScope("local")` |
| `SummaryPolicy` | `RESULT_ONLY`, `COMPRESSED_TRACE`, `FULL_CHILD_REF` | sub-flow return policy | enum `ValueError` | `SummaryPolicy("result_only")` |
| `EnforcementMode` | `STRICT`, `DEV`; `coerce(value)` maps `"prod"` to strict | deploy/runtime diagnostic behavior | enum `ValueError` | `EnforcementMode.coerce("dev")` |
| `HUMAN_GATE_TOOL` | `"__human_gate__"` | reserved human signal wait tool | none | `call(HUMAN_GATE_TOOL)` |
| `SLEEP_TOOL` | `"__sleep__"` | reserved durable timer tool | none | `delay(seconds=1)` |
| `RECV_TOOL`, `EMIT_TOOL` | `"__recv__"`, `"__emit__"` | reserved session channel tools | none | `recv("in")`, `emit("out")` |
| `HUMAN_CHANNEL` | `"human"` | default human channel name | none | `HUMAN_CHANNEL` |
| `__version__` | package distribution version or `"0.0.0+unknown"` | artifact identity component | none | `print(__version__)` |

## IR value types

These are plain Python value objects for authored or frozen IR. `to_json()` is
available where shown; `from_json(...)` exists on the matching JSON codecs.

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `NativeTool` | `NativeTool(name: str, kind: str = "native")` | `name` is the native tool key | tool ref | none at construction | `native("lookup").to_json()` |
| `McpTool` | `McpTool(server: str, tool: str, kind: str = "mcp")` | MCP server and tool names | tool ref | none | `mcp("fs", "read").to_json()` |
| `ChannelRef` | `ChannelRef(name: str, payload: dict[str, Any] | None = None)` | session channel and optional schema | channel ref | `KeyError` in `from_json` if missing name | `ChannelRef("in").to_json()` |
| `ContextPolicy` | `ContextPolicy(scope=ContextScope.LOCAL, redact_pii=False, max_tokens=None)` | explicit context scope and token cap | policy | enum `ValueError` in `from_json` | `ContextPolicy(scope=ContextScope.LOCAL)` |
| `CacheHint` | `CacheHint(key: str | None = None, ttl_s: int | None = None)` | advisory cache key/TTL | hint | none | `Ann(cache=CacheHint("x", 60))` |
| `Ann` | `Ann(*, cost=None, risk=None, cache=None, effect=None, timeout_s=None, max_attempts=None, retry_interval_s=None, backoff_rate=None, batchable=False)` | per-node cost, risk, timeout, retry, batchability | annotation | validation emits retry diagnostics for bad ranges | `Ann(timeout_s=5, max_attempts=2)` |
| `SubContract` | `SubContract(shape: Shape, summary_policy: SummaryPolicy | None = None)` | declared child shape and summary policy | sub contract | enum `ValueError` in `from_json` | `SubContract(Shape.PIPELINE)` |
| `Node` | `Node(op, id, ann=None, step=None, left=None, right=None, select=None, cases=None, default=None, bound=None, body=None, plan=None, state_schema=None, channels=None, controller=None, pure=None, args=None, merge=None, prompt=None, tools=None, subflows=None, budget=None, max_rounds=None, ctx=None, summarizer=None, source=None)` | complete IR node fields | IR tree node | malformed trees fail `validate` or `freeze` | `Node.from_json(ident().to_json())` |
| `ToolManifest` | `dict[str, FrozenTool]` | execution hash -> frozen tool | manifest | lookup `KeyError` | `manifest_to_json(deployment.manifest)` |

## Authoring: decorators, handles, tools, pures, reasoners

`@flow` runs the Python function once at definition time with `Handle` values.
Registered tools, registered pures, `think(...)`, `cond(...)`, `switch(...)`,
`each(...)`, and `reschedule(...)` append graph steps; `h1 | h2` emits
`std.merge`; `h["field"]` and `h.field` emit `std.pluck`. Runtime values must enter through
flow parameters or JSON captures.

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `flow` | `flow(fn: Callable[..., Any]) -> FlowDef` | Python function with at least one parameter | decorated flow | `DefineError` for bad handle use, unused params, non-Handle return | `@flow\ndef f(x): return x["a"]` |
| `FlowDef` | `FlowDef(fn: Callable[..., Any])` | function to lower | lowerable flow | `DefineError` | `flow(lambda x: x)` is invalid because source/return rules are stricter |
| `FlowDef.to_ir` | `to_ir(self) -> Node` | no args | compiled IR | `DefineError` if more than one runtime parameter remains | `triage.to_ir().to_json()` |
| `BoundFlow` | `BoundFlow(flow: FlowDef, bound_args: dict[str, Any])` | partially applied JSON args | lowerable flow | `DefineError` if not exactly one runtime parameter remains | `some_flow(region="us").to_ir()` |
| `Handle` | `Handle(label: str, graph, source)` | internal data handle | authoring handle | `TypeError`/`DefineError` on bool, iter, equality, or invalid/private attribute access | `h.summary`, `h["summary"]`, `h1 | h2` inside `@flow` |
| `tool` | `tool(fn=None, /, *, effect="write", idempotent=False, name=None)` | function plus effect/idempotency/name | `Tool` or decorator | `ValueError` for invalid effect | `@tool(effect="read", idempotent=True)` |
| `Tool` | `Tool(name, fn, contract, input_schema, output_schema, param_names=())` | native callable contract | `FlowLike` tool | callable may raise its own errors | `lookup.to_ir()` |
| `mcp_tool` | `mcp_tool(server, tool, *, name=None) -> McpToolStep` | frozen MCP server/tool reference | `FlowLike` MCP step | `ValueError` for empty names; callable only on handles inside `@flow` | `read = mcp_tool("episodes", "read_episode")` |
| `Tool.bound_tool` | property `Callable[[Any], Any]` | single threaded input adapter | callable | function errors | `snapshot_from_tools([lookup])` |
| `snapshot_from_tools` | `snapshot_from_tools(tools: Sequence[Tool]) -> McpSnapshot` | native tools | freeze snapshot | none | `deploy(triage, tools=[lookup])` |
| `pure` | `pure(fn, /) -> Pure`; `pure(name: str, /) -> Callable[[fn], Pure]` | deterministic map/predicate | `Pure` | registry `ValueError` on conflicting name | `@pure("is_large")` |
| `Pure` | `Pure(name: str, fn: Callable[..., Any])` | registered pure function | `FlowLike` pure | function errors at runtime | `prompt.to_ir()` |
| `register_pure` | `register_pure(name: str, fn: PureFn) -> PureEntry` | name and callable | registry entry | `ValueError` on conflicting function | `register_pure("id", lambda x: x)` |
| `get_pure` | `get_pure(name: str) -> PureFn` | registered pure name | callable | `KeyError` if unknown | `get_pure("prompt")({"summary": "x"})` |
| `is_registered` | `is_registered(name: str) -> bool` | pure name | bool | none | `is_registered("prompt")` |
| `diff_pure_hashes` | `diff_pure_hashes(pinned: dict[str,str], registered: dict[str,str]) -> list[dict[str,str|None]]` | pinned and actual hash maps | drift list | none | `diff_pure_hashes({}, {})` |
| `Reasoner` | `Reasoner(name, model, system="", tools=(), temperature=None, max_rounds=None, is_agent=False, sub_contract=None, context_scope=ContextScope.LOCAL, system_render=None, user_render=None, max_tokens=None, *, reply=_UNSET)` | model-call config; `reply` accepts TypedDict, Pydantic v2 model, or raw schema dict | reasoner config | `TypeError` for unsupported `reply` | `Reasoner("r", "anthropic:claude-haiku-4-5", reply=Reply)` |
| `get_reasoner` | `get_reasoner(name: str) -> Reasoner` | reasoner name | config | `KeyError` if unknown | `get_reasoner("support_reply").model` |
| `load_dotctx` | `load_dotctx(path: str) -> Reasoner` | dotctx directory | registered reasoner | `FileNotFoundError`, `RuntimeError`, rich-layout import errors | `load_dotctx("reasoners/planner")` |
| `reasoner_from_settings` | `reasoner_from_settings(settings: dict[str, Any], *, name=None, base_dir=None) -> Reasoner` | settings mapping and optional path | registered reasoner | `ValueError` if no name | `reasoner_from_settings({"name":"r","model":"m"})` |
| `reasoner_to_flow` | `reasoner_to_flow(reasoner: Reasoner, *, ctx=None) -> Node` | reasoner and optional context | `think`, `iter_up_to`, `app`, or `sub` node | none | `reasoner_to_flow(get_reasoner("r"))` |
| `dotctx_flow` | `dotctx_flow(path: str, *, ctx=None) -> Node` | dotctx path | lowered node | same as `load_dotctx` | `dotctx_flow("reasoners/r")` |
| `CtxPipelineConfig` | `CtxPipelineConfig(name, ctx, lane="default", env={})` | zero-code pipeline declaration | config value | config validation occurs in `load_config` | `CtxPipelineConfig("summary", "prompts/summary.ctx")` |
| `pipeline_spec_from_ctx` | `pipeline_spec_from_ctx(config, *, root, env_vars=None) -> PipelineSpec` | load dotctx, merge env, and lower with `reasoner_to_flow` | pipeline spec | dotctx/config errors | `pipeline_spec_from_ctx(cfg, root=Path("."))` |

## `@flow` control helpers

These names are exported at package root. For lower-level `dsl.think` and
`dsl.each`, import from `julep.dsl`.

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `think` | `think(reasoner_or_name: str | Reasoner, value: Handle | None = None, /, **kwargs) -> Node | Handle` | reasoner and optional `Handle`; kwargs may include `name`, `retries`, `retry_interval_s`, `backoff_rate`, `timeout_s` | node outside `@flow`, handle inside | `DefineError` for invalid captures; `TypeError` for bad usage | `think(SUPPORT_REPLY, prompt(hit), timeout_s=10)` |
| `cond` | `cond(pred: str | Any, subject: Handle, *, then: FlowDef | BoundFlow, orelse: FlowDef | BoundFlow) -> Handle` | registered pure predicate, subject, two arms | branch handle | `DefineError` for unregistered pred or bad arm binding | `cond("is_large", item, then=big, orelse=small)` |
| `switch` | `switch(selector: str | Any, subject: Handle, *, cases: dict[str, FlowDef | BoundFlow], default=None) -> Handle` | registered selector and case arms | selected branch handle | `DefineError` for empty cases or bad arm binding | `switch("route", item, cases={"a": a_flow}, default=b_flow)` |
| `each` | `each(body: FlowDef | BoundFlow | Node, items: Handle | None = None, *, max_parallel=None, reducer=None) -> Node | Handle` | body flow/node, list handle in `@flow`, optional reducer | dynamic fan-out | `DefineError`, `GraphDefinitionError`, `ValueError` | `each(label_one, clusters, max_parallel=8)` |
| `reschedule` | `reschedule(state: Handle, *, after_s=None, after=None, mark=None) -> Handle` | terminal continuation state, delay seconds/node, optional mark tool | continuation handle | `DefineError` for bad delay/mark | `return reschedule(state, after_s=60)` |
| `DefineError` | subclass of `GraphDefinitionError` | define-time failure | exception | n/a | `except DefineError as exc: ...` |

## Low-level IR builders

All functions return `Node` unless noted. They do no IO; `freeze(...)`,
`validate(...)`, and an interpreter or backend decide whether the tree can run.

| Symbol | Signature | Parameters | Raises | Example |
|---|---|---|---|---|
| `native` | `native(name: str) -> NativeTool` | native tool key | none | `native("lookup")` |
| `mcp` | `mcp(server: str, tool: str) -> McpTool` | MCP server/tool | none | `mcp("github", "search")` |
| `call` | `call(ref_or_name: str | ToolRef, *, ctx=None, ann=None) -> Node` | native name or `NativeTool`/`McpTool` | `TypeError` for non-tool ref | `call("lookup", ann=Ann(timeout_s=5))` |
| `ident` | `ident() -> Node` | identity leaf | none | `seq(ident(), arr("prompt"))` |
| `arr` | `arr(pure_name: str, args: dict[str, Any] | None = None) -> Node` | registered pure and static JSON args | validation diagnostics for unknown or bad args | `arr("std.pluck", {"key": "summary"})` |
| `sub` | `sub(ref: str, contract=None, *, summary_policy=None) -> Node` | opaque child ref and contract | none | `sub("child", Contract.agent())` |
| `seq` | `seq(*flows: Node | Sequence[Node]) -> Node` | one or more flows, threaded left to right | `ValueError` if empty | `seq(call("a"), call("b"))` |
| `par` / `fanout` | `par(*flows) -> Node`; `fanout(*flows) -> Node` | static branches over same input | `ValueError` if empty | `par(call("a"), call("b"))` |
| `alt` | `alt(pred=None, if_true=None, if_false=None, *, select=None, cases=None, default=None) -> Node` | binary predicate mode or switch mode | `ValueError` for mixed/missing branch forms | `alt("is_ok", call("yes"), call("no"))` |
| `iter_up_to` | `iter_up_to(max: int, body: Node, *, until=None) -> Node` | bounded loop and optional convergence pure | validation rejects bound < 1 | `iter_up_to(3, call("refine"))` |
| `stage` | `stage(planner: str) -> Node` | planner reasoner | none at construction | `stage("planner")` |
| `app` | `app(controller: str, *, tools=None, subflows=None, budget=None, max_rounds=None, ctx=None, summarizer=None) -> Node` | agent controller and inline grants | validation rejects missing controller/context gaps | `app("agent", tools=["lookup"], max_rounds=4)` |
| `Contract.of` | `Contract.of(shape: Shape, summary_policy=None) -> SubContract` | shape and policy | none | `Contract.of(Shape.FEEDBACK)` |
| `Contract.pipeline` | `Contract.pipeline(summary_policy=None) -> SubContract` | policy | none | `Contract.pipeline()` |
| `Contract.dataflow` | `Contract.dataflow(summary_policy=None) -> SubContract` | policy | none | `Contract.dataflow()` |
| `Contract.feedback` | `Contract.feedback(summary_policy=None) -> SubContract` | policy | none | `Contract.feedback()` |
| `Contract.staged` | `Contract.staged(summary_policy=None) -> SubContract` | policy | none | `Contract.staged()` |
| `Contract.agent` | `Contract.agent(summary_policy=SummaryPolicy.RESULT_ONLY) -> SubContract` | policy | none | `Contract.agent()` |

## Derived combinators and continuations

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `race` | `race(*flows: Node | Sequence[Node], reduce=None) -> Node` | branches, optional pure reducer | first-success `par` group | `ValueError` if no branches through helper | `race(call("a"), call("b"))` |
| `hedge` | `hedge(*flows, hedge_ms: int, reduce=None) -> Node` | first branch, delayed rest | hedge group | `ValueError` if `hedge_ms < 0` | `hedge(call("fast"), call("slow"), hedge_ms=100)` |
| `quorum` | `quorum(*flows, k: int, reduce=None) -> Node` | branches and success count | quorum group | `ValueError` if `k` out of range | `quorum([call("a"), call("b")], k=1)` |
| `map_n` | `map_n(*flows: Node, reducer=None) -> Node` | ordinary all-branch fan-out | dataflow node | `ValueError` if no branches | `map_n(call("a"), call("b"))` |
| `map_reduce` | `map_reduce(mappers: Sequence[Node], reduce: str) -> Node` | branches plus reducer pure | dataflow node | `ValueError` if empty | `map_reduce([call("a")], "std.merge")` |
| `vote` | `vote(reasoners: Sequence[str], agg: str) -> Node` | reasoner names and aggregator pure | dataflow node | `ValueError` if empty | `vote(["r1", "r2"], "majority")` |
| `review` | `review(main: Node, reviewer: str, k: int, *, agg=None) -> Node` | main flow, reviewer reasoner, count | seq -> fan-out | `ValueError` if `k < 1` | `review(call("draft"), "reviewer", 2)` |
| `recv` | `recv(channel: str, *, timeout_s=None) -> Node` | input channel and optional timeout | reserved recv leaf | session validation can reject placement | `recv("in")` |
| `emit` | `emit(channel: str, value: str | None = None) -> Node` | output channel and optional constant value | reserved emit leaf | session validation can reject placement | `emit("out")` |
| `human_gate` | `human_gate(*, prompt=None, timeout_s=None) -> Node` | prompt and timeout | human signal wait leaf | none at construction | `seq(human_gate(prompt="approve?"), call("send"))` |
| `delay` | `delay(*, seconds: int) -> Node` | durable sleep seconds | sleep leaf | `ValueError` if `< 1` | `delay(seconds=10)` |
| `check_race_admission` | `check_race_admission(flow: Node, manifest: ToolManifest) -> list[Diagnostic]` | frozen flow and manifest | diagnostics | none | `check_race_admission(deployment.flow, deployment.manifest)` |
| `continue_with` | `continue_with(value: Any) -> dict[str, Any]` | next segment input | sentinel dict | none | `continue_with({"cursor": 1})` |
| `is_continuation` | `is_continuation(value: Any) -> bool` | value | bool | none | `is_continuation(continue_with(1))` |
| `continuation_value` | `continuation_value(value: dict[str, Any]) -> Any` | sentinel dict | wrapped value | `KeyError` if missing key | `continuation_value(continue_with(1))` |
| `run_chained` | `async run_chained(run_segment, input, *, max_segments=1000) -> Any` | async segment runner and initial input | final non-continuation value | `JulepError` when max segments exhausted | `await run_chained(lambda x: one_segment(x), 0)` |

## Sessions

`scan`, `loop`, and `@session` all build a root `Op.LOOP`. `events()` is
single-consumer and ends only on `Closed`.

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `Channel` | `Channel[Tname: str, payload: dict[str, Any] | None = None` | channel name/schema | in-memory port | none | `ch = Channel[str"in"` |
| `Channel.recv` | `async recv(self) -> T` | none | next inbound item | waits until item | `await ch.recv()` |
| `Channel.append` | `append(self, value: T) -> None` | inbound value | None | none | `ch.append("hi")` |
| `Channel.emit` / `drain` | `emit(value) -> None`; `drain() -> list[object]` | outbound value | drained list | none | `ch.emit("x"); ch.drain()` |
| `Session` | `Session[I, Obody: Node, init: object, in_channel: str, out_channel: str` | loop body and initial carrier | session | none | `Session(body=node, init=[], in_channel="in", out_channel="out")` |
| `SessionEvent` | `SessionEvent(kind, channel=None, seq=None, payload=None, turn=None, reason=None, fatal=False)` | normalized event data | event | none | `SessionEvent.emit("out", 1, "hi")` |
| `SessionEvent` factories | `emit`, `turn_started`, `turn_done`, `error`, `closed` | event fields | event | none | `SessionEvent.closed("done").is_closed` |
| `SessionHandle` | protocol: `events`, `send`, `state`, `open_receives`, `close` | live backend handle | async facade | backend errors | `await handle.send({"text":"hi"})` |
| `scan` | `scan(step_flow: Node, init: object, *, in_channel="in", out_channel="out", state_schema=None) -> Session[Any, Any]` | turn flow returning `(carrier, output)` | session | `SessionValidationError` | `chat = scan(turn_flow, init=[])` |
| `loop` | `loop(body: Node, *, init: object, in_channel="in", out_channel="out", state_schema=None) -> Session[Any, Any]` | body value becomes next carrier | session | `SessionValidationError` | `loop(seq(recv("in"), emit("out")), init=None)` |
| `session` | `session(func=None, *, in_channel="in", out_channel="out", state_schema=None)` | straight-line async coroutine sugar | `Session` or decorator | `SessionCompileError` | `@session\nasync def chat(s): ...` |
| `drive_session` | `async drive_session(session, *, inputs, max_turns=1000, env=None) -> tuple[object, list[O]]` | session, input iterable, local env | final carrier and emissions | `JulepError` for overrun; interpreter errors | `await drive_session(chat, inputs=["hi"])` |
| `LocalSessionHandle.open` | `async open(session, *, tools=None, reasoners=None, subs=None, agents=None, planners=None, max_calls=None, mode=STRICT, principal=None, max_turns=100000, channel_capacity=None, env=None, manifest=None) -> LocalSessionHandle` | local effect maps and limits | live local handle | interpreter/session errors | `await LocalSessionHandle.open(chat, reasoners={})` |

## Contracts, freeze, validate, and deploy

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `ToolContract` | `ToolContract(effect: Effect, idempotency: Idempotency)` | asserted/defaulted behavior | contract | enum `ValueError` in `from_json` | `ToolContract(Effect.READ, Idempotency.NATIVE)` |
| `McpAnnotations` | `McpAnnotations(read_only_hint=None, destructive_hint=None, open_world_hint=None, idempotent_hint=None)` | MCP behavior hints | annotation snapshot | none | `McpAnnotations.from_mcp({"annotations": {}})` |
| `definition_hash` | `definition_hash(ref, input_schema, output_schema=None, server_version=None, annotations=None) -> str` | provider definition data | `sha256:<hex>` | JSON serialization errors | `definition_hash(native("t"), {})` |
| `execution_hash` | `execution_hash(tool_definition_hash: str, contract: ToolContract, asserted: bool) -> str` | definition hash plus contract | `sha256:<hex>` | none | `execution_hash(h, c, True)` |
| `FrozenTool` | `FrozenTool(definition_hash, execution_hash, ref, input_schema, contract, output_schema=None, server_version=None, asserted=False)` | frozen manifest entry | frozen tool | none | `FrozenTool.create(native("t"), {}, c)` |
| `FrozenTool.create` | `create(ref, input_schema, contract, output_schema=None, server_version=None, asserted=False, annotations=None) -> FrozenTool` | hashes tool definition and execution contract | frozen tool | JSON serialization errors | `FrozenTool.create(native("t"), {}, c)` |
| `manifest_to_json` | `manifest_to_json(m: ToolManifest) -> dict[str, Any]` | manifest | JSON form | none | `manifest_to_json(deployment.manifest)` |
| `manifest_from_json` | `manifest_from_json(d: dict[str, Any]) -> ToolManifest` | manifest JSON | manifest | `KeyError`, enum `ValueError` for malformed entries | `manifest_from_json(deployment.manifest_json)` |
| `McpToolSpec` | `McpToolSpec(input_schema, annotations=McpAnnotations(), output_schema=None)` | MCP tool schema/hints | snapshot entry | none | `McpToolSpec({})` |
| `McpServerSnapshot` | `McpServerSnapshot(server: str, tools: dict[str, McpToolSpec], version=None)` | server tools/version | snapshot server | none | `McpServerSnapshot("s", {"t": McpToolSpec({})})` |
| `NativeToolSpec` | `NativeToolSpec(input_schema, contract, output_schema=None)` | native tool schema/contract | snapshot entry | none | `NativeToolSpec({}, c)` |
| `McpSnapshot` | `McpSnapshot(servers={}, native={})` | whole tool surface | snapshot | none | `snapshot_from_tools([lookup])` |
| `CapabilityOverrides` | `CapabilityOverrides(contracts={})`; `get(key) -> ToolContract | None` | asserted contracts | overrides | none | `CapabilityOverrides({"t": c}).get("t")` |
| `FreezeResult` | `FreezeResult(flow: Node, manifest: ToolManifest, source_map={})` | freeze output | result | none | `freeze(flow, snapshot).manifest` |
| `freeze` | `freeze(flow: Node, snapshot: McpSnapshot, overrides=None, *, expected_tool_schemas=None) -> FreezeResult` | authored flow and snapshot | frozen flow/manifest | `FreezeError` for cycles, missing tools, schema drift | `freeze(call("lookup"), snapshot_from_tools([lookup]))` |
| `Diagnostic` | `Diagnostic(code, node_id, message, severity="error", hint=None, help_url=None, source=None)` | validation finding | diagnostic | none | `Diagnostic("X", "$", "message")` |
| `validate` | `validate(flow: Node, manifest: ToolManifest | None = None, *, target=None) -> list[Diagnostic]` | flow, optional manifest, target `"flow"`/`"session"` | diagnostics | `ValueError` for bad target | `validate(deployment.flow, deployment.manifest)` |
| `blocking` | `blocking(diags: list[Diagnostic]) -> list[Diagnostic]` | diagnostics | error-severity diagnostics | none | `if blocking(validate(flow)): ...` |
| `explain` | `explain(diagnostics: Iterable[Diagnostic]) -> str` | diagnostics | human text | none | `print(explain(validate(flow)))` |
| `Budget` | `Budget(cost=None, tokens=None, wall_seconds=None)` | cost/token/time envelope | budget | none | `Budget(cost=10)` |
| `Budget.from_dict` | `from_dict(d: dict[str, Any] | None) -> Budget | None` | mapping with `cost`/`usd`, `tokens`, `wallSeconds` | budget | none | `Budget.from_dict({"cost": 1})` |
| `ToolGrant` | `ToolGrant(name, effect=None, idempotency=None, approval=None, max_calls=None)` | granted tool and optional asserted contract | grant | none | `ToolGrant("lookup", Effect.READ, Idempotency.NATIVE)` |
| `CapabilityManifest` | `CapabilityManifest(tools={}, reasoners=set(), models=set(), subflows=set(), memory=set(), network=set(), mcp_servers={}, budget=None, ...)` | allow-lists and budget | manifest | none | `CapabilityManifest.from_dict({"tools": []})` |
| `CapabilityManifest.from_dict` | `from_dict(d: dict[str, Any]) -> CapabilityManifest` | YAML-shaped dict | manifest | enum `ValueError` for bad values | `CapabilityManifest.from_dict({"reasoners":["r"]})` |
| `CapabilityManifest.from_yaml` | `from_yaml(text: str) -> CapabilityManifest` | YAML mapping | manifest | `CapabilityDenied` for missing PyYAML or non-mapping | `CapabilityManifest.from_yaml("tools: []")` |
| `CapabilityManifest.from_file` | `from_file(path: str) -> CapabilityManifest` | file path | manifest | file/YAML errors | `CapabilityManifest.from_file("caps.yaml")` |
| `CapabilityManifest.enforce_compile` | `enforce_compile(flow, manifest=None) -> list[Diagnostic]` | flow and optional frozen manifest | diagnostics | none | `caps.enforce_compile(flow, manifest)` |
| `CapabilityManifest.overrides` | `overrides() -> CapabilityOverrides` | asserted tool grants | overrides | none | `caps.overrides()` |
| `CapabilityManifest.max_call_limits` | `max_call_limits() -> dict[str, int]` | grants | max call map | none | `caps.max_call_limits()` |
| `CapabilityManifest.network_allows` | `network_allows(domain: str) -> bool` | egress domain | bool | none | `caps.network_allows("api.example.com")` |
| `CapabilityManifest.assert_within_budget` | `assert_within_budget(*, cost=0.0, tokens=0) -> None` | current estimates | None | `CapabilityDenied` | `caps.assert_within_budget(cost=0.5)` |
| `check_approval_gates` | `check_approval_gates(flow, manifest, capabilities=None) -> list[Diagnostic]` | frozen flow/manifest/caps | diagnostics | none | `check_approval_gates(flow, manifest, caps)` |
| `snapshot_from_listings` | `snapshot_from_listings(listings, *, versions=None) -> McpSnapshot` | MCP tools/list-shaped dict | snapshot | none | `snapshot_from_listings({"s": {"t": {"inputSchema": {}}}})` |
| `fetch_listings` | `fetch_listings(servers, *, auth=None, timeout_s=10, total_timeout_s=60, allowlist=None) -> dict` | Streamable HTTP server configs and exact URL allow-list | plain `tools/list` data | `McpSnapshotError`, `ImportError`, `RuntimeError` in an active event loop | `fetch_listings(servers, allowlist={servers["memory"]["url"]})` |
| `snapshot_servers` | `snapshot_servers(servers, *, auth=None, timeout_s=10, total_timeout_s=60, allowlist=None) -> McpSnapshot` | same live server configuration | version-pinned freeze snapshot | same as `fetch_listings` | `snapshot_servers(servers, allowlist=urls)` |
| `deploy` | `deploy(flow, snapshot=None, *, tools=None, mcp_servers=None, mcp_listings=None, reasoners=None, capabilities=None, extra_overrides=None, strict=True, mode=STRICT, freeze_timing="deploy_time", snapshot_source=None, target="flow", queue=None) -> Deployment` | explicit snapshot, or exactly one generated source; explicit `snapshot` wins | deployment | `ValueError`, `FreezeError`, `ValidationError` | `deploy(batch, mcp_listings=listings)` |
| `Deployment` | `Deployment(flow, manifest, diagnostics=[], capabilities=None, mode=STRICT, freeze_timing="deploy_time", ...)` | compiled artifact | deployment | none | `deployment.artifact_hash` |
| `Deployment.refresh` | `refresh(snapshot=None) -> Deployment` | fresh snapshot or stored source | new deployment | `ValueError`, deploy errors | `deployment.refresh(new_snapshot)` |
| `Deployment.run` | `async run(client, *, session_id, input=None, task_queue="julep", policy=None, principal=None) -> Any` | Temporal client and run input | workflow result | `ValueError` in dev mode; Temporal errors | `await deployment.run(client, session_id="run-1")` |
| `Deployment.adry_run` / `dry_run` | `adry_run(value, *, mcp_call=None, reasoners=None) -> Result`; sync equivalent | local value, MCP seam, and fake reasoners | interpreter result | effect handler and interpreter errors | `deployment.adry_run(batch, mcp_call=fake, reasoners={...})` |
| `Deployment.publish` | `publish(store_or_url, *, signing_key=None) -> dict[str, Any]` | CAS store/url and optional signing key | bundle record | bundle/CAS/signing errors | `deployment.publish(".julep/cas")` |

`mode="dev"` returns deployments with would-block diagnostics in
`Deployment.prod_gap`; Temporal `Deployment.run(...)` refuses dev mode.
`freeze_timing` is `"deploy_time"` or `"per_run"`.

Import live snapshot helpers from `julep.mcp_snapshot`. They use the official
MCP SDK from `julep[mcp]` and never follow redirects outside the configured
endpoint allow-list.

`mcp_tool` schemas and effect/idempotency behavior always come from the frozen
snapshot; its constructor has no contract override arguments. Handle-valued
keyword calls synthesize a compiler-owned `std.record` node. Capability defaults
are derived from the resolved frozen tool set when `capabilities` is omitted.
`InMemoryEnv` also accepts `mcp_call=`, so an MCP-only deployment needs no
native `tools=` map for local execution.

## MCP authentication

Julep ships the verifier half for application-owned MCP servers and a
batteries-included HTTP caller. Authoring and serving the MCP server itself
remain application responsibilities.

| Symbol | Signature | Behavior |
|---|---|---|
| `McpAuthConfig` | `McpAuthConfig(signing_key, issuer, kid, ttl_s=300)` | Ed25519 signing config; `ttl_s` must be `1..300`. The key is the same 64-hex seed or seed-file form as `JULEP_BUNDLE_SIGNING_KEY`; `from_env()` reads `JULEP_MCP_SIGNING_KEY`, `JULEP_MCP_ISSUER`, `JULEP_MCP_KID`, and `JULEP_MCP_TTL_S`. |
| `mint_token` | `mint_token(cfg, *, server_id, tool, scopes, idempotency_key, principal) -> str` | Creates an EdDSA JWT. `aud` is the stable logical server id, not its URL. Claims include `iss`, `aud`, typed `sub`/`tenant`/`scope`, `tool`, `idk`, `iat`, `exp`, and `jti`; the JOSE header includes `kid`. Only selected subject/tenant fields are copied from the principal. |
| `verify_token` | `verify_token(token, *, verify_keys, audience, required_scopes=(), idempotency_key, issuer=None, leeway_s=30) -> VerifiedToken` | Pins `algorithms=["EdDSA"]`, verifies key id, audience, issuer/time claims and scopes, and requires JWT `idk` to equal the request's actual `Idempotency-Key`. |
| `verify_keys_from_env` | `verify_keys_from_env() -> dict[str, Ed25519PublicKey]` | Parses `JULEP_MCP_VERIFY_KEYS` as comma-separated `kid:base64pub` entries. |
| `FastMCPTokenVerifier` | `FastMCPTokenVerifier(verify_keys, audience, required_scopes=(), issuer=None, leeway_s=30)` | Adapter for the official MCP server auth provider. Pair with the middleware below because the provider interface does not expose request headers. |
| `asgi_auth_middleware` | `asgi_auth_middleware(app, *, verify_keys, audience, required_scopes=(), issuer=None, leeway_s=30) -> ASGIApp` | Requires bearer auth and `Idempotency-Key`, verifies their binding, and stores `VerifiedToken` on the ASGI scope. |
| `http_mcp_caller` | `http_mcp_caller(servers, auth=None) -> McpCaller` | Calls Streamable HTTP servers, always sends `Idempotency-Key` equal to the deterministic activity cid, and adds a minted bearer token when auth is configured. |

This surface uses PyJWT with the allowed algorithm pinned to EdDSA and is
installed by `julep[mcp]`. The principal mapping is never serialized wholesale.

## Staged plans and agent-loop extraction

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `estimate_cost` | `estimate_cost(plan: Node) -> float` | candidate plan | estimated cost | none | `estimate_cost(seq(call("a"), call("b")))` |
| `referenced_tool_keys` | `referenced_tool_keys(plan: Node) -> list[str]` | plan | unique tool keys | none | `referenced_tool_keys(call("lookup"))` |
| `bind_plan_to_manifest` | `bind_plan_to_manifest(plan: Node, manifest: ToolManifest) -> Node` | plan and parent manifest | copied, bound plan | `PlanRejected` | `bind_plan_to_manifest(plan, manifest)` |
| `validate_plan` | `validate_plan(plan: Node, parent: CapabilityManifest, manifest=None) -> list[Diagnostic]` | plan, parent caps, optional manifest | diagnostics | none | `validate_plan(plan, caps, manifest)` |
| `admit_plan` | `admit_plan(plan: Node, parent: CapabilityManifest, manifest=None) -> Node` | plan and parent gates | admitted plan | `PlanRejected` | `admit_plan(plan, caps)` |
| `Decision` | `FINISH`, `ESCALATE`, `CALL`, `SUB`, `CONTROLLER_ERROR` | controller action kind | enum | enum `ValueError` | `Decision("call")` |
| `AgentConfig` | `AgentConfig(max_rounds=24, budget=None, mode=STRICT, continue_as_new_after=0, think_cost=2.0, permissive_controller=False, ctx=None, summarizer=None)` | loop policy | config | enum `ValueError` in `from_json` | `AgentConfig(max_rounds=4)` |
| `AgentState` | `AgentState(round=0, spent=0.0, last=None, trace=[], call_counts={}, summary=None)` | mutable loop state | state | JSON errors in fingerprinting | `AgentState(last={"q": "hi"})` |
| `Decision` helpers | `interpret_reasoner_reply(reply, *, strict=True) -> RoundAction` | controller reply | normalized action | none | `interpret_reasoner_reply({"done": True})` |
| `generalize_trace_to_plan` | `generalize_trace_to_plan(trace: list[TraceEntry]) -> Node` | observed trace | pipeline candidate | enum `ValueError` for bad shape strings | `generalize_trace_to_plan([])` |
| `extract_plan` | `extract_plan(trace, parent, manifest=None) -> tuple[Node, list[Diagnostic]]` | trace and parent gates | candidate and diagnostics | none | `extract_plan(state.trace, caps)` |
| `promote_plan` | `promote_plan(trace, parent, manifest=None) -> Node` | observed trace and gates | admitted plan | `PlanRejected` | `promote_plan(trace, caps)` |

## Agent facade

`Agent` wraps an `app(...)` node plus local, Temporal, DBOS, and CMA adapters.
It is a facade over the same frozen IR and capability gates, not a separate
language.

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `Agent` | `Agent(reasoner: str \| Reasoner, tools: Sequence[FlowLike | SplitCapability] = (), *, name=None, llm=None, budget_cost=None, max_rounds=24, instructions=None, mode=STRICT, langfuse_export=None)` | model slug or a `Reasoner` object (its model/system drive the controller), tool/flow/agent capabilities, local LLM seam, policy | agent facade | `ValidationError`, `TypeError` | `agent = Agent("anthropic:claude-haiku-4-5", [lookup], llm=fake)` |
| `Agent.name` | property `str` | none | controller name | none | `agent.name` |
| `Agent.to_ir` | `to_ir() -> Node` | none | app node | none | `agent.to_ir()` |
| `Agent.with_tools` | `with_tools(*, add=(), remove=()) -> Agent` | add/remove capabilities | new agent | same as constructor | `agent.with_tools(add=[other_tool])` |
| `Agent.without` | `without(*tools: FlowLike | SplitCapability | str) -> Agent` | capabilities/names | new agent | same as constructor | `agent.without("lookup")` |
| `Agent.replace` | `replace(*, reasoner: str \| Reasoner \| None = None, budget_cost=_KEEP, max_rounds=None, instructions=_KEEP, mode=_KEEP, llm=_KEEP) -> Agent` | selected config overrides (a `Reasoner` object drives model/system like the constructor) | new agent | same as constructor | `agent.replace(max_rounds=8)` |
| `Agent.arun` / `run` | `async arun(input, *, principal=None) -> Result`; `run(input, *, principal=None) -> Result` | one-shot input and optional run principal | typed run dict | `RuntimeError` if sync call inside event loop; deploy/interpreter errors | `agent.run({"task": "x"}).output` |
| `Agent.arun_on_cma` / `run_on_cma` | `async arun_on_cma(input, *, client, environment=None) -> Result`; sync wrapper | CMA client and environment | typed run dict | `RuntimeError`, CMA/tool errors | `await agent.arun_on_cma("hi", client=cma)` |
| `Agent.open` | `async open(*, session, backend="local", principal=None, client=None, task_queue="julep", policy=None, history_threshold=None, channel_capacity=None, session_id=None, environment=None) -> SessionHandle` | session plus backend config | live handle | `ValueError`, `ValidationError`, `NotImplementedError` for Temporal sub-cap auto-wire | `await agent.open(session=chat, backend="local")` |
| `Agent.open_session` | sync wrapper for non-local backends | same as `open` | `SessionHandle` | `RuntimeError` for local or running loop | `agent.open_session(session=chat, backend="temporal", client=client)` |
| `Agent.deployment` | `deployment() -> Deployment` | none | compiled deployment | deploy errors | `agent.deployment().artifact_hash` |
| `Agent.sub_deployments` | `sub_deployments() -> dict[str, Deployment]` | none | child artifacts | deploy errors | `agent.sub_deployments()` |
| `Agent.split_children` | `split_children() -> dict[str, SplitCapability]` | none | split child markers | none | `agent.split_children()` |
| `Agent.check` | `check() -> list[Diagnostic]` | none | deploy diagnostics | freeze errors | `agent.check()` |
| `Agent.deploy` | `async deploy(client, *, session_id, input=None, task_queue="julep", policy=None, principal=None) -> Any` | Temporal client and run input | workflow result | `NotImplementedError` with sub-capabilities; deploy/runtime errors | `await agent.deploy(client, session_id="run-1")` |
| `AGENT_REPLY_SCHEMA` | JSON schema constant | closed controller vocabulary | schema dict | none | `Reasoner("agent", "m", reply=AGENT_REPLY_SCHEMA)` |

`Result` returned by `Agent.run` is a `dict` with properties `output`, `status`,
`ok`, `trace`, `cost`, `rounds`, `reason`, and `prod_gap`.

## Typed and DAG escape hatches

The package root exports `as_flow`; the full typed wrapper lives in
`julep.typed`.

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `as_flow` | `as_flow(x: FlowLike | Node) -> Flow` | lowerable value or IR node | typed wrapper | none | `as_flow(lookup).local_name` |
| `Graph` | `Graph(input_name="__input__", output_name=None, source=None)` | single-assignment graph | graph | `GraphDefinitionError` for reserved explicit output | `g = Graph(); g.add_step("tool", "lookup", output="hit")` |
| `Graph.add_step` | `add_step(kind, ref, *, inputs=(), output, contract=None, ann=None, source=None, args=None, tool=None) -> StepNode` | tool/think/pure/passthrough step | step | `GraphDefinitionError` | `g.add_step(StepKind.TOOL, "lookup", output="hit")` |
| `Graph.add_cond` | `add_cond(pred, *, inputs=(), output, if_true, if_false, source=None, branch_subject=None) -> StepNode` | binary branch graphs | step | `GraphDefinitionError` | `g.add_cond("is_ok", output="o", if_true=a, if_false=b)` |
| `Graph.add_switch` | `add_switch(select, *, inputs=(), output, cases, default=None, source=None, branch_subject=None) -> StepNode` | selector cases | step | `GraphDefinitionError` | `g.add_switch("route", output="o", cases={"a": a})` |
| `Graph.add_each` | `add_each(body, *, items, output, max_parallel=None, reducer=None, const_captures=None, source=None) -> StepNode` | dynamic fan-out graph | step | `GraphDefinitionError`, warning for oversized captures | `g.add_each(body, items="items", output="outs")` |
| `StepKind` | `TOOL`, `THINK`, `PURE`, `PASSTHROUGH`, `COND`, `SWITCH`, `EACH` | DAG step kind | enum | enum `ValueError` | `StepKind("tool")` |
| `InputEdge` | `InputEdge(name: str, source: str)` | data edge | edge | none | `InputEdge("hit", "hit")` |
| `StepNode` | `StepNode(kind, ref, inputs, output, contract=None, ann=None, source=None, args=None, order=0, ...)` | compiled step record | step | none | `StepNode(StepKind.PURE, "std.pluck", (), "x")` |
| `compile_dag` | `compile(graph: Graph) -> Node` | DAG | IR | `GraphDefinitionError` | `compile_dag(g)` |
| `compile_env_dag` | `compile_env(graph: Graph, initial_fields: Sequence[str]) -> Node` | env graph and initial fields | IR | `GraphDefinitionError` | `compile_env_dag(g, ["__input__"])` |

## Pure interpreter and execution policy

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `ExecutionPolicy` | `ExecutionPolicy(tool_timeout_s=30, reasoner_timeout_s=120, plan_timeout_s=120, sub_task_timeout_s=3600, agent_task_timeout_s=3600, idempotent_max_attempts=5, write_max_attempts=3, reasoner_max_attempts=4, initial_retry_s=1.0, retry_backoff=2.0, max_retry_interval_s=60, trace_content_refs=False, max_parallel=None)` | backend timeouts/retries/projection | policy | none | `ExecutionPolicy(reasoner_max_attempts=1).to_json()` |
| `ExecutionPolicy.from_json` | `from_json(d: dict[str, Any] | None) -> ExecutionPolicy` | policy JSON | policy | none | `ExecutionPolicy.from_json({"maxParallel": 4})` |
| `Env` | protocol with `run_call`, `invoke_reasoner`, `run_sub`, `run_agent`, `compile_plan`, `human_gate`, `sleep`, `recv`, `emit`, `gather`, `race_first` | interpreter effect boundary | protocol | implementation-defined | implement for a backend |
| `InMemoryEnv` | `InMemoryEnv(manifest, emitter, *, tools=None, mcp_call=None, reasoners=None, subs=None, agents=None, planners=None, gate=None, sleeper=None, max_parallel=None, max_calls=None, mode=STRICT, registry=None, principal=None, root_run_id=None, segment_seq=0, inbound=None)` | local effect maps and limits | env | `CapabilityDenied`, `KeyError`, handler errors | `InMemoryEnv({}, emitter, mcp_call=fake)` |
| `interpret` | `async interpret(node, value, env, causes=(), *, principal=None, root_run_id=None, segment_seq=None) -> Result` | IR, input, env, optional run identity | `Result(value, event_id, attrs, reported_cost)` | framework, pure, handler errors | `await interpret(flow, value, env)` |
| `Result` | `Result(value: Any, event_id: str | None = None, attrs=None, reported_cost=None)` | interpreter result | value envelope | none | `result.value` |
| `RunPrincipal` | `dict[str, Any]` | opaque tenant/credential reference, never secret | alias | none | `principal={"tenant": "acme"}` |
| `WorkerContext` | `WorkerContext(tool_urls={}, mcp_call=None, llm=None, on_attempt=None, resolve_qos=default_resolve_qos, blob_store=None, session_store=None, capabilities=None, registry=None, http_timeout_s=30.0, principal_headers=None, count_tokens=None, subflows={}, agents={}, trajectory_sink=None, trajectory_blob_store=None)` | process-global worker dependencies | context | none | `WorkerContext(llm=make_llm_caller())` |

## Temporal, worker, DBOS, and CMA runtime

Top-level Temporal exports exist only when `HAVE_TEMPORAL` is true:
`FlowWorkflow`, `SessionWorkflow`, `AgentWorkflow`, `FlowInput`, `SessionInput`,
`AgentInput`, `run_flow`, `start_flow`, `TemporalSessionHandle`, `build_worker`,
`run_worker`, `callTool`, `invokeReasoner`, `compilePlan`, `verifyPures`,
`resolveSubflow`, `resolveAgentSpec`, and `resolveRuntimeCapabilities`.

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `FlowInput` | `FlowInput(session_id, input=None, flow_json=None, manifest_json=None, pinned_pures=None, max_call_limits=None, call_counts=None, ref=None, policy=None, principal=None, bundle=None, root_run_id=None, segment_seq=0)` | Temporal flow workflow input | dataclass | none | `FlowInput("run-1", flow_json=deployment.flow_json)` |
| `SessionInput` | `SessionInput(session_id, flow_json, manifest_json, init, max_call_limits=None, call_counts=None, pinned_pures=None, budget=None, spent=0.0, bundle=None, in_channel="in", out_channel="out", policy=None, principal=None, root_run_id=None, segment_seq=0, history_threshold=None, channel_capacity=None, ...)` | Temporal session workflow input | dataclass | none | created by `Agent.open(..., backend="temporal")` |
| `AgentInput` | `AgentInput(controller, session_id, input=None, config=None, granted_tools=None, granted_tools_unconstrained=False, granted_subflows=None, granted_contracts=None, state=None, state_cursor=None, use_session_store=False, policy=None, resolve_spec=True, principal=None, root_run_id=None, segment_seq=0)` | Temporal agent workflow input | dataclass | none | created by runtime |
| `run_flow` | `async run_flow(client, flow_json, manifest_json, *, session_id, input=None, task_queue="julep", policy=None, pinned_pures=None, max_call_limits=None, principal=None, root_run_id=None, bundle=None) -> Any` | connected Temporal client and frozen artifact | workflow result | Temporal/runtime errors | `await run_flow(client, d.flow_json, d.manifest_json, session_id="run-1")` |
| `start_flow` | same params as `run_flow` | connected client and artifact | workflow handle | Temporal errors | `handle = await start_flow(client, d.flow_json, d.manifest_json, session_id="run-1")` |
| `TemporalSessionHandle` | `TemporalSessionHandle(wfhandle, *, in_channel="in", out_channel="out", poll_s=0.02)` | workflow handle and channels | session handle | backend errors | returned by `Agent.open(..., backend="temporal")` |
| `build_worker` | `build_worker(client, context, *, task_queue=DEFAULT_TASK_QUEUE, min_batch_window_s=0.0, **worker_kwargs) -> Worker` | Temporal client, `WorkerContext`, queue, SDK kwargs | worker | Temporal/import/config errors | `build_worker(client, WorkerContext(llm=llm))` |
| `run_worker` | `async run_worker(*, target_host="localhost:7233", namespace="default", task_queue=DEFAULT_TASK_QUEUE, tool_urls=None, mcp_call=None, llm=None, capabilities=None, subflows=None, agents=None, blob_store=None, session_store=None, trajectory_sink=None, trajectory_blob_store=None, on_attempt=None, http_timeout_s=30.0, **worker_kwargs) -> None` | standalone worker config | never until cancelled | Temporal/runtime errors | `await run_worker(llm=llm)` |
| `WorkerServeSettings` | `WorkerServeSettings(context_factory, address="localhost:7233", namespace="default", task_queue=DEFAULT_TASK_QUEUE, ..., application=None, runtime_declarations_hash=None, redaction=None)` | container worker settings; application/hash are optional paired cross-checks | settings | `ValueError` for an unpaired cross-check | `WorkerServeSettings.from_env(env)` |
| `serve` | `async serve(settings: WorkerServeSettings, *, shutdown_event=None) -> None` | settings and optional test shutdown event | None | `JulepError` without `temporalio`, factory errors | `await serve(WorkerServeSettings.from_env())` |
| `HealthServer` | `HealthServer(port: int, *, host="0.0.0.0")` | probe listener | server with `/healthz`, `/readyz` | `RuntimeError` if `port` before start | `await HealthServer(8080).start()` |
| `load_context_factory` | `load_context_factory(spec: str) -> Callable[[], Any]` | `module:attr` spec | callable | `ValueError` | `load_context_factory("app.worker:make_context")` |
| Activity inputs | `CallToolInput`, `InvokeReasonerInput`, `ResolveQoSInput`, `CompilePlanInput`, `LoadStateInput`, `CommitStateInput`, `LoadValueInput`, `CommitValueInput`, `PutBlobInput` | dataclass payloads for activity wrappers | payload | none | `CallToolInput({"kind":"native","name":"t"}, {}, "cid")` |
| Activities | `callTool`, `invokeReasoner`, `compilePlan`, `verifyPures`, `resolveSubflow`, `resolveRuntimeCapabilities`, `resolveAgentSpec` | activity payloads | effect results | worker context and policy errors | normally called by workflows |
| `CMAEvent` | `CMAEvent(kind, tool=None, input=None, call_id=None, output=None, reason=None, usage=None)` | normalized managed-agent event | event | none | `CMAEvent("terminal", output="ok")` |
| `CMAClient` | protocol `create_session(*, agent, environment, session_cid, input=None) -> CMASession` | CMA adapter seam | session | adapter errors | implement for provider |
| `CMASession` | protocol `events`, `tool_result`, `tool_error`, `cancel` | one provider session | async event stream | adapter errors | `async for ev in session.events(): ...` |
| `manifest_to_custom_tools` | `manifest_to_custom_tools(tool_names, *, input_schemas=None, descriptions=None) -> list[dict[str, Any]]` | granted tool names | CMA custom tools | none | `manifest_to_custom_tools(["lookup"])` |
| `drive_cma_agent_loop` | `async drive_cma_agent_loop(*, input, cfg, session, call_tool, granted=None, contracts=None, state=None, session_cid="cma") -> dict[str, Any]` | CMA session and same gates as local loop | terminal result | CMA/tool errors | `await drive_cma_agent_loop(input=x, cfg=cfg, session=s, call_tool=fn)` |
| `CMAAgentEnv` | `CMAAgentEnv(inner, *, client, environment=None, tools, cfg, granted=None, contracts=None, custom_tools=None)` | wraps an `Env`, replacing only `run_agent` | env | backend errors | `CMAAgentEnv(inner, client=c, tools={}, cfg=cfg)` |

DBOS exports are available from `julep.execution` only when
`HAVE_DBOS` is true; they are not re-exported by the package root.

## Projection and observability

Projection is derived from execution history; it is not the source of
durability.

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `ProjectionEvent` | `ProjectionEvent(event_id, type, node, cid, ts, causes=(), value_ref=None, shape=None, cost=None, error=None, attrs={})` | one activation fact | event | enum `ValueError` in `from_json` | `ProjectionEvent.from_json(e.to_json())` |
| `ProjectionEmitter` | `ProjectionEmitter(store: ProjectionStore, clock=None)` | append store and optional clock | emitter | store errors | `emitter = ProjectionEmitter(InMemoryProjection())` |
| `ProjectionEmitter.plan` | `plan(node, cid, causes=(), shape=None, attrs=None) -> str` | planned activation | event id | store errors | `emitter.plan("$", "$@1")` |
| `ProjectionEmitter.did` | `did(node, cid, value=None, cost=None, shape=None, causes=(), attrs=None) -> str` | successful activation | event id | value JSON/store errors | `emitter.did("$", "$@1", {"ok": True})` |
| `ProjectionEmitter.fail` | `fail(node, cid, error, causes=()) -> str` | failed activation | event id | store errors | `emitter.fail("$", "$@1", "boom")` |
| `ProjectionStore` | protocol `append(event)`, `events() -> list[ProjectionEvent]` | queryable store | protocol | implementation-defined | `InMemoryProjection()` |
| `ProjectionSink` | protocol `append(event) -> None` | write-only sink | protocol | implementation-defined | pass to `TeeStore` |
| `InMemoryProjection` | `InMemoryProjection()` | local store | store | none | `store.cost_by_shape()` |
| `PostgresProjection` | `PostgresProjection(execute=None)` | SQL execute callable | sink/store buffer | `RuntimeError` if no execute | `PostgresProjection(execute=cursor.execute)` |
| `TeeStore` | `TeeStore(primary: InMemoryProjection, *sinks: ProjectionSink)` | primary plus sinks | store | sink errors propagate | `TeeStore(InMemoryProjection(), sink)` |
| `ValueStore` | `ValueStore()` with `put`, `get`, `has` | content-addressed values | store | `KeyError` on missing get | `ValueStore().put({"x": 1})` |
| `SpanData` | `SpanData(name, cid, node, start_ts, end_ts, status, parents, error=None, attrs={}, cost=None, value_ref=None, planned_event_id=None, terminal_event_id=None)` | OTel-ready span data | span record | none | `to_otel_spans(store.events())` |
| `to_otel_spans` | `to_otel_spans(events: list[ProjectionEvent]) -> list[SpanData]` | projection events | span data | none | `to_otel_spans(store.events())` |

## Provider resilience and QoS

| Symbol | Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|---|
| `ErrorClass` | `TRANSIENT`, `TIMEOUT`, `CONFIG`, `MODEL_BEHAVIOR` | model-call failure class | enum | enum `ValueError` | `ErrorClass("transient")` |
| `classify_error` | `classify_error(exc: BaseException) -> ErrorClass` | provider exception | class | none | `classify_error(TimeoutError())` |
| `AttemptRecord` | `AttemptRecord(model, provider, outcome, detail="", tier=None, batch_id=None)` | one model attempt | record | none | `AttemptRecord("m", "anthropic", "ok").ok` |
| `ResiliencePolicy` | `ResiliencePolicy(fallbacks={}, transient_attempts=2, timeout_attempts=1, initial_backoff_s=0.5, backoff_factor=2.0, max_backoff_s=8.0)` | fallback/retry policy | policy | none | `ResiliencePolicy({"m": ["m2"]}).candidates("m")` |
| `CircuitBreaker` | `CircuitBreaker(*, failure_threshold=5, cooldown_s=30.0, clock=time.monotonic)` | per-provider breaker | breaker | `ValueError` if threshold < 1 | `breaker.allow("anthropic")` |
| `summarize_attempts` | `summarize_attempts(attempts: Sequence[AttemptRecord]) -> str` | attempt records | one-line string | none | `summarize_attempts([AttemptRecord("m","p","ok")])` |
| `QoSTier` | `PRIORITY`, `STANDARD`, `FLEX`, `BATCH` | dispatch tier | enum | enum `ValueError` | `QoSTier("BATCH")` |
| `ReasonerDispatch` | `ReasonerDispatch(qos=QoSTier.STANDARD, batch_id=None)` | recorded dispatch choice | dispatch record | none | `ReasonerDispatch(qos=QoSTier.FLEX)` |
| `default_resolve_qos` | `default_resolve_qos(reasoner, node_ann, principal, load=None, *, timeout_s=None, min_batch_window_s=None) -> QoSTier` | reasoner, `Ann`, principal hints | QoS tier | enum `ValueError` internally clamped to standard/flex | `default_resolve_qos(None, Ann(batchable=True), {"qos": "BATCH"})` |
| `make_llm_caller` | `make_llm_caller(*, default_provider="anthropic", acompletion=None) -> Callable[..., Awaitable[Any]]` | provider and optional test completion fn | worker `LlmCaller` | lazy `ImportError`, provider errors | `WorkerContext(llm=make_llm_caller())` |
| `make_local_reasoner` | `make_local_reasoner(*, default_provider="anthropic", acompletion=None) -> Callable[[str, Any], Awaitable[Any]]` | provider/test seam | facade `llm` callable | lazy `ImportError`, provider errors | `Agent("anthropic:m", llm=make_local_reasoner())` |
| `make_resilient_llm_caller` | `make_resilient_llm_caller(*, policy, breaker=None, on_attempt=None, classifier=classify_error, default_provider="anthropic", acompletion=None, sleep=asyncio.sleep) -> Callable[..., Awaitable[Any]]` | fallback policy and hooks | resilient `LlmCaller` | `ResilienceExhausted`, config/provider errors | `make_resilient_llm_caller(policy=ResiliencePolicy())` |

## Errors and exceptions

| Exception | Constructor | Raised by | Example |
|---|---|---|---|
| `JulepError` | `JulepError(*args)` | base framework error | `except JulepError:` |
| `ValidationError` | `ValidationError(diagnostics: list[Diagnostic])` | strict `deploy`, facade checks | `exc.diagnostics` |
| `FreezeError` | `FreezeError(*args)` | `freeze`, manifest binding | unresolved tool |
| `AdmissionError` | `AdmissionError(*args)` | race admission callers | illegal race branch |
| `PureDriftError` | `PureDriftError(*args)` | `verifyPures` | mismatched pure source |
| `RaceAllFailed` | `RaceAllFailed(failures: Iterable[BaseException])` | race-family runtime | `exc.failures` |
| `BudgetExceeded` | `BudgetExceeded(*args)` | agent/plan budget paths | over budget |
| `PlanRejected` | `PlanRejected(reasons: Iterable[str])` | staged plan admission | `exc.reasons` |
| `CapabilityDenied` | `CapabilityDenied(*args)` | capability compile/runtime gates | denied egress/tool |
| `PrincipalRequired` | `PrincipalRequired(*args)` | worker-supplied callers | missing principal |
| `ResilienceExhausted` | `ResilienceExhausted(attempts: list[AttemptRecord])` | resilient LLM caller | `exc.attempts` |
| `UnsupportedShapeError` | `UnsupportedShapeError(*args)` | backend preflight | unsupported op |
| `SessionCompileError` | `SessionCompileError(*args)` | `@session` AST lifting | non-liftable coroutine |
| `SessionValidationError` | `SessionValidationError(*args)` | `scan`/`loop` validation | bad LOOP shape |

## CLI and configuration

CLI entry points:

| Script | Entry point | Scope |
|---|---|---|
| `julep` | `julep.cli.main:main` | module-level developer CLI over Python source |
| `python -m julep.cli.artifact` | `julep.cli.artifact:main` | Direct module fallback for JSON artifact plumbing |

`julep artifact` and `julep worker` commands and flags:

| Command | Verified signature |
|---|---|
| `validate` | `julep artifact validate <flow_json> [--manifest <path>]` |
| `freeze` | `julep artifact freeze <flow_json> <snapshot_json> [--caps <path>]` |
| `inspect` | `julep artifact inspect <flow_json> [--manifest <path>] [--caps <path>]` |
| `run-local` | `julep artifact run-local <flow_json> <input_json> [--mode strict|dev]` |
| `graph` | `julep artifact graph <flow_json>` |
| `worker` | `julep worker [--smoke-test-seconds seconds]` |

`julep` commands and flags:

| Command | Verified signature |
|---|---|
| root | `julep [--version]` |
| `ls` | `julep ls [selector] [--exclude expr]` |
| `show` | `julep show <name>` |
| `graph` | `julep graph [selector] [--exclude expr]` |
| `run` | `julep run <name-or-path.ctx> [--input JSON] [--run-id id] [--env name]` |
| `deploy` | `julep deploy [selector] [--exclude expr] [--env name]` |
| `plan` | `julep plan [--env name] [--json] [--mcp-snapshot]` |
| `apply` | `julep apply --env name [--publish-only] [--mcp-snapshot]` |
| `status` | `julep status [selector] [--exclude expr] [--env name] [--remote] [--api-url URL] [--api-key KEY] [--limit N]` |
| `serve api` | `julep serve api [--host HOST] [--port PORT] [--migrate]` |
| `db migrate` | `julep db migrate [--dsn DSN]` |
| `db sweep` | `julep db sweep --older-than SECONDS [--dsn DSN]` |
| `schedule apply` | `julep schedule apply [--env name]` |
| `schedule ls` | `julep schedule ls [--env name]` |
| `schedule rm` | `julep schedule rm <name> [--env name]` |
| `worker` | `julep worker [--smoke-test-seconds seconds]` (`0` continuous; positive smoke/poll/drain) |
| `lint` | `julep lint [selector] [--exclude expr] [--fail-severity error|warning|info]` |
| `test` | `julep test [selector] [--exclude expr] [--dry-run]` |
| `eval` | `julep eval <ctx_path> [--env name] [--limit N] [--tag tag] [--sample-name name] [--json path] [--baseline path] [--llm-caller module:attr]` |
| `trace` | `julep trace <run_id> [--remote] [--api-url URL] [--api-key KEY]` |
| `doctor` | `julep doctor` |
| `chat` | `julep chat <name> [--env local]` |
| `trigger` | `julep trigger <name> <event> [--channel name]` |
| `listen` | `julep listen <name> --forward-to URL` |

Selection forms accepted by `julep` are documented in [CLI](/docs/guides/using-the-cli).

Environment knobs verified in source:

| Variable | Used by | Meaning |
|---|---|---|
| `JULEP_SOURCE_CAPTURE` | `dsl.py` | `1` enables `SourceSpan` capture for diagnostics |
| `WORKER_CONTEXT_FACTORY` | `WorkerServeSettings.from_env` | required `module:attr` factory returning `WorkerContext` |
| `TEMPORAL_ADDRESS` | worker host | Temporal frontend, default `localhost:7233` |
| `TEMPORAL_NAMESPACE` | worker host | namespace, default `default` |
| `TEMPORAL_TASK_QUEUE` | worker host | task queue, default `julep` |
| `TEMPORAL_API_KEY` | worker host | Temporal Cloud API key; setting it defaults TLS on |
| `TEMPORAL_TLS` | worker host | boolean TLS override |
| `WORKER_GRACEFUL_SHUTDOWN_S` | worker host | SIGTERM drain window, default `30` |
| `WORKER_MAX_CONCURRENT_ACTIVITIES` | worker host | SDK activity slots |
| `WORKER_MAX_CONCURRENT_WORKFLOW_TASKS` | worker host | SDK workflow-task slots |
| `WORKER_HEALTH_PORT` | worker host | probe port serving `/healthz` and `/readyz` |
| `STORE_URL` | bundle worker/verification | CAS URL for bundle resolution |
| `JULEP_BUNDLE_SIGNING_KEY` | bundle publish | signing seed or path |
| `JULEP_BUNDLE_ALLOWED_SIGNERS` | bundle resolution | comma-separated signer allow-list |
| `JULEP_BUNDLES` | bundle worker | bundle refs to load from `STORE_URL` |
| `JULEP_PURE_NATIVE_DEPS` | pure dependency admission | comma-separated pure names allowed to use native dependency tier |
| `JULEP_WASM_FUEL` | wasm executor | instruction fuel, default from executor |
| `JULEP_WASM_CACHE_DIR` | wasm executor | compiled component cache directory |
| `JULEP_WASM_EPOCH_MS` | wasm executor | optional epoch interruption interval |
| `JULEP_NATIVE_VENV_CACHE_DIR` | native venv executor | cache directory for native-venv pure tier |
| `ANTHROPIC_API_KEY` | Anthropic CMA client | fallback API key |
| `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | Langfuse exporter | OTLP endpoint credentials |
| `LANGFUSE_CAPTURE_IO` | Langfuse exporter | `1`/`true` captures IO |
| `LANGFUSE_PROJECT_ID` | `julep trace` deep links | optional project deep-link component |
<!-- generated by julep-docs-matrix: julep/reference -->

<!-- ported-by julep-docs-site: reference/python-api -->
