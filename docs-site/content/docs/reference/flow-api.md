---
title: "@flow API"
description: "The @flow authoring API: decorators, combinators, and registration."
---

Start with `@flow`. A decorated Python function runs once at define time with
`Handle` values, appends a single-assignment DAG, compiles through
`julep.dag`, and lowers to the same `Node` IR emitted by the raw
combinator kernel. The typed layer in `julep.typed` is an
authoring-only wrapper over that IR and disappears before freeze.

Related: [Authoring](/docs/guides/authoring-flows), [Concepts](/docs/concepts/model), [typed-flow design](/docs/internals/typed-flow-calculus), [README quickstart](/docs#quickstart-10-minutes-no-api-key).

## Minimal Flow

```python
from typing import TypedDict
from julep import Reasoner, deploy, flow, pure, think, tool

class Reply(TypedDict):
    reply: str
@tool(effect="read", idempotent=True)
def lookup(ticket: str) -> dict[str, str]:
    return {"ticket": ticket, "queue": "billing"}
@pure("prompt")
def prompt(hit: dict[str, str]) -> dict[str, str]:
    return {"queue": hit["queue"]}
SUPPORT_REPLY = Reasoner("support_reply", "anthropic:claude-haiku-4-5-20251001", reply=Reply)
@flow
def triage(ticket: str) -> dict[str, str]:
    hit = lookup(ticket, retries=2, timeout_s=5)
    request = prompt(hit)
    answer = think(SUPPORT_REPLY, request, timeout_s=10)
    return hit | answer

deployment = deploy(triage, tools=[lookup], reasoners=[SUPPORT_REPLY])
result = deployment.dry_run("charged twice", reasoners={"support_reply": lambda value: {"reply": value["queue"]}})
print(result.value)
```

## Import Paths

Top-level exports cover `flow`, `think`, `cond`, `switch`, `each`,
`reschedule`, raw combinators, derived combinators, DAG classes, IR classes,
`validate`, `blocking`, and `explain`. Typed wrappers live in
`julep.typed`; typed adapters in `julep.flow_adapters`.

## Define-By-Construction Frontend

### `@flow`

Signature: `flow(fn: Callable[..., Any]) -> FlowDef`

Decorates a Python function into a define-time graph builder. The function must
have at least one parameter and must return a `Handle`. The body may call
registered `Tool` objects, registered `Pure` objects, `think(...)`, `cond(...)`,
`switch(...)`, `each(...)`, `reschedule(...)`, or another `@flow`.

Parameter: `fn` is executed once at definition time with `Handle` parameters.
Returns: `FlowDef`.

Raises: `DefineError` for no parameters, non-`Handle` return, unused parameters,
unregistered callables on handles, handle truthiness/equality misuse,
foreign-scope handle capture, reserved `__*__` step names, non-JSON or
secret-shaped captures, tuple-unpacking handle targets, unsaturated flow return,
or invalid sub-flow inlining. Example: `node = triage.to_ir()`.

### `FlowDef`

Constructor: `FlowDef(fn: Callable[..., Any]) -> None`

Usually produced by `@flow`. `FlowDef` implements `FlowLike[Any, Any]`.

Attributes: `fn: Callable[..., Any]`, `name: str`,
`param_names: list[str]`, and `graph: dag.Graph`.

Methods:

| Signature | Returns | Raises | Example |
|---|---|---|---|
| `__call__(*args: Any, **kwargs: Any) -> Handle | BoundFlow` | Inlines when called inside another `@flow` with a single handle; otherwise returns `BoundFlow`. | `TypeError` for unexpected/duplicate args; `DefineError` for invalid inline multi-param use. | `partial = enrich(config={"limit": 3})` |
| `to_ir() -> Node` | Compiled `Node`. | `DefineError` if more than one runtime parameter remains. | `flow_ir = normalize.to_ir()` |

### `BoundFlow`

Dataclass signature: `BoundFlow(flow: FlowDef, bound_args: dict[str, Any])`

Created by partial application of a `FlowDef`. Non-handle bound values must be
canonical JSON and must not look secret-shaped.

| API | Returns | Raises | Example |
|---|---|---|---|
| `BoundFlow.from_supplied(flow_def: FlowDef, supplied: dict[str, Any]) -> BoundFlow` | A partially applied flow. | `DefineError` for non-JSON or secret-shaped constants. | `BoundFlow.from_supplied(bounded, {"limit": 7})` |
| `remaining_param_names -> list[str]` | Unbound parameter names. | None. | `one_arg.remaining_param_names` |
| `to_ir() -> Node` | `std.pack` plus `compile_env(...)` wrapper. | `DefineError` unless exactly one runtime parameter remains. | `one_arg.to_ir()` |

### `Handle`

Constructor: `Handle(label: str, graph: Optional[dag.Graph], source: Optional[SourceSpan]) -> None`

Authoring-time value, not runtime data.

| API | Returns | Raises | Example |
|---|---|---|---|
| `Handle.synthetic(label: str) -> Handle` | Synthetic handle for tests/errors. | None. | `Handle.synthetic("source")` |
| `h1 | h2 -> Handle` | Appends `std.merge`. | `DefineError` outside `@flow` or for foreign-scope handles. | `payload = hit | answer` |
| `h["key"] -> Handle` | Appends `std.pluck` with `args={"key": key}`. | `DefineError` outside `@flow`. | `clusters = source["clusters"]` |
| `bool(h)` | Never returns. | `TypeError`; use `cond(...)`. | `cond(is_ready, h, then=a, orelse=b)` |
| `iter(h)` | Never returns. | `TypeError`; use `each(...)`. | `each(body, h)` |
| `h.foo` | Never returns. | `AttributeError`; use `h["foo"]`. | `h["foo"]` |
| `h == other`, `h != other` | Never returns. | `DefineError`; use `cond(...)`. | `cond(eq_pred, h, then=a, orelse=b)` |

### Step Options

Inside `@flow`, tool, pure, and reasoner step calls accept these reserved kwargs.
They become `Ann` fields and do not enter pure static args.

| Kwarg | Lowers to | Requirement checked by `validate` |
|---|---|---|
| `name: str` | Step output name override. | Must be a string and not match `__.*__`. |
| `retries` | `Ann(max_attempts=retries)` | Integer-like value `>= 1`. |
| `retry_interval_s` | `Ann(retry_interval_s=...)` | Finite number `>= 0`. |
| `backoff_rate` | `Ann(backoff_rate=...)` | Finite number `>= 1`. |
| `timeout_s` | `Ann(timeout_s=...)` | Serialized as `timeout`. |

```python
@flow
def with_options(ticket: str) -> dict[str, str]:
    hit = lookup(ticket, name="ticket_hit", retries=3, retry_interval_s=0.5, backoff_rate=2.0, timeout_s=10)
    return hit
```

### Frontend Control Helpers

| Signature | Meaning | Returns | Raises | Example |
|---|---|---|---|---|
| `think(reasoner_or_name: str | Reasoner, value: None = None, /, **kwargs: Any) -> Node` | Outside `@flow`, build `dsl.think(name, **kwargs)`. | `Node` | Errors from `dsl.think`/`Ann` validation later. | `think(SUPPORT_REPLY)` |
| `think(reasoner_or_name: str | Reasoner, value: Handle, /, **kwargs: Any) -> Handle` | Inside `@flow`, append a reasoner step. | `Handle` | `DefineError` for bad handle or escaped handle. | `answer = think(SUPPORT_REPLY, prompt)` |
| `cond(pred: str | Any, subject: Handle, *, then: FlowDef | BoundFlow, orelse: FlowDef | BoundFlow) -> Handle` | Binary branch on registered pure predicate. Arms receive the branch subject by name. | `Handle` | `DefineError` for unregistered predicate, non-flow arms, JSON captures in arms, or arm parameter mismatch. | `cond(is_found, hit, then=found, orelse=missing)` |
| `switch(selector: str | Any, subject: Handle, *, cases: dict[str, FlowDef | BoundFlow], default: FlowDef | BoundFlow | None = None) -> Handle` | Multiway branch on registered pure selector. | `Handle` | `DefineError` for empty cases, unregistered selector, non-flow arms, or arm parameter mismatch. | `switch(status, write, cases={"ok": ok}, default=fail)` |
| `each(body: FlowDef | BoundFlow | Node, items: Optional[Handle] = None, *, max_parallel: Optional[int] = None, reducer: str | Any | None = None) -> Node | Handle` | Inside `@flow`, dynamic fan-out over `items`; outside, dispatches to `dsl.each` only when `body` is a `Node`. | `Handle` or `Node` | `DefineError` for missing handle items inside `@flow`, invalid body, invalid captures, bad reducer; `ValueError` later for invalid low-level bounds. | `labels = each(label_one(ctx=ctx), clusters, max_parallel=2)` |
| `reschedule(state: Handle, *, after_s: Optional[int] = None, after: Optional[Node] = None, mark: Any = None) -> Handle` | Terminal owned-continuation primitive: optional mark tool, reserved `__sleep__`, then `std.continue_with`. | `Handle` | `DefineError` unless exactly one delay source is supplied; `after_s >= 1`; `after=delay(seconds=...)`; `mark` is a registered `Tool`. | `return reschedule(state, after_s=300, mark=mark_dirty)` |
| `apply_if_authoring(fn: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any` | Hook used by `Tool` and `Pure` calls. Returns `NotImplemented` outside authoring. | `Any` | `DefineError` when a handle escapes its flow or call shape is invalid. | `Tool.__call__` uses it. |

## Typed Authoring Surface

### `FlowLike[In, Out]`

Base class for objects that lower to `Node`.

| Signature | Meaning | Returns | Raises | Example |
|---|---|---|---|---|
| `to_ir(self) -> Node` | Lower to IR. | `Node` | `NotImplementedError` on the base class. | `node = flow_like.to_ir()` |
| `__rshift__(self, other: FlowLike[Out, Next]) -> Flow[In, Next]` | Typed sequential composition. | `Flow` | Whatever `to_ir()` raises. | `pipeline = fetch >> classify` |
| `as_sub(self, queue: Optional[str] = None) -> SplitCapability` | Mark a named flow/agent for split deployment. | `SplitCapability` | `ValueError` if there is no durable ref; call `.named(...)` first. | `cap = pipeline.named("svc.v1").as_sub(queue="svc")` |
| `named(self, ref: str) -> Flow[In, Out]` | Register durable ref. | `Flow` | `FlowRegistryError` on collision. | `named = pipeline.named("svc.v1")` |
| `renamed(self, ref: str) -> Flow[In, Out]` | Replace/reassert durable ref. | `Flow` | `FlowRegistryError` on namespace collision. | `next_v = changed.renamed("svc.v1")` |

### `Flow[In, Out]`

Constructor: `Flow(node: Node, name: Optional[str] = None) -> None`

| API | Type | Meaning |
|---|---|---|
| `to_ir(self) -> Node` | method | Return the wrapped node. |
| `name` | `Optional[str]` | Durable ref carried by `.named()` or `.renamed()`. |
| `local_name` | `str` | Debug-only deterministic `flow-<hash>` over normalized IR. |
| `__repr__(self) -> str` | method | `Flow(<op>#<id>)`. |

### Typed Helpers

| Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|
| `derive_local_name(node: Node) -> str` | `node`: IR node. | `flow-<8 hex>` debug name. | None expected for serializable `Node`. | `derive_local_name(node)` |
| `as_flow(x: FlowLike[In, Out]) -> Flow[In, Out]` | Lowerable typed value. | `Flow`. | Whatever `x.to_ir()` raises. | `as_flow(tool_obj)` |
| `as_flow(x: Node) -> Flow[Any, Any]` | Raw IR node. | `Flow`. | None. | `as_flow(call("lookup"))` |
| `seq(*flows: FlowLike[Any, Any]) -> Flow[Any, Any]` | One or more flows; overloaded through arity 8 for precise types. | Typed sequential `Flow`. | `ValueError` if empty. | `seq(fetch, classify)` |
| `par(branches: Sequence[FlowLike[In, Any]], *, join: str | Pure | None = None) -> Flow[In, Any]` | Concurrent branches; optional pure reducer. | `Flow[In, Any]`. | Whatever branch lowering raises. | `par([a, b], join="join")` |
| `alt(pred: str | Pure, if_true: FlowLike[In, Out], if_false: FlowLike[In, Out]) -> Flow[In, Out]` | Registered predicate and same-typed arms. | `Flow`. | Whatever arm lowering raises. | `alt(is_found, found, missing)` |
| `each(body: FlowLike[In, Out], *, max_parallel: Optional[int] = None) -> Flow[Sequence[In], list[Out]]` | Body flow. | List-producing `Flow`. | `ValueError` from low-level `dsl.each` if bound invalid. | `each(label_one, max_parallel=4)` |
| `each(body: FlowLike[In, Out], *, max_parallel: Optional[int] = None, reducer: str | Pure) -> Flow[Sequence[In], Any]` | Body plus reducer pure. | Reduced `Flow`. | `ValueError` from low-level `dsl.each` if bound invalid. | `each(label_one, reducer="count_items")` |

### `SplitCapability`

Dataclass signature: `SplitCapability(ref: str, target: FlowLike[Any, Any], queue: Optional[str] = None)`

Used by split deployment plumbing. `ref` is the durable flow ref, `target` is
the lowerable flow/agent, and `queue` is an optional execution queue hint.

## Typed Adapters and Registry

| Signature | Meaning | Returns | Raises | Example |
|---|---|---|---|---|
| `as_type(t: type[T]) -> Flow[Any, T]` | Authoring-only cast. Lowers to `dsl.ident()`; no runtime validation. | `Flow[Any, T]` | None. | `typed = as_type(dict)` |
| `expect(f: Flow[In, Any], t: type[T]) -> Flow[In, T]` | Retype `f` output by composing with `as_type(t)`. | `Flow[In, T]` | Whatever `f.to_ir()` raises. | `typed = expect(agent_flow, dict)` |
| `any_edges(f: Flow[Any, Any]) -> list[AnyEdge]` | Structural report of `Any` boundaries for `app`, `eval_plan`, and `think`. | `list[AnyEdge]` | Whatever `f.to_ir()` raises. | `any_edges(as_flow(think("r")))` |

Dataclass: `AnyEdge(node_id: str, op: str, reason: str)`.

Registry APIs:

| Signature | Meaning | Returns | Raises | Example |
|---|---|---|---|---|
| `FlowRegistry(reasoner_registry: Registry = DEFAULT_REGISTRY) -> None` | Isolated durable flow registry. | `FlowRegistry` | None. | `registry = FlowRegistry()` |
| `FlowRegistry.register_flow(ref: str, flow_or_node: Node | _Lowerable, *, replace: bool = False) -> FlowSpec` | Register a ref. Idempotent for structurally equal IR. | `FlowSpec` | `FlowRegistryError` on different-flow collision or reasoner/tool-name collision. | `registry.register_flow("svc.v1", node)` |
| `FlowRegistry.get_flow(ref: str) -> FlowSpec` | Resolve ref. | `FlowSpec` | `FlowRegistryError` if unknown. | `registry.get_flow("svc.v1")` |
| `FlowRegistry.has_flow(ref: str) -> bool` | Check local registry. | `bool` | None. | `registry.has_flow("svc.v1")` |
| `register_flow(ref: str, flow_or_node: Node | _Lowerable, *, replace: bool = False) -> FlowSpec` | Register in default registry. | `FlowSpec` | `FlowRegistryError`. | `register_flow("svc.v1", node)` |
| `get_flow(ref: str) -> FlowSpec` | Resolve from default registry. | `FlowSpec` | `FlowRegistryError`. | `get_flow("svc.v1")` |

Dataclass: `FlowSpec(ref: str, node: Node)`.

## Raw Combinator Kernel

Every function here returns `Node` except `native`, `mcp`, source-capture
helpers, and `Contract` constructors.

### Source Capture

| Signature | Meaning | Returns | Raises | Example |
|---|---|---|---|---|
| `set_source_capture(enabled: bool) -> None` | Enable/disable best-effort `SourceSpan` capture for raw DSL constructors. | `None` | None. | `set_source_capture(True)` |
| `source_capture_enabled() -> bool` | Current raw DSL capture flag. | `bool` | None. | `source_capture_enabled()` |

Environment knob: `COMPOSABLE_AGENTS_SOURCE_CAPTURE=1` enables raw DSL source
capture at import time. Source spans are metadata and are not serialized into
`Node.to_json()`.

### Leaves

| Signature | Parameters | Returns | Raises | Example |
|---|---|---|---|---|
| `native(name: str) -> NativeTool` | Native tool name. | `NativeTool`. | None. | `native("lookup")` |
| `mcp(server: str, tool: str) -> McpTool` | MCP server and tool names. | `McpTool`. | None. | `mcp("github", "search")` |
| `call(ref_or_name: str | ToolRef, *, ctx: CtxArg = None, ann: Optional[Ann] = None) -> Node` | Bare string is native; `ctx` is `ContextPolicy`/`ContextScope`; `ann` carries policy. | `Node(op=Op.PRIM)`. | `TypeError` if `ref_or_name` is not a string, `NativeTool`, or `McpTool`. | `call(mcp("srv", "tool"), ctx=ContextScope.LOCAL)` |
| `think(reasoner: str, *, ctx: CtxArg = None, ann: Optional[Ann] = None) -> Node` | Named reasoner. | `Node(op=Op.PRIM)`. | None. | `think("support_reply", ann=Ann(timeout_s=10))` |
| `reasoner_from_ctx(path: str, *, ctx: CtxArg = None) -> Node` | Dotctx-backed think leaf; defaults to local context when omitted. | `Node`. | None. | `reasoner_from_ctx("agent.ctx")` |
| `ident() -> Node` | Identity leaf. | `Node(op=Op.IDENT)`. | None. | `ident()` |
| `arr(pure_name: str, args: Optional[dict[str, Any]] = None) -> Node` | Registered pure name plus optional static args. | `Node(op=Op.ARR)`. | None at construction; validation checks pure registration and args. | `arr("std.pluck", {"key": "id"})` |
| `sub(ref: str, contract: Optional[SubContract] = None, *, summary_policy: Optional[SummaryPolicy] = None) -> Node` | Opaque child workflow ref. | `Node(op=Op.PRIM)`. | None. | `sub("child.v1", Contract.feedback())` |

### Structural Combinators

| Signature | Shape | Returns | Raises | Example |
|---|---|---|---|---|
| `seq(*flows: Node | Sequence[Node]) -> Node` | Pipeline | Left-folded `Op.SEQ`, or the single node unchanged. | `ValueError` if empty. | `seq(call("a"), call("b"))` |
| `par(*flows: Node | Sequence[Node]) -> Node` | Dataflow | Left-folded `Op.PAR`, or the single node unchanged. | `ValueError` if empty. | `par(think("a"), think("b"))` |
| `fanout(*flows: Node | Sequence[Node]) -> Node` | Dataflow | Same IR as `par`. | `ValueError` if empty. | `fanout(call("a"), call("b"))` |
| `alt(pred: Optional[str] = None, if_true: Optional[Node] = None, if_false: Optional[Node] = None, *, select: Optional[str] = None, cases: Optional[dict[str, Node]] = None, default: Optional[Node] = None) -> Node` | Branching | Binary predicate branch or selector/cases branch. | `ValueError` for mixed modes, missing selector/predicate, no cases, or missing binary arms. | `alt("is_found", call("yes"), call("no"))` |
| `each(body: Node, *, max_parallel: Optional[int] = None, reducer: Optional[str] = None) -> Node` | Dataflow | `Op.EACH` over runtime list input. | `ValueError` if `max_parallel < 1`. | `each(call("label"), max_parallel=4)` |
| `iter_up_to(max: int, body: Node, *, until: Optional[str] = None) -> Node` | Feedback | Bounded loop. | No constructor guard for `max`; validation/runtime own malformed values. | `iter_up_to(3, call("step"), until="done")` |
| `stage(planner: str) -> Node` | Staged | Model-generated plan leaf. | None. | `stage("planner")` |
| `app(controller: str, *, tools: Optional[Any] = None, subflows: Optional[Any] = None, budget: Optional[Any] = None, max_rounds: Optional[int] = None, ctx: CtxArg = None, summarizer: Optional[str] = None) -> Node` | Agent | Open-ended controller loop. | None at construction; validation/capabilities enforce legality. | `app("agent", tools=["lookup"], max_rounds=5)` |

### `Contract`

Static constructors for `SubContract`.

| Signature | Returns | Example |
|---|---|---|
| `Contract.of(shape: Shape, summary_policy: Optional[SummaryPolicy] = None) -> SubContract` | Contract for explicit shape. | `Contract.of(Shape.DATAFLOW)` |
| `Contract.pipeline(summary_policy: Optional[SummaryPolicy] = None) -> SubContract` | `Shape.PIPELINE`. | `Contract.pipeline()` |
| `Contract.dataflow(summary_policy: Optional[SummaryPolicy] = None) -> SubContract` | `Shape.DATAFLOW`. | `Contract.dataflow()` |
| `Contract.feedback(summary_policy: Optional[SummaryPolicy] = None) -> SubContract` | `Shape.FEEDBACK`. | `Contract.feedback()` |
| `Contract.staged(summary_policy: Optional[SummaryPolicy] = None) -> SubContract` | `Shape.STAGED`. | `Contract.staged()` |
| `Contract.agent(summary_policy: Optional[SummaryPolicy] = SummaryPolicy.RESULT_ONLY) -> SubContract` | `Shape.AGENT`. | `Contract.agent()` |

## Derived Combinators

| Signature | Meaning | Returns | Raises | Example |
|---|---|---|---|---|
| `race(*flows: Node | Sequence[Node], reduce: Optional[str] = None) -> Node` | First successful branch wins; losers cancelled. | Race-marked `par` chain. | `ValueError` if no branches. | `race(call("a"), call("b"))` |
| `hedge(*flows: Node | Sequence[Node], hedge_ms: int, reduce: Optional[str] = None) -> Node` | Start first branch, reveal others after delay. | Hedge-marked `par` chain. | `ValueError` if no branches or `hedge_ms < 0`. | `hedge(call("fast"), call("slow"), hedge_ms=100)` |
| `quorum(*flows: Node | Sequence[Node], k: int, reduce: Optional[str] = None) -> Node` | Settle after `k` successes. | Quorum-marked `par` chain. | `ValueError` if `k` outside `1..len(branches)` or no branches. | `quorum(call("a"), call("b"), k=1)` |
| `map_n(*flows: Node, reducer: Optional[str] = None) -> Node` | Wait for all branches; optional reducer. | `par` chain with `Merge(kind="all")`. | `ValueError` if no branches. | `map_n(call("a"), call("b"), reducer="join")` |
| `map_reduce(mappers: Sequence[Node], reduce: str) -> Node` | Fan out then reduce. | `Node`. | `ValueError` if no mappers. | `map_reduce([call("a")], "join")` |
| `vote(reasoners: Sequence[str], agg: str) -> Node` | Parallel reasoner votes, aggregate with pure. | `Node`. | `ValueError` if no reasoners. | `vote(["r1", "r2"], "majority")` |
| `review(main: Node, reviewer: str, k: int, *, agg: Optional[str] = None) -> Node` | Run `main`, then `k` reviewer reasoner passes. | `Node`. | `ValueError` if `k < 1`. | `review(call("draft"), "reviewer", 2)` |
| `recv(channel: str, *, timeout_s: Optional[int] = None) -> Node` | Reserved `__recv__` channel receive. | `Node`. | None. | `recv("inbox", timeout_s=60)` |
| `emit(channel: str, value: Optional[str] = None) -> Node` | Reserved `__emit__` channel append; `value` or input is emitted. | `Node`. | None. | `emit("outbox")` |
| `human_gate(*, prompt: Optional[str] = None, timeout_s: Optional[int] = None) -> Node` | Reserved `__human_gate__` signal wait. | `Node`. | None. | `human_gate(prompt="approve?", timeout_s=300)` |
| `delay(*, seconds: int) -> Node` | Reserved `__sleep__` durable timer. | `Node`. | `ValueError` if `seconds < 1`. | `delay(seconds=30)` |
| `flatten_race_group(root: Node) -> list[Node]` | Recover flat branch list from same-kind race-family `par` chain. | `list[Node]`. | None. | `flatten_race_group(race(a, b))` |
| `check_race_admission(flow: Node, manifest: ToolManifest) -> list[Diagnostic]` | Validate race-family branches against frozen manifest. | Diagnostics. | None. | `check_race_admission(flow, manifest)` |

Constants: `HUMAN_GATE_TOOL = "__human_gate__"`, `SLEEP_TOOL = "__sleep__"`,
`RECV_TOOL = "__recv__"`, `EMIT_TOOL = "__emit__"`, and
`HUMAN_CHANNEL = "human"`.

## DAG Compiler

The `@flow` frontend builds this model; other frontends may build it directly.
It compiles to raw `Node` IR and preserves effect fences: write, external, and
dangerous tool steps are barriers, while pure/read/think steps can layer into
parallel env projections when dependencies allow.

### Data Types

| API | Signature | Meaning |
|---|---|---|
| `GraphDefinitionError` | `class GraphDefinitionError(ValueError)` | Define/compile-time graph error. |
| `StepKind` | `TOOL`, `THINK`, `PURE`, `PASSTHROUGH`, `COND`, `SWITCH`, `EACH` | DAG step classes. |
| `InputEdge` | `InputEdge(name: str, source: str)` | Declared data edge. User input renaming is rejected. |
| `StepNode` | `StepNode(kind: StepKind, ref: str, inputs: tuple[InputEdge, ...], output: str, contract: Optional[ToolContract] = None, ann: Optional[Ann] = None, source: Optional[SourceSpan] = None, args: Optional[dict[str, Any]] = None, order: int = 0, if_true: Optional[Graph] = None, if_false: Optional[Graph] = None, cases: Optional[dict[str, Graph]] = None, default: Optional[Graph] = None, body: Optional[Graph] = None, max_parallel: Optional[int] = None, reducer: Optional[str] = None, const_captures: Optional[dict[str, Any]] = None, branch_subject: Optional[str] = None)` | One single-assignment step. |
| `Graph` | `Graph(input_name: str = "__input__", output_name: Optional[str] = None, source: Optional[SourceSpan] = None)` | Authored DAG with unique outputs. |

Constants: `CAPTURE_SIZE_WARNING_BYTES = 4096`, `BRANCH_VALUE_KEY = "__branch__"`,
`RESERVED_ENV_NAME_RE = re.compile(r"__.*__")`.

### Graph Methods

| Signature | Returns | Raises | Example |
|---|---|---|---|
| `Graph.add_step(kind: StepKind | str, ref: str, *, inputs: Sequence[InputSpec] = (), output: str, contract: Optional[ToolContract] = None, ann: Optional[Ann] = None, source: Optional[SourceSpan] = None, args: Optional[dict[str, Any]] = None, tool: Any = None) -> StepNode` | Added step. | `GraphDefinitionError` on output collision/reserved output; `ValueError` if `kind` is invalid. | `g.add_step(StepKind.PURE, "std.pluck", output="id", args={"key": "id"})` |
| `Graph.add_cond(pred: str, *, inputs: Sequence[InputSpec] = (), output: str, if_true: Graph, if_false: Graph, source: Optional[SourceSpan] = None, branch_subject: Optional[InputSpec] = None) -> StepNode` | Branch step. | `GraphDefinitionError` on output issues/input renaming. | `g.add_cond("is_found", output="r", if_true=a, if_false=b)` |
| `Graph.add_switch(select: str, *, inputs: Sequence[InputSpec] = (), output: str, cases: dict[str, Graph], default: Optional[Graph] = None, source: Optional[SourceSpan] = None, branch_subject: Optional[InputSpec] = None) -> StepNode` | Selector branch step. | `GraphDefinitionError` if `cases` empty or output/input invalid. | `g.add_switch("status", output="r", cases={"ok": ok})` |
| `Graph.add_each(body: Graph, *, items: InputSpec, output: str, max_parallel: Optional[int] = None, reducer: Optional[str] = None, const_captures: Optional[dict[str, Any]] = None, source: Optional[SourceSpan] = None) -> StepNode` | Dynamic fan-out step. | `GraphDefinitionError` on output collision, `max_parallel < 1`, foreign handle capture, non-JSON capture; emits `UserWarning` for oversized captures. | `g.add_each(body, items="items", output="labels")` |

### Compile Functions

| Signature | Meaning | Returns | Raises | Example |
|---|---|---|---|---|
| `compile(graph: Graph) -> Node` | Compile public-input graph to `Node`. | `Node`. | `GraphDefinitionError` for cycles, unknown outputs, forward edges, malformed branches/each, reserved output names. | `node = compile(graph)` |
| `compile_env(graph: Graph, initial_fields: Sequence[str]) -> Node` | Compile from an existing env record; used for bound flows and branch/each arms. | `Node`. | `GraphDefinitionError` for malformed graph. | `node = compile_env(graph, ["item", "ctx"])` |

## Frozen IR

`Node.to_json()` is the wire format. It uses camelCase keys where needed
(`summaryPolicy`, `inputSchema`, `maxRounds`, `retryIntervalS`) and omits
metadata such as `SourceSpan`. `canonical_json(value)` is compact, sorted JSON
used for hashing.

### Enums

| Enum | Values |
|---|---|
| `Op` | `PRIM`, `IDENT`, `ARR`, `SEQ`, `PAR`, `EACH`, `ALT`, `ITER_UP_TO`, `EVAL_PLAN`, `APP`, `LOOP` |
| `Shape` | `PIPELINE`, `DATAFLOW`, `BRANCHING`, `FEEDBACK`, `STAGED`, `AGENT` |
| `EnforcementMode` | `STRICT`, `DEV`; `EnforcementMode.coerce("prod") == STRICT` |
| `Effect` | `READ`, `WRITE`, `EXTERNAL`, `DANGEROUS` |
| `Idempotency` | `REQUIRED`, `NATIVE`, `BEST_EFFORT`, `NONE` |
| `ContextScope` | `NONE`, `LOCAL`, `SUMMARY`, `WHOLE_SESSION` |
| `SummaryPolicy` | `RESULT_ONLY`, `COMPRESSED_TRACE`, `FULL_CHILD_REF` |

Shape helpers:

| Signature | Returns | Example |
|---|---|---|
| `shape_rank(s: Shape) -> int` | Rank in the shape lattice. | `shape_rank(Shape.DATAFLOW)` |
| `shape_leq(a: Shape, b: Shape) -> bool` | Whether `a <= b`. | `shape_leq(Shape.PIPELINE, Shape.AGENT)` |
| `shape_join(*shapes: Shape) -> Shape` | Least upper bound; empty join is `Shape.PIPELINE`. | `shape_join(Shape.PIPELINE, Shape.DATAFLOW)` |
| `surface_shape(n: Node) -> Shape` | Shape as parent scheduler sees it; `Sub` is opaque. | `surface_shape(node)` |
| `closed_shape(n: Node) -> Shape` | Shape for budgeting/admission; `Sub` reveals contract shape. | `closed_shape(node)` |

### Tool and Channel Refs

| API | Signature | JSON | Raises | Example |
|---|---|---|---|---|
| `NativeTool` | `NativeTool(name: str, kind: str = "native")` | `{"kind":"native","name":...}` | None. | `NativeTool("lookup").to_json()` |
| `McpTool` | `McpTool(server: str, tool: str, kind: str = "mcp")` | `{"kind":"mcp","server":...,"tool":...}` | None. | `McpTool("srv", "search").to_json()` |
| `toolref_from_json(d: dict[str, Any]) -> ToolRef` | Rebuild tool ref. | Input dict. | `ValueError` for unknown `kind`; `KeyError` for missing keys. | `toolref_from_json({"kind": "native", "name": "x"})` |
| `toolref_key(ref: ToolRef) -> str` | Manifest/capability key. | Native name or `server/tool`. | None. | `toolref_key(McpTool("srv", "search"))` |
| `ChannelRef` | `ChannelRef(name: str, payload: Optional[JSONSchema] = None)` | `{"name":...,"payload":...}` when payload exists. | `KeyError` in `from_json` if missing `name`. | `ChannelRef("inbox").to_json()` |
| `ChannelRef.from_json(d: dict[str, Any]) -> ChannelRef` | Rebuild channel ref. | Input dict. | `KeyError` for missing `name`. | `ChannelRef.from_json({"name": "inbox"})` |
| `channelref_key(ref: ChannelRef) -> str` | Channel manifest key. | Name. | None. | `channelref_key(ChannelRef("inbox"))` |

### Context, Cache, Annotation

| API | Signature | Parameters | Returns/Raises | Example |
|---|---|---|---|---|
| `ContextPolicy` | `ContextPolicy(scope: ContextScope = ContextScope.LOCAL, redact_pii: bool = False, max_tokens: Optional[int] = None)` | Explicit context scope, PII redaction flag, max tokens. | `.to_json()` / `.from_json(...)`; enum conversion can raise `ValueError`. | `ContextPolicy(ContextScope.SUMMARY, max_tokens=800)` |
| `CacheHint` | `CacheHint(key: Optional[str] = None, ttl_s: Optional[int] = None)` | Cache key and TTL seconds. | `.to_json()` / `.from_json(...)`. | `CacheHint(key="ticket", ttl_s=60)` |
| `Ann` | `Ann(*, cost: Optional[float] = None, risk: Optional[str] = None, cache: Optional[CacheHint] = None, effect: Optional[Effect] = None, timeout_s: Optional[int] = None, max_attempts: Optional[int] = None, retry_interval_s: Optional[float] = None, backoff_rate: Optional[float] = None, batchable: bool = False)` | Per-node cost/risk/cache/effect/timeout/retry/batch hints. | `.to_json()` emits non-empty fields; `.from_json(...)` can raise enum `ValueError`. | `Ann(timeout_s=10, max_attempts=3, batchable=True)` |

### Steps

| API | Signature | Meaning | Raises | Example |
|---|---|---|---|---|
| `CallStep` | `CallStep(tool: ToolRef, ctx: Optional[ContextPolicy] = None, frozen_hash: Optional[str] = None, kind: str = "call")` | Tool invocation; `frozen_hash` is bound by freeze. | None. | `CallStep(NativeTool("lookup")).to_json()` |
| `ThinkStep` | `ThinkStep(reasoner: str, ctx: Optional[ContextPolicy] = None, kind: str = "think")` | Reasoner invocation. | None. | `ThinkStep("support_reply").to_json()` |
| `SubContract` | `SubContract(shape: Shape, summary_policy: Optional[SummaryPolicy] = None)` | Contract crossing the sub-flow firewall. | `.from_json` can raise enum `ValueError`/`KeyError`. | `SubContract(Shape.AGENT, SummaryPolicy.RESULT_ONLY)` |
| `SubStep` | `SubStep(ref: str, contract: SubContract, kind: str = "sub")` | Opaque child workflow. | None. | `SubStep("child.v1", SubContract(Shape.PIPELINE))` |
| `step_from_json(d: dict[str, Any]) -> Step` | Rebuild `CallStep`, `ThinkStep`, or `SubStep`. | `ValueError` for unknown `kind`; `KeyError` for missing fields. | `step_from_json({"kind": "think", "reasoner": "r"})` |

### Merge and Node

`Merge(kind: str = "all", hedge_ms: Optional[int] = None, quorum_m: Optional[int] = None, reducer: Optional[str] = None)`

`kind` is `"all"`, `"race"`, `"hedge"`, or `"quorum"` by convention. The
constructor does not validate that set; race admission keys off
`RACE_LIKE_MERGES = frozenset({"race", "hedge", "quorum"})`.

`Node` constructor: `Node(op: Op, id: str, ann: Optional[Ann] = None, step:
Optional[Step] = None, left: Optional[Node] = None, right: Optional[Node] = None,
select: Optional[str] = None, cases: Optional[dict[str, Node]] = None, default:
Optional[Node] = None, bound: Optional[int] = None, body: Optional[Node] = None,
plan: Optional[Node] = None, state_schema: Optional[JSONSchema] = None,
channels: Optional[list[ChannelRef]] = None, controller: Optional[str] = None,
pure: Optional[str] = None, args: Optional[dict[str, Any]] = None, merge:
Optional[Merge] = None, prompt: Optional[str] = None, tools: Optional[Any] =
None, subflows: Optional[Any] = None, budget: Optional[Any] = None, max_rounds:
Optional[int] = None, ctx: Optional[ContextPolicy] = None, summarizer:
Optional[str] = None, source: Optional[SourceSpan] = None)`.

Methods:

| Signature | Returns | Raises | Example |
|---|---|---|---|
| `children(self) -> list[Node]` | Direct children, sorted by case key. | None. | `node.children()` |
| `walk(self) -> Iterator[Node]` | Pre-order traversal. | None. | `[n.id for n in node.walk()]` |
| `tool_refs(self) -> list[ToolRef]` | Tool refs from `CallStep` leaves. | None. | `node.tool_refs()` |
| `to_json(self) -> dict[str, Any]` | Wire-format dict. | May propagate child serialization errors. | `node.to_json()` |
| `Node.from_json(d: dict[str, Any]) -> Node` | Rebuilt tree. | `ValueError`/`KeyError` for bad enum/kind/missing fields. | `Node.from_json(node.to_json())` |

Other IR helpers:

| Signature | Meaning | Example |
|---|---|---|
| `SourceSpan(file: str, line: int, function: Optional[str] = None, text: Optional[str] = None)` | Source metadata used for diagnostics; omitted from JSON. | `SourceSpan("flow.py", 10, "build")` |
| `canonical_json(value: Any) -> str` | Sorted compact JSON. | `canonical_json({"b": 2, "a": 1})` |
| `pure_display(name: str, args: Any = None) -> str` | Human label for pure plus args. | `pure_display("std.pluck", {"key": "id"})` |

## Contracts and Pures

### Tool Contracts

| Signature | Meaning | Returns/Raises | Example |
|---|---|---|---|
| `ToolContract(effect: Effect, idempotency: Idempotency)` | Asserted or defaulted behavior. | `.to_json()` / `.from_json(...)`; enum conversion can raise. | `ToolContract(Effect.READ, Idempotency.NATIVE)` |
| `contract_allows_retry(contract: ToolContract) -> bool` | Retry is safe for read or native/required idempotent tools. | `bool`. | `contract_allows_retry(contract)` |
| `McpAnnotations(read_only_hint: Optional[bool] = None, destructive_hint: Optional[bool] = None, open_world_hint: Optional[bool] = None, idempotent_hint: Optional[bool] = None)` | MCP hints snapshot. | `.to_json()`. | `McpAnnotations(read_only_hint=True)` |
| `McpAnnotations.from_mcp(d: dict[str, Any]) -> McpAnnotations` | Reads `tool.annotations` or a flat dict. | `McpAnnotations`. | `McpAnnotations.from_mcp({"annotations": {"readOnlyHint": True}})` |
| `contract_from_annotations(ann: McpAnnotations) -> ToolContract` | Conservative mapping; destructive > external > read-only > default. | `ToolContract`. | `contract_from_annotations(McpAnnotations(read_only_hint=True))` |
| `definition_hash(ref: ToolRef, input_schema: JSONSchema, output_schema: Optional[JSONSchema] = None, server_version: Optional[str] = None, annotations: Optional[McpAnnotations | dict[str, Any]] = None) -> str` | Provider definition identity. | `sha256:<hex>`. | `definition_hash(NativeTool("x"), {})` |
| `execution_hash(tool_definition_hash: str, contract: ToolContract, asserted: bool) -> str` | Exact execution identity. | `sha256:<hex>`. | `execution_hash(def_hash, contract, True)` |

`CONSERVATIVE_DEFAULT = ToolContract(effect=Effect.WRITE, idempotency=Idempotency.NONE)`.

`FrozenTool` signature: `FrozenTool(definition_hash: str, execution_hash: str,
ref: ToolRef, input_schema: JSONSchema, contract: ToolContract,
output_schema: Optional[JSONSchema] = None, server_version: Optional[str] =
None, asserted: bool = False)`.

| API | Returns | Raises | Example |
|---|---|---|---|
| `FrozenTool.hash -> str` | Alias for `execution_hash`. | None. | `frozen.hash` |
| `FrozenTool.create(ref: ToolRef, input_schema: JSONSchema, contract: ToolContract, output_schema: Optional[JSONSchema] = None, server_version: Optional[str] = None, asserted: bool = False, annotations: Optional[McpAnnotations | dict[str, Any]] = None) -> FrozenTool` | Frozen tool with computed hashes. | JSON serialization errors for non-canonical inputs. | `FrozenTool.create(NativeTool("x"), {}, contract, asserted=True)` |
| `FrozenTool.to_json() -> dict[str, Any]` | Manifest entry. | None expected for serializable fields. | `frozen.to_json()` |
| `manifest_to_json(m: ToolManifest) -> dict[str, Any]` | Manifest JSON. | None expected. | `manifest_to_json(manifest)` |
| `frozentool_from_json(d: dict[str, Any]) -> FrozenTool` | Rebuild one entry, preserving hash. | `KeyError` for missing `executionHash`/fields; enum errors for invalid contract. | `frozentool_from_json(payload)` |
| `manifest_from_json(d: dict[str, Any]) -> ToolManifest` | Inverse of `manifest_to_json`. | Same as `frozentool_from_json`. | `manifest_from_json(payload)` |

### Pures

`Pure(name: str, fn: PureFn)` is a first-class registered pure. Calling it as
`Pure.__call__(value: Any, **kwargs: Any) -> Any` appends a pure step during
`@flow` authoring and otherwise runs `fn`; invalid authoring raises
`DefineError`. `Pure.to_ir() -> Node` lowers to `dsl.arr(self.name)`.

Registration APIs: `pure(fn: PureFn, /) -> Pure`, `pure(name: str, /) ->
Callable[[PureFn], Pure]`, `register_pure(name: str, fn: PureFn) -> PureEntry`,
`register_pure_with_source(name: str, fn: PureFn, source: str) -> PureEntry`,
and `register_pure_from_source(name: str, source: str, *, tier: str = "wasm") ->
PureEntry`. Registry/source errors surface from duplicate or invalid entries.
Lookup APIs: `is_registered(name: str) -> bool`, `get_pure(name: str) -> PureFn`,
`executor_of(name: str) -> str`, `source_hash_of(name: str) -> str`,
`diff_pure_hashes(pinned: dict[str, str], registered: dict[str, str]) ->
list[dict[str, str | None]]`, and `registered_names() -> list[str]`. Examples:
`@pure("normalize")`, `get_pure("normalize")`, `registered_names()`.

## Validation and Diagnostics

Dataclass: `Diagnostic(code: str, node_id: str, message: str, severity: str = "error", hint: Optional[str] = None, help_url: Optional[str] = None, source: Optional[SourceSpan] = None)`

| Signature | Meaning | Returns | Raises | Example |
|---|---|---|---|---|
| `blocking(diags: list[Diagnostic]) -> list[Diagnostic]` | Keep `severity == "error"`. | Diagnostics. | None. | `blocking(validate(node))` |
| `schema_incompatibility(out: Optional[JSONSchema], inp: Optional[JSONSchema]) -> Optional[str]` | Conservative JSON-Schema edge check. | Reason string or `None`. | None. | `schema_incompatibility({"type": "string"}, {"type": "object"})` |
| `validate(flow: Node, manifest: Optional[ToolManifest] = None, *, target: Optional[str] = None) -> list[Diagnostic]` | Structural validation; with manifest, schema and frozen-call checks. `target` is `None`, `"flow"`, or `"session"`. | Diagnostics. | `ValueError` for invalid `target`. | `validate(node, manifest, target="flow")` |
| `hint_for(code: str) -> Optional[str]` | User-facing fix hint for known diagnostic code. | Hint or `None`. | None. | `hint_for("UNKNOWN_PURE")` |
| `explain(diagnostics: Iterable[Diagnostic]) -> str` | CLI/library text rendering. | String. | None. | `print(explain(validate(node)))` |

Validation checks include finite trees, duplicate ids, per-op structure,
registered pure names, canonical JSON static args, retry-field bounds,
`seq` schema incompatibility, manifest resolution after freeze, session-loop
placement/productivity, and `WHOLE_SESSION` context under `par` as a warning.

## Errors and Exceptions

`DefineError(GraphDefinitionError)` covers invalid `@flow` authoring. `GraphDefinitionError(ValueError)` covers DAG construction/compile failures. `FlowRegistryError(ValueError)` covers named-flow lookup/collision failures. Raw DSL helpers also raise `ValueError` for empty groups or invalid bounds, `dsl.call` raises `TypeError` for bad refs, `Handle.__getattr__` raises `AttributeError`, oversized captures emit `UserWarning`, and strict `deploy(...)` raises `ValidationError` for blocking diagnostics.

## Configuration Knobs

`COMPOSABLE_AGENTS_SOURCE_CAPTURE=1` and `set_source_capture(True | False)`
toggle raw DSL source capture. `CAPTURE_SIZE_WARNING_BYTES = 4096` controls
oversized closure-capture warnings. `Ann(batchable=True)` serializes
`"batchable": true`. Deploy accepts `mode="strict" | "prod" | "dev"` and
`freeze_timing="deploy_time" | "per_run"`. There is no `@flow` decorator
argument surface and no flow-frontend-specific CLI flag in the source; see
[CLI docs](/docs/guides/using-the-cli) for `julep`.
<!-- generated by ca-docs-matrix: flow-frontend/reference -->

<!-- ported-by ca-docs-site: reference/flow-api -->
