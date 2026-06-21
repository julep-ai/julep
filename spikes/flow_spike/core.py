from __future__ import annotations

import ast
import inspect
import json
import linecache
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Sequence

from composable_agents import dsl
from composable_agents.agent import Tool
from composable_agents.flow import FlowLike
from composable_agents.ir import Node
from composable_agents.purity import Pure, is_registered, pure


def _split_pair(value: Any) -> tuple[dict[str, Any], Any]:
    env, item = value
    return dict(env), item


def _assign(value: Any, key: str) -> dict[str, Any]:
    if isinstance(value, list) and len(value) == 2 and isinstance(value[0], dict):
        env, item = _split_pair(value)
        env[key] = item
        return env
    return {key: value}


@pure("spike.assign_episode_id")
def spike_assign_episode_id(value: Any) -> dict[str, Any]:
    return _assign(value, "episode_id")


@pure("spike.assign_source")
def spike_assign_source(value: Any) -> dict[str, Any]:
    return _assign(value, "source")


@pure("spike.assign_summary")
def spike_assign_summary(value: Any) -> dict[str, Any]:
    return _assign(value, "summary")


@pure("spike.assign_merged")
def spike_assign_merged(value: Any) -> dict[str, Any]:
    return _assign(value, "merged")


@pure("spike.assign_liner")
def spike_assign_liner(value: Any) -> dict[str, Any]:
    return _assign(value, "liner")


@pure("spike.assign_return_arg")
def spike_assign_return_arg(value: Any) -> dict[str, Any]:
    return _assign(value, "return_arg")


@pure("spike.assign_return_value")
def spike_assign_return_value(value: Any) -> dict[str, Any]:
    return _assign(value, "return_value")


@pure("spike.pluck_episode_id")
def spike_pluck_episode_id(env: dict[str, Any]) -> Any:
    return env["episode_id"]


@pure("spike.pluck_source")
def spike_pluck_source(env: dict[str, Any]) -> Any:
    return env["source"]


@pure("spike.pluck_summary")
def spike_pluck_summary(env: dict[str, Any]) -> Any:
    return env["summary"]


@pure("spike.pluck_merged")
def spike_pluck_merged(env: dict[str, Any]) -> Any:
    return env["merged"]


@pure("spike.pluck_liner")
def spike_pluck_liner(env: dict[str, Any]) -> Any:
    return env["liner"]


@pure("spike.pluck_return_arg")
def spike_pluck_return_arg(env: dict[str, Any]) -> Any:
    return env["return_arg"]


@pure("spike.pluck_return_value")
def spike_pluck_return_value(env: dict[str, Any]) -> Any:
    return env["return_value"]


@pure("spike.merge")
def spike_merge(parts: list[dict[str, Any]]) -> dict[str, Any]:
    left, right = parts
    return {**left, **right}


@pure("spike.merge_source_summary")
def spike_merge_source_summary(env: dict[str, Any]) -> dict[str, Any]:
    return {**env["source"], **env["summary"]}


@pure("spike.merge_merged_liner")
def spike_merge_merged_liner(env: dict[str, Any]) -> dict[str, Any]:
    return {**env["merged"], **env["liner"]}


def _pure_name(value: str | Pure) -> str:
    if isinstance(value, str):
        return value
    return value.name


def _assign_name(label: str) -> str:
    return f"spike.assign_{label}"


def _pluck_name(label: str) -> str:
    return f"spike.pluck_{label}"


def _require_registered_pure(name: str, context: str) -> None:
    if not is_registered(name):
        raise ValueError(f"{context} needs registered pure {name!r}")


def _require_label_glue(label: str) -> None:
    _require_registered_pure(_assign_name(label), f"label {label!r}")
    _require_registered_pure(_pluck_name(label), f"label {label!r}")


def _merge_name(left: str, right: str) -> str:
    return f"spike.merge_{left}_{right}"


def _pack_name(flow_name: str, bound_names: Sequence[str], item_name: str) -> str:
    bound_part = "_".join(bound_names)
    return f"spike.pack_{flow_name}_{bound_part}_{item_name}"


def _unpack_name(flow_name: str) -> str:
    return f"spike.unpack_{flow_name}_args"


def _sanitize_label(value: str) -> str:
    return value.replace(".", "_").replace("-", "_")


def _label_from_authoring_line(kind: str, fallback_name: str) -> Optional[str]:
    frame = inspect.currentframe()
    if frame is None:
        return None
    frame = frame.f_back
    while frame is not None:
        if frame.f_code.co_filename == __file__:
            frame = frame.f_back
            continue
        line = linecache.getline(frame.f_code.co_filename, frame.f_lineno)
        if line:
            try:
                tree = ast.parse(textwrap.dedent(line))
            except SyntaxError:
                return None
            if tree.body:
                node = tree.body[0]
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    if isinstance(target, ast.Name):
                        return target.id
                if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    return node.target.id
                if isinstance(node, ast.Return):
                    return "return_arg" if kind == "merge" else "return_value"
        frame = frame.f_back
    return _sanitize_label(f"{kind}_{fallback_name}")


def _default_output_label(kind: str, name: str, inputs: Sequence["Handle"]) -> str:
    captured = _label_from_authoring_line(kind, name)
    if captured is not None:
        return captured
    if kind == "merge" and inputs:
        return _sanitize_label(f"merge_{'_'.join(handle.label for handle in inputs)}")
    return _sanitize_label(f"{kind}_{name}")


@dataclass
class Step:
    kind: str
    name: str
    inputs: tuple["Handle", ...]
    output: "Handle"
    target: Any = None
    then: Optional["FlowDef"] = None
    orelse: Any = None
    cases: Optional[dict[str, Any]] = None
    default: Any = None


@dataclass
class Graph:
    name: str
    params: list["Handle"] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    output: Optional["Handle"] = None
    labels: set[str] = field(default_factory=set)

    def new_handle(self, label: str) -> "Handle":
        if label in self.labels:
            raise ValueError(
                f"label {label!r} is already bound in flow {self.name!r}; "
                "spike flow handles are single-assignment, so choose a new "
                "Python variable name for the derived value"
            )
        self.labels.add(label)
        return Handle(label=label, graph=self)

    def append(
        self,
        kind: str,
        name: str,
        inputs: Sequence["Handle"],
        *,
        label: Optional[str] = None,
        target: Any = None,
        then: Optional["FlowDef"] = None,
        orelse: Any = None,
        cases: Optional[dict[str, Any]] = None,
        default: Any = None,
    ) -> "Handle":
        output_label = label or _default_output_label(kind, name, inputs)
        if kind not in {"cond", "switch"}:
            _require_label_glue(output_label)
        if kind == "merge":
            _require_registered_pure(name, "merge step")
        out = self.new_handle(output_label)
        self.steps.append(
            Step(
                kind=kind,
                name=name,
                inputs=tuple(inputs),
                output=out,
                target=target,
                then=then,
                orelse=orelse,
                cases=cases,
                default=default,
            )
        )
        return out


_GRAPH_STACK: list[Graph] = []


def _current_graph() -> Graph:
    if not _GRAPH_STACK:
        raise RuntimeError("@flow authoring operation used outside a flow definition")
    return _GRAPH_STACK[-1]


def _ensure_handle(value: Any) -> "Handle":
    if not isinstance(value, Handle):
        if isinstance(value, BoundFlow):
            raise TypeError(
                "unsaturated @flow application is a closure-converted body, "
                "not runtime data; pass it to each(...) or supply Handles for "
                "all flow parameters"
            )
        raise TypeError("spike flow operations currently require Handle inputs")
    return value


class Handle:
    def __init__(self, label: str, graph: Optional[Graph] = None) -> None:
        self.label = label
        self.graph = graph

    @classmethod
    def synthetic(cls, label: str) -> "Handle":
        return cls(label)

    def __or__(self, other: object) -> "Handle":
        rhs = _ensure_handle(other)
        graph = self.graph or rhs.graph or _current_graph()
        return graph.append("merge", _merge_name(self.label, rhs.label), [self, rhs])

    def __getitem__(self, key: str) -> "Handle":
        graph = self.graph or _current_graph()
        return graph.append("pluck", str(key), [self], label=str(key))

    def __bool__(self) -> bool:
        raise TypeError("Handle truthiness is not runtime data. Use cond(pred, input, then=..., orelse=...).")

    def __iter__(self) -> object:
        raise TypeError("Handle iteration is not runtime data. Use each(body, max_parallel=..., reducer=...).")

    def __repr__(self) -> str:
        return f"Handle({self.label})"


class ToolRef:
    def __init__(self, tool: Tool[Any, Any]) -> None:
        self.tool = tool
        self.name = tool.name

    def __call__(self, value: Handle) -> Handle:
        return apply(self, value)

    def to_ir(self) -> Node:
        return self.tool.to_ir()


class FlowDef(FlowLike[Any, Any]):
    def __init__(self, fn: Callable[..., Any]) -> None:
        self.fn = fn
        self.name = fn.__name__
        self.graph = Graph(fn.__name__)
        sig = inspect.signature(fn)
        self.param_names = list(sig.parameters)
        self.graph.params = [self.graph.new_handle(name) for name in sig.parameters]
        for param in self.graph.params:
            _require_label_glue(param.label)
        _GRAPH_STACK.append(self.graph)
        try:
            result = fn(*self.graph.params)
        finally:
            _GRAPH_STACK.pop()
        if isinstance(result, BoundFlow):
            raise TypeError(
                "unsaturated @flow application cannot be returned or stored as "
                "runtime data; pass it directly to each(...) as a "
                "closure-converted body"
            )
        if not isinstance(result, Handle):
            raise TypeError("@flow functions must return a Handle in the spike frontend")
        self.graph.output = result

    def __call__(self, *args: Any, **kwargs: Any) -> "Handle | BoundFlow":
        supplied: dict[str, Any] = {}
        for index, arg in enumerate(args):
            if index >= len(self.param_names):
                raise TypeError(
                    f"flow {self.name!r} expected at most {len(self.param_names)} "
                    f"arguments, got {len(args)}"
                )
            supplied[self.param_names[index]] = arg
        for key, value in kwargs.items():
            if key not in self.param_names:
                raise TypeError(f"flow {self.name!r} has no parameter {key!r}")
            if key in supplied:
                raise TypeError(f"flow {self.name!r} got multiple values for {key!r}")
            supplied[key] = value

        if len(supplied) < len(self.param_names):
            return BoundFlow.from_supplied(self, supplied)

        handles = [_ensure_handle(supplied[name]) for name in self.param_names]
        graph = _current_graph()
        if len(handles) != 1:
            raise TypeError(
                "multi-argument subflow calls are not lowered by this spike; "
                "leave one argument unbound and use the partial flow as an "
                "each(...) body"
            )
        return graph.append("subflow", self.name, handles, target=self)

    def to_ir(self) -> Node:
        return compile_graph(self.graph)


@dataclass(frozen=True)
class BoundFlow(FlowLike[Any, Any]):
    flow: FlowDef
    bound_args: dict[str, Any]

    @classmethod
    def from_supplied(cls, flow_def: FlowDef, supplied: dict[str, Any]) -> "BoundFlow":
        for name, value in supplied.items():
            if isinstance(value, Handle):
                continue
            try:
                json.dumps(value, sort_keys=True)
            except TypeError as exc:
                raise TypeError(
                    f"bound argument {name!r} for flow {flow_def.name!r} must be "
                    "JSON-serializable in this spike"
                ) from exc
        ordered = {
            name: supplied[name] for name in flow_def.param_names if name in supplied
        }
        return cls(flow=flow_def, bound_args=ordered)

    @property
    def remaining_param_names(self) -> list[str]:
        return [
            name for name in self.flow.param_names if name not in self.bound_args
        ]

    def _pack_pure_name(self) -> str:
        remaining = self.remaining_param_names
        if len(remaining) != 1:
            raise ValueError(
                f"closure-converted each body {self.flow.name!r} must leave "
                f"exactly one unbound item parameter; remaining={remaining!r}"
            )
        return _pack_name(self.flow.name, list(self.bound_args), remaining[0])

    def to_ir(self) -> Node:
        pack_name = self._pack_pure_name()
        _require_registered_pure(pack_name, f"partial flow {self.flow.name!r}")
        return dsl.seq(dsl.arr(pack_name), self.flow.to_ir())


@dataclass
class EachDef(FlowLike[Any, Any]):
    body: FlowDef | BoundFlow
    max_parallel: Optional[int] = None
    reducer: Optional[str] = None

    def to_ir(self) -> Node:
        return dsl.each(
            self.body.to_ir(),
            max_parallel=self.max_parallel,
            reducer=self.reducer,
        )


def flow(fn: Callable[..., Any]) -> FlowDef:
    return FlowDef(fn)


def tool(tool_obj: Tool[Any, Any]) -> ToolRef:
    return ToolRef(tool_obj)


def think(reasoner_name: str, value: Handle) -> Handle:
    handle = _ensure_handle(value)
    graph = handle.graph or _current_graph()
    return graph.append("think", reasoner_name, [handle], target=reasoner_name)


def apply(fn: Any, value: Handle) -> Handle:
    handle = _ensure_handle(value)
    if isinstance(fn, ToolRef):
        graph = handle.graph or _current_graph()
        return graph.append("tool", fn.name, [handle], target=fn.tool)
    if isinstance(fn, Tool):
        graph = handle.graph or _current_graph()
        return graph.append("tool", fn.name, [handle], target=fn)
    if isinstance(fn, Pure):
        graph = handle.graph or _current_graph()
        return graph.append("pure", fn.name, [handle], target=fn)
    if isinstance(fn, FlowDef):
        return fn(handle)
    raise TypeError(
        "Handle application needs a registered Tool, Pure, @flow function, or think(...); "
        f"got {getattr(fn, '__name__', type(fn).__name__)}"
    )


def cond(pred: str | Pure, value: Handle, *, then: FlowDef, orelse: Any) -> Handle:
    handle = _ensure_handle(value)
    graph = handle.graph or _current_graph()
    return graph.append(
        "cond",
        _pure_name(pred),
        [handle],
        label="cond",
        then=then,
        orelse=orelse,
    )


def switch(
    selector: str | Pure,
    value: Handle,
    *,
    cases: dict[str, Any],
    default: Any,
) -> Handle:
    handle = _ensure_handle(value)
    graph = handle.graph or _current_graph()
    return graph.append(
        "switch",
        _pure_name(selector),
        [handle],
        label="switch",
        cases=cases,
        default=default,
    )


def each(
    body: FlowDef | BoundFlow,
    *,
    max_parallel: Optional[int] = None,
    reducer: str | Pure | None = None,
) -> EachDef:
    if isinstance(body, FlowDef) and len(body.param_names) != 1:
        raise ValueError(
            f"each body {body.name!r} must take one item parameter or be a "
            "partially-applied @flow with exactly one unbound item parameter"
        )
    if isinstance(body, BoundFlow):
        body._pack_pure_name()
    return EachDef(
        body=body,
        max_parallel=max_parallel,
        reducer=None if reducer is None else _pure_name(reducer),
    )


def _step_flow(step: Step) -> Node:
    input_label = step.inputs[0].label
    if step.kind == "tool":
        return dsl.seq(dsl.arr(_pluck_name(input_label)), step.target.to_ir())
    if step.kind == "think":
        return dsl.seq(dsl.arr(_pluck_name(input_label)), dsl.think(step.name))
    if step.kind == "pure":
        return dsl.seq(dsl.arr(_pluck_name(input_label)), dsl.arr(step.name))
    raise ValueError(f"step kind {step.kind!r} cannot be lowered as a primitive")


def _compile_arm(arm: Any) -> Node:
    if isinstance(arm, FlowDef):
        return arm.to_ir()
    if isinstance(arm, Pure):
        return dsl.arr(arm.name)
    if isinstance(arm, Node):
        return arm
    if isinstance(arm, FlowLike):
        return arm.to_ir()
    raise TypeError(f"unsupported branch arm {arm!r}")


def compile_graph(graph: Graph) -> Node:
    if not graph.params:
        raise ValueError("spike flows need at least one parameter")
    if graph.output is None:
        raise ValueError("spike flow has no output")

    if len(graph.params) == 1:
        nodes: list[Node] = [dsl.arr(_assign_name(graph.params[0].label))]
    else:
        unpack_name = _unpack_name(graph.name)
        _require_registered_pure(unpack_name, f"flow {graph.name!r}")
        nodes = [dsl.arr(unpack_name)]
    current_kind = "env"
    current_label = graph.params[0].label

    for step in graph.steps:
        if step.kind in {"tool", "think", "pure"}:
            nodes.append(dsl.par(dsl.ident(), _step_flow(step)))
            nodes.append(dsl.arr(_assign_name(step.output.label)))
            current_kind = "env"
            current_label = step.output.label
            continue
        if step.kind == "merge":
            nodes.append(dsl.arr(step.name))
            nodes.append(dsl.arr(_assign_name(step.output.label)))
            current_kind = "env"
            current_label = step.output.label
            continue
        if step.kind == "pluck":
            nodes.append(dsl.arr(_pluck_name(step.inputs[0].label)))
            nodes.append(dsl.arr(_assign_name(step.output.label)))
            current_kind = "env"
            current_label = step.output.label
            continue
        if step.kind == "cond":
            nodes.append(dsl.arr(_pluck_name(step.inputs[0].label)))
            assert step.then is not None
            nodes.append(
                dsl.alt(
                    step.name,
                    if_true=step.then.to_ir(),
                    if_false=_compile_arm(step.orelse),
                )
            )
            current_kind = "raw"
            current_label = step.output.label
            continue
        if step.kind == "switch":
            nodes.append(dsl.arr(_pluck_name(step.inputs[0].label)))
            assert step.cases is not None
            nodes.append(
                dsl.alt(
                    select=step.name,
                    cases={key: _compile_arm(arm) for key, arm in step.cases.items()},
                    default=_compile_arm(step.default),
                )
            )
            current_kind = "raw"
            current_label = step.output.label
            continue
        if step.kind == "subflow":
            nodes.append(dsl.par(dsl.ident(), dsl.seq(dsl.arr(_pluck_name(step.inputs[0].label)), step.target.to_ir())))
            nodes.append(dsl.arr(_assign_name(step.output.label)))
            current_kind = "env"
            current_label = step.output.label
            continue
        raise ValueError(f"unsupported step kind: {step.kind}")

    if current_kind == "env" and graph.output.label == current_label:
        nodes.append(dsl.arr(_pluck_name(graph.output.label)))
    return dsl.seq(*nodes)
