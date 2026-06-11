"""Frontend-neutral DAG model and compiler to core IR.

The future ``@flow`` frontend will build this graph, but the model is deliberately
plain data so tests and other frontends can construct it directly.
"""

from __future__ import annotations

import math
import warnings
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Optional, Sequence

from . import dsl
from .contracts import CONSERVATIVE_DEFAULT, ToolContract
from .ir import Ann, Node, SourceSpan, canonical_json
from .kinds import Effect, Op


class GraphDefinitionError(ValueError):
    """Define-time graph construction or compilation error."""


CAPTURE_SIZE_WARNING_BYTES = 4096
"""Warn when one static closure capture exceeds this canonical JSON byte size."""

BRANCH_VALUE_KEY = "__branch__"
"""Internal env key for frontend subject-shaped branch predicates/selectors."""


class StepKind(str, Enum):
    TOOL = "tool"
    THINK = "think"
    PURE = "pure"
    PASSTHROUGH = "passthrough"
    COND = "cond"
    SWITCH = "switch"
    EACH = "each"


@dataclass(frozen=True)
class InputEdge:
    """A declared data edge from a prior step output into a named input slot.

    Public graph construction does not support input renaming yet: user-supplied
    input specs must use the same ``name`` and ``source``. The compiler reserves
    distinct names for internal slots such as the ``items`` edge on ``each``.
    """

    name: str
    source: str


@dataclass(frozen=True)
class StepNode:
    """One single-assignment DAG step."""

    kind: StepKind
    ref: str
    inputs: tuple[InputEdge, ...]
    output: str
    contract: Optional[ToolContract] = None
    ann: Optional[Ann] = None
    source: Optional[SourceSpan] = None
    args: Optional[dict[str, Any]] = None
    order: int = 0
    if_true: Optional["Graph"] = None
    if_false: Optional["Graph"] = None
    cases: Optional[dict[str, "Graph"]] = None
    default: Optional["Graph"] = None
    body: Optional["Graph"] = None
    max_parallel: Optional[int] = None
    reducer: Optional[str] = None
    const_captures: Optional[dict[str, Any]] = None
    branch_subject: Optional[str] = None


InputSpec = str | InputEdge | tuple[str, str]


@dataclass
class Graph:
    """A collection of authored steps with unique output names."""

    input_name: str = "__input__"
    output_name: Optional[str] = None
    source: Optional[SourceSpan] = None

    def __post_init__(self) -> None:
        self.steps: list[StepNode] = []
        self._outputs: dict[str, StepNode] = {}
        self._explicit_output_name = self.output_name is not None

    def add_step(
        self,
        kind: StepKind | str,
        ref: str,
        *,
        inputs: Sequence[InputSpec] = (),
        output: str,
        contract: Optional[ToolContract] = None,
        ann: Optional[Ann] = None,
        source: Optional[SourceSpan] = None,
        args: Optional[dict[str, Any]] = None,
        tool: Any = None,
    ) -> StepNode:
        """Add a step, rejecting output-name collisions immediately."""
        step_kind = StepKind(kind)
        if output in self._outputs:
            raise GraphDefinitionError(f"output name collision: {output}")

        resolved_ref = ref
        resolved_contract = contract
        if tool is not None:
            resolved_ref = str(getattr(tool, "name", ref))
            tool_contract = getattr(tool, "contract", None)
            if isinstance(tool_contract, ToolContract):
                resolved_contract = tool_contract
        elif step_kind is StepKind.TOOL and resolved_contract is None:
            resolved_contract = CONSERVATIVE_DEFAULT

        node = StepNode(
            kind=step_kind,
            ref=resolved_ref,
            inputs=_coerce_user_inputs(inputs, source),
            output=output,
            contract=resolved_contract,
            ann=ann,
            source=source,
            args=args,
            order=len(self.steps),
        )
        self.steps.append(node)
        self._outputs[output] = node
        if not self._explicit_output_name:
            self.output_name = output
        return node

    def add_cond(
        self,
        pred: str,
        *,
        inputs: Sequence[InputSpec] = (),
        output: str,
        if_true: "Graph",
        if_false: "Graph",
        source: Optional[SourceSpan] = None,
        branch_subject: Optional[InputSpec] = None,
    ) -> StepNode:
        """Add a binary branch step whose arms are sub-graphs over env fields."""
        return self._add_branch(
            StepKind.COND,
            pred,
            inputs=inputs,
            output=output,
            if_true=if_true,
            if_false=if_false,
            source=source,
            branch_subject=branch_subject,
        )

    def add_switch(
        self,
        select: str,
        *,
        inputs: Sequence[InputSpec] = (),
        output: str,
        cases: dict[str, "Graph"],
        default: Optional["Graph"] = None,
        source: Optional[SourceSpan] = None,
        branch_subject: Optional[InputSpec] = None,
    ) -> StepNode:
        """Add a selector branch step lowered to the existing select/cases alt."""
        if not cases:
            raise GraphDefinitionError("switch branch needs at least one case")
        return self._add_branch(
            StepKind.SWITCH,
            select,
            inputs=inputs,
            output=output,
            cases=dict(cases),
            default=default,
            source=source,
            branch_subject=branch_subject,
        )

    def add_each(
        self,
        body: "Graph",
        *,
        items: InputSpec,
        output: str,
        max_parallel: Optional[int] = None,
        reducer: Optional[str] = None,
        const_captures: Optional[dict[str, Any]] = None,
        source: Optional[SourceSpan] = None,
    ) -> StepNode:
        """Add a dynamic fan-out step over a list-valued input edge.

        ``body`` is compiled once and applied to each item. Plain JSON captures
        are supplied through ``const_captures`` and pinned into arr static args.
        Body references to names produced by this graph are runtime handle
        captures and lower to a pre-each env projection.
        """
        if output in self._outputs:
            raise GraphDefinitionError(f"output name collision: {output}")
        if max_parallel is not None and max_parallel < 1:
            raise GraphDefinitionError("each max_parallel must be >= 1")

        consts = dict(const_captures or {})
        for name, value in consts.items():
            _validate_const_capture(name, value)
            _warn_if_oversized_capture(name, value)

        available = set(self._outputs)
        available.add(self.input_name)
        body_externals = _external_sources(body)
        for capture in body_externals:
            if capture in consts:
                continue
            if capture not in available:
                raise GraphDefinitionError(f"foreign-scope handle capture: {capture}")

        item_edge = _coerce_user_input(items, source)
        node = StepNode(
            kind=StepKind.EACH,
            ref="each",
            inputs=(InputEdge(name="items", source=item_edge.source),),
            output=output,
            source=source,
            order=len(self.steps),
            body=body,
            max_parallel=max_parallel,
            reducer=reducer,
            const_captures=consts,
        )
        self.steps.append(node)
        self._outputs[output] = node
        if not self._explicit_output_name:
            self.output_name = output
        return node

    def _add_branch(
        self,
        kind: StepKind,
        ref: str,
        *,
        inputs: Sequence[InputSpec],
        output: str,
        source: Optional[SourceSpan],
        if_true: Optional["Graph"] = None,
        if_false: Optional["Graph"] = None,
        cases: Optional[dict[str, "Graph"]] = None,
        default: Optional["Graph"] = None,
        branch_subject: Optional[InputSpec] = None,
    ) -> StepNode:
        if output in self._outputs:
            raise GraphDefinitionError(f"output name collision: {output}")
        subject = None if branch_subject is None else _coerce_user_input(branch_subject, source).source
        node = StepNode(
            kind=kind,
            ref=ref,
            inputs=_coerce_user_inputs(inputs, source),
            output=output,
            source=source,
            order=len(self.steps),
            if_true=if_true,
            if_false=if_false,
            cases=cases,
            default=default,
            branch_subject=subject,
        )
        self.steps.append(node)
        self._outputs[output] = node
        if not self._explicit_output_name:
            self.output_name = output
        return node


def compile(graph: Graph) -> Node:
    """Compile a frontend DAG into core :class:`~composable_agents.ir.Node` IR."""
    ordered = _toposort(graph, (graph.input_name,))
    final_output = graph.output_name or (ordered[-1].output if ordered else graph.input_name)
    _validate_output_name(graph, ordered, final_output)
    if not ordered:
        return dsl.ident()

    if _is_linear_chain(ordered, final_output):
        return _stamp_missing_sources(_seq([_leaf(step) for step in ordered]))

    layers = _effect_fenced_layers(ordered, (graph.input_name,))
    pieces: list[Node] = []
    env_started = False
    current_fields: list[str] = []

    for index, layer in enumerate(layers):
        if index == len(layers) - 1 and len(layer) == 1 and layer[0].output == final_output:
            if not env_started:
                if layer[0].kind in {StepKind.COND, StepKind.SWITCH}:
                    pieces.append(_arr("std.init", {"key": graph.input_name}, None))
                    pieces.extend(_seq_items(_step_from_env(layer[0], graph.input_name)))
                else:
                    pieces.append(_leaf(layer[0]))
            else:
                pieces.extend(_seq_items(_step_from_env(layer[0], graph.input_name)))
            return _stamp_missing_sources(_seq(pieces))

        if (
            not env_started
            and len(layer) == 1
            and not layer[0].inputs
            and not _later_layers_consume_input(layers, index, graph.input_name)
        ):
            first = layer[0]
            pieces.append(_leaf(first))
            pieces.append(_arr("std.init", {"key": first.output}, first.source))
            env_started = True
            current_fields = [first.output]
            live = _live_fields_after_layer(
                layers,
                index,
                final_output,
                current_fields,
                graph.input_name,
            )
            if live != current_fields:
                pieces.append(_prune_env(live, first.source))
                current_fields = live
            continue

        if not env_started:
            pieces.append(_arr("std.init", {"key": graph.input_name}, None))
            env_started = True
            current_fields = [graph.input_name]

        pieces.extend(_compile_env_layer(layer, graph.input_name))
        current_fields = _append_unique(current_fields, [step.output for step in layer])
        live = _live_fields_after_layer(
            layers,
            index,
            final_output,
            current_fields,
            graph.input_name,
        )
        if live != current_fields:
            pieces.append(_prune_env(live, layer[0].source))
            current_fields = live

    pieces.append(_arr("std.pluck", {"key": final_output}, _source_for_output(ordered, final_output)))
    return _stamp_missing_sources(_seq(pieces))


def compile_env(graph: Graph, initial_fields: Sequence[str]) -> Node:
    """Compile ``graph`` from an existing env record with ``initial_fields``.

    This is an additive frontend seam for partially-bound ``@flow`` values: the
    public input is first packed into an env record, then the normal env compiler
    runs with the same liveness and effect-fencing semantics as branch/each arms.
    """
    return _compile_env_graph(graph, initial_fields)


def _validate_const_capture(name: str, value: Any) -> None:
    if not _json_capture_ok(value):
        raise GraphDefinitionError(f"const capture {name!r} must be canonical JSON")
    try:
        canonical_json(value)
    except TypeError as exc:
        raise GraphDefinitionError(f"const capture {name!r} must be canonical JSON") from exc


def _json_capture_ok(value: Any) -> bool:
    if isinstance(value, dict):
        return all(isinstance(key, str) and _json_capture_ok(child) for key, child in value.items())
    if isinstance(value, list):
        return all(_json_capture_ok(item) for item in value)
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    return False


def _warn_if_oversized_capture(name: str, value: Any) -> None:
    size = len(canonical_json(value).encode("utf-8"))
    if size > CAPTURE_SIZE_WARNING_BYTES:
        warnings.warn(
            (
                f"const capture {name!r} is {size} bytes; values larger than "
                f"{CAPTURE_SIZE_WARNING_BYTES} bytes are duplicated into the frozen artifact"
            ),
            stacklevel=3,
        )


def _coerce_input(value: InputSpec) -> InputEdge:
    if isinstance(value, InputEdge):
        return value
    if isinstance(value, str):
        return InputEdge(name=value, source=value)
    name, source = value
    return InputEdge(name=name, source=source)


def _coerce_user_inputs(
    values: Sequence[InputSpec],
    source: Optional[SourceSpan],
) -> tuple[InputEdge, ...]:
    return tuple(_coerce_user_input(value, source) for value in values)


def _coerce_user_input(value: InputSpec, source: Optional[SourceSpan]) -> InputEdge:
    edge = _coerce_input(value)
    if edge.name != edge.source:
        raise GraphDefinitionError(
            "input edge renaming is not supported"
            f"{_source_suffix(source)}: name={edge.name!r}, source={edge.source!r}; "
            f"use inputs=[{edge.source!r}] and add an explicit pure step if the value "
            "must be reshaped"
        )
    return edge


def _validate_output_name(graph: Graph, ordered: Sequence[StepNode], final_output: str) -> None:
    if final_output == graph.input_name:
        return
    outputs = {step.output for step in ordered}
    if final_output in outputs:
        return
    available = ", ".join(sorted(outputs)) if outputs else "<none>"
    raise GraphDefinitionError(
        f"unknown output name: {final_output}"
        f"{_source_suffix(graph.source)}; available outputs: {available}; "
        "return one of the available handles or set Graph(output_name=...) to one"
    )


def _source_suffix(source: Optional[SourceSpan]) -> str:
    if source is None:
        return ""
    parts = [f" at {source.file}:{source.line}"]
    if source.function:
        parts.append(f" in {source.function}")
    if source.text:
        parts.append(f": {source.text}")
    return "".join(parts)


def _toposort(graph: Graph, external_sources: Iterable[str] = ()) -> list[StepNode]:
    by_output = {step.output: step for step in graph.steps}
    external = set(external_sources)
    visiting: set[str] = set()
    visited: set[str] = set()
    out: list[StepNode] = []

    def visit(step: StepNode, stack: list[str]) -> None:
        if step.output in visited:
            return
        if step.output in visiting:
            start = stack.index(step.output) if step.output in stack else 0
            cycle = stack[start:] + [step.output]
            raise GraphDefinitionError("cycle detected: " + " -> ".join(cycle))

        visiting.add(step.output)
        stack.append(step.output)
        for source in _input_sources(step):
            dep = by_output.get(source)
            if dep is not None:
                visit(dep, stack)
                if dep.order > step.order:
                    raise GraphDefinitionError(
                        "forward input edge "
                        f"{step.output!r} consumes {source!r}; steps must be declared "
                        "in dependency order"
                    )
            elif source != graph.input_name and source not in external:
                raise GraphDefinitionError(f"unknown input edge source: {source}")
        stack.pop()
        visiting.remove(step.output)
        visited.add(step.output)
        out.append(step)

    for step in graph.steps:
        visit(step, [])

    return out


def _is_linear_chain(steps: Sequence[StepNode], final_output: str) -> bool:
    if not steps or steps[-1].output != final_output:
        return False
    if any(step.kind in {StepKind.COND, StepKind.SWITCH} for step in steps):
        return False
    if any(step.kind is StepKind.EACH and _handle_captures(step) for step in steps):
        return False
    if steps[0].inputs:
        return False
    for idx, step in enumerate(steps[1:], start=1):
        if len(step.inputs) != 1 or step.inputs[0].source != steps[idx - 1].output:
            return False
    consumers: dict[str, int] = defaultdict(int)
    for step in steps:
        for source in _input_sources(step):
            consumers[source] += 1
    return all(consumers.get(step.output, 0) <= 1 for step in steps)


def _effect_fenced_layers(
    steps: Sequence[StepNode],
    external_sources: Iterable[str] = (),
) -> list[list[StepNode]]:
    remaining = list(steps)
    done: set[str] = set(external_sources)
    layers: list[list[StepNode]] = []

    while remaining:
        first = remaining[0]
        if not _deps_done(first, done):
            pending = ", ".join(step.output for step in remaining)
            raise GraphDefinitionError(f"cycle detected among: {pending}")

        if _is_barrier(first):
            layers.append([first])
            done.add(first.output)
            remaining.pop(0)
            continue

        group: list[StepNode] = []
        stop = 0
        for idx, step in enumerate(remaining):
            if _is_barrier(step):
                break
            if _deps_done(step, done):
                group.append(step)
                stop = idx + 1
            elif step.inputs:
                break

        if not group:
            raise GraphDefinitionError("cycle detected among: " + ", ".join(s.output for s in remaining))

        selected = {step.output for step in group}
        layers.append(group)
        done.update(selected)
        remaining = [step for idx, step in enumerate(remaining) if idx >= stop or step.output not in selected]

    return layers


def _deps_done(step: StepNode, done: set[str]) -> bool:
    return all(source in done for source in _input_sources(step))


def _is_barrier(step: StepNode) -> bool:
    if step.kind in {StepKind.COND, StepKind.SWITCH}:
        return _branch_has_barrier(step)
    if step.kind is StepKind.EACH:
        if step.body is None:
            raise GraphDefinitionError(f"each step {step.output!r} needs a body")
        return _graph_has_barrier(step.body)
    if step.kind is not StepKind.TOOL:
        return False
    contract = step.contract or CONSERVATIVE_DEFAULT
    return contract.effect in {Effect.WRITE, Effect.EXTERNAL, Effect.DANGEROUS}


def _compile_env_layer(layer: Sequence[StepNode], input_name: str) -> list[Node]:
    branches = [_step_from_env(step, input_name) for step in layer]
    if len(branches) == 1:
        step = layer[0]
        # Even when later liveness drops this output, std.assign is the current
        # std-family fold-back from [env, step_result] to env. Eliding it would
        # need a new wire-format-stable discard pure.
        return [
            _par([_with_source(dsl.ident(), step.source), branches[0]], step.source),
            _arr("std.assign", {"key": step.output}, step.source),
        ]
    return [
        _par([_with_source(dsl.ident(), layer[0].source), *branches], layer[0].source),
        _arr("std.collect", {"fields": [step.output for step in layer]}, layer[0].source),
    ]


def _step_from_env(step: StepNode, input_name: str) -> Node:
    if step.kind in {StepKind.COND, StepKind.SWITCH}:
        return _branch_from_env(step)
    if step.kind is StepKind.EACH:
        return _each_from_env(step)
    if step.kind is StepKind.PURE and step.ref == "std.merge" and len(step.inputs) > 1:
        return _input_projection(step, input_name)
    return _seq([_input_projection(step, input_name), _leaf(step)])


def _input_projection(step: StepNode, input_name: str) -> Node:
    if not step.inputs:
        return _arr("std.pluck", {"key": input_name}, step.source)
    fields = [edge.source for edge in step.inputs]
    if len(fields) == 1:
        return _arr("std.pluck", {"key": fields[0]}, step.source)
    return _arr("std.merge", {"fields": fields}, step.source)


def _leaf(step: StepNode) -> Node:
    if step.kind is StepKind.TOOL:
        return _with_source(dsl.call(step.ref, ann=step.ann), step.source)
    if step.kind is StepKind.THINK:
        return _with_source(dsl.think(step.ref, ann=step.ann), step.source)
    if step.kind is StepKind.PURE:
        return _with_source(dsl.arr(step.ref, step.args), step.source)
    if step.kind is StepKind.PASSTHROUGH:
        return _with_source(dsl.ident(), step.source)
    if step.kind in {StepKind.COND, StepKind.SWITCH}:
        return _branch_from_env(step)
    if step.kind is StepKind.EACH:
        return _each_from_flowing_input(step)
    raise AssertionError(f"unhandled step kind: {step.kind}")


def _each_from_env(step: StepNode) -> Node:
    if step.body is None:
        raise GraphDefinitionError(f"each step {step.output!r} needs a body")
    item_source = _each_item_source(step)
    handle_captures = _handle_captures(step)
    consts = dict(step.const_captures or {})
    body = _compile_each_body(step, packed_input=bool(handle_captures), consts=consts)
    each_node = _with_source(
        dsl.each(body, max_parallel=step.max_parallel, reducer=step.reducer),
        step.source,
    )
    if handle_captures:
        return _seq(
            [
                _arr(
                    "std.each_pack",
                    {
                        "items": item_source,
                        "item": step.body.input_name,
                        "fields": {name: name for name in handle_captures},
                        "consts": consts,
                    },
                    step.source,
                ),
                each_node,
            ]
        )
    return _seq([_arr("std.pluck", {"key": item_source}, step.source), each_node])


def _each_from_flowing_input(step: StepNode) -> Node:
    if step.body is None:
        raise GraphDefinitionError(f"each step {step.output!r} needs a body")
    handle_captures = _handle_captures(step)
    if handle_captures:
        raise GraphDefinitionError(
            f"each step {step.output!r} with handle captures requires env compilation"
        )
    body = _compile_each_body(step, packed_input=False, consts=dict(step.const_captures or {}))
    return _with_source(
        dsl.each(body, max_parallel=step.max_parallel, reducer=step.reducer),
        step.source,
    )


def _compile_each_body(
    step: StepNode,
    *,
    packed_input: bool,
    consts: dict[str, Any],
) -> Node:
    if step.body is None:
        raise GraphDefinitionError(f"each step {step.output!r} needs a body")
    handle_captures = _handle_captures(step)
    initial_fields = [step.body.input_name, *handle_captures, *sorted(consts)]

    if not packed_input and not consts:
        return _stamp_missing_sources(_compile_raw_item_body(step.body))

    pieces: list[Node] = []
    if packed_input:
        unpack_fields = {field: field for field in initial_fields}
    else:
        pack_fields = {step.body.input_name: {"input": True}}
        for name in sorted(consts):
            pack_fields[name] = {"const": consts[name]}
        pieces.append(_arr("std.pack", {"fields": pack_fields}, step.source))
        unpack_fields = {field: field for field in initial_fields}
    pieces.append(_arr("std.unpack", {"fields": unpack_fields}, step.source))
    pieces.extend(_seq_items(_compile_env_graph(step.body, initial_fields)))
    return _stamp_missing_sources(_seq(pieces))


def _compile_raw_item_body(graph: Graph) -> Node:
    return compile(graph)


def _each_item_source(step: StepNode) -> str:
    if len(step.inputs) != 1:
        raise GraphDefinitionError(f"each step {step.output!r} needs one list input")
    return step.inputs[0].source


def _handle_captures(step: StepNode) -> list[str]:
    if step.kind is not StepKind.EACH or step.body is None:
        return []
    consts = set(step.const_captures or {})
    return [source for source in _external_sources(step.body) if source not in consts]


def _arr(name: str, args: dict[str, Any], source: Optional[SourceSpan]) -> Node:
    return _with_source(dsl.arr(name, args), source)


def _with_source(node: Node, source: Optional[SourceSpan]) -> Node:
    node.source = source
    return node


def _seq(nodes: Iterable[Node]) -> Node:
    return _stamp_missing_sources(dsl.seq(_collapse_prune_pluck_pairs(list(nodes))))


def _collapse_prune_pluck_pairs(nodes: Sequence[Node]) -> list[Node]:
    collapsed: list[Node] = []
    index = 0
    while index < len(nodes):
        current = nodes[index]
        if index + 1 < len(nodes):
            next_node = nodes[index + 1]
            key = _single_field_prune_key(current)
            if key is not None and _is_pluck_key(next_node, key):
                if next_node.source is None:
                    next_node.source = current.source
                collapsed.append(next_node)
                index += 2
                continue
        collapsed.append(current)
        index += 1
    return collapsed


def _single_field_prune_key(node: Node) -> Optional[str]:
    if node.op is not Op.ARR or node.pure != "std.pack" or not isinstance(node.args, dict):
        return None
    fields = node.args.get("fields")
    if not isinstance(fields, dict) or len(fields) != 1:
        return None
    key, selector = next(iter(fields.items()))
    if selector == {"field": key}:
        return str(key)
    return None


def _is_pluck_key(node: Node, key: str) -> bool:
    return (
        node.op is Op.ARR
        and node.pure == "std.pluck"
        and isinstance(node.args, dict)
        and node.args == {"key": key}
    )


def _par(nodes: Sequence[Node], source: Optional[SourceSpan]) -> Node:
    return _with_source(_stamp_missing_sources(dsl.par(list(nodes))), source)


def _seq_items(node: Node) -> list[Node]:
    if node.op is not Op.SEQ:
        return [node]
    items: list[Node] = []
    if node.left is not None:
        items.extend(_seq_items(node.left))
    if node.right is not None:
        items.extend(_seq_items(node.right))
    return items


def _source_for_output(steps: Sequence[StepNode], output: str) -> Optional[SourceSpan]:
    for step in steps:
        if step.output == output:
            return step.source
    return None


def _input_sources(step: StepNode) -> list[str]:
    sources = [edge.source for edge in step.inputs]
    if step.kind in {StepKind.COND, StepKind.SWITCH}:
        sources = _append_unique(sources, _branch_external_sources(step))
    if step.kind is StepKind.EACH:
        sources = _append_unique(sources, _handle_captures(step))
    return sources


def _branch_external_sources(step: StepNode) -> list[str]:
    fields: list[str] = []
    for arm in _branch_arms(step):
        fields = _append_unique(fields, _external_sources(arm))
        if _graph_consumes_input(arm):
            fields = _append_unique(fields, [arm.input_name])
    return fields


def _branch_arms(step: StepNode) -> list[Graph]:
    if step.kind is StepKind.COND:
        if step.if_true is None or step.if_false is None:
            raise GraphDefinitionError(f"cond branch {step.output!r} needs both arms")
        return [step.if_true, step.if_false]
    if step.kind is StepKind.SWITCH:
        if step.cases is None:
            raise GraphDefinitionError(f"switch branch {step.output!r} needs cases")
        arms = [step.cases[key] for key in sorted(step.cases)]
        if step.default is not None:
            arms.append(step.default)
        return arms
    return []


def _external_sources(graph: Graph) -> list[str]:
    produced = {step.output for step in graph.steps}
    fields: list[str] = []
    for step in graph.steps:
        for edge in step.inputs:
            if edge.source not in produced and edge.source != graph.input_name:
                fields.append(edge.source)
        if step.kind in {StepKind.COND, StepKind.SWITCH}:
            for source in _branch_external_sources(step):
                if source not in produced and source != graph.input_name:
                    fields.append(source)
    if graph.output_name is not None and graph.output_name not in produced:
        fields.append(graph.output_name)
    return _dedupe(fields)


def _graph_consumes_input(graph: Graph) -> bool:
    if graph.output_name == graph.input_name:
        return True
    for step in graph.steps:
        if _step_consumes_field(step, graph.input_name):
            return True
    return False


def _step_consumes_field(step: StepNode, field: str) -> bool:
    if any(edge.source == field for edge in step.inputs):
        return True
    if (
        not step.inputs
        and step.kind
        in {StepKind.TOOL, StepKind.THINK, StepKind.PURE, StepKind.PASSTHROUGH}
    ):
        return True
    if step.kind in {StepKind.COND, StepKind.SWITCH}:
        return field in _branch_input_fields(step)
    return False


def _branch_has_barrier(step: StepNode) -> bool:
    return any(_graph_has_barrier(arm) for arm in _branch_arms(step))


def _graph_has_barrier(graph: Graph) -> bool:
    return any(_is_barrier(step) for step in graph.steps)


def _branch_from_env(step: StepNode) -> Node:
    fields = _branch_input_fields(step)
    prefix = _prune_env(fields, step.source)
    if step.kind is StepKind.COND:
        if step.if_true is None or step.if_false is None:
            raise GraphDefinitionError(f"cond branch {step.output!r} needs both arms")
        pred = "std.branch_predicate" if step.branch_subject is not None else step.ref
        alt = dsl.alt(
            pred,
            _compile_branch_arm(step.if_true, fields),
            _compile_branch_arm(step.if_false, fields),
        )
    elif step.kind is StepKind.SWITCH:
        if step.cases is None:
            raise GraphDefinitionError(f"switch branch {step.output!r} needs cases")
        select = "std.branch_selector" if step.branch_subject is not None else step.ref
        alt = dsl.alt(
            select=select,
            cases={key: _compile_branch_arm(step.cases[key], fields) for key in sorted(step.cases)},
            default=None if step.default is None else _compile_branch_arm(step.default, fields),
        )
    else:
        raise AssertionError(f"unhandled branch kind: {step.kind}")
    if step.branch_subject is None:
        return _seq([prefix, _with_source(alt, step.source)])
    decision = _seq(
        [
            _arr("std.pluck", {"key": step.branch_subject}, step.source),
            _with_source(dsl.arr(step.ref), step.source),
        ]
    )
    return _seq(
        [
            prefix,
            _par([_with_source(dsl.ident(), step.source), decision], step.source),
            _arr("std.assign", {"key": BRANCH_VALUE_KEY}, step.source),
            _with_source(alt, step.source),
        ]
    )


def _branch_input_fields(step: StepNode) -> list[str]:
    fields = [edge.source for edge in step.inputs]
    if step.branch_subject is not None:
        fields = _append_unique(fields, [step.branch_subject])
    fields = _append_unique(fields, _branch_external_sources(step))
    return fields


def _compile_branch_arm(graph: Graph, incoming_fields: Sequence[str]) -> Node:
    arm_fields = _arm_entry_fields(graph, incoming_fields)
    pieces = [_prune_env(arm_fields, None)]
    pieces.extend(_seq_items(_compile_env_graph(graph, arm_fields)))
    return _seq(pieces)


def _arm_entry_fields(graph: Graph, incoming_fields: Sequence[str]) -> list[str]:
    needed = _external_sources(graph)
    if _graph_consumes_input(graph):
        needed = _append_unique(needed, [graph.input_name])
    allowed = set(incoming_fields)
    return [field for field in incoming_fields if field in needed and field in allowed]


def _compile_env_graph(graph: Graph, initial_fields: Sequence[str]) -> Node:
    ordered = _toposort(graph, initial_fields)
    final_output = graph.output_name or (ordered[-1].output if ordered else None)
    if final_output is None:
        return _stamp_missing_sources(dsl.ident())
    if not ordered:
        if final_output not in initial_fields:
            raise GraphDefinitionError(f"unknown output name: {final_output}")
        return _arr("std.pluck", {"key": final_output}, None)

    layers = _effect_fenced_layers(ordered, initial_fields)
    pieces: list[Node] = []
    current_fields = list(initial_fields)

    for index, layer in enumerate(layers):
        if index == len(layers) - 1 and len(layer) == 1 and layer[0].output == final_output:
            pieces.extend(_seq_items(_step_from_env(layer[0], graph.input_name)))
            return _stamp_missing_sources(_seq(pieces))

        pieces.extend(_compile_env_layer(layer, graph.input_name))
        current_fields = _append_unique(current_fields, [step.output for step in layer])
        live = _live_fields_after_layer(
            layers,
            index,
            final_output,
            current_fields,
            graph.input_name,
        )
        if live != current_fields:
            pieces.append(_prune_env(live, layer[0].source))
            current_fields = live

    if final_output not in current_fields:
        raise GraphDefinitionError(f"unknown output name: {final_output}")
    pieces.append(_arr("std.pluck", {"key": final_output}, _source_for_output(ordered, final_output)))
    return _stamp_missing_sources(_seq(pieces))


def _live_fields_after_layer(
    layers: Sequence[Sequence[StepNode]],
    index: int,
    final_output: str,
    current_fields: Sequence[str],
    input_name: str,
) -> list[str]:
    needed: list[str] = []
    for future_layer in layers[index + 1:]:
        for step in future_layer:
            needed = _append_unique(needed, _live_input_sources(step, input_name))
    if final_output in current_fields:
        needed.append(final_output)
    needed_set = set(needed)
    return [field for field in current_fields if field in needed_set]


def _live_input_sources(step: StepNode, input_name: str) -> list[str]:
    sources = _input_sources(step)
    if _step_consumes_field(step, input_name):
        sources = _append_unique(sources, [input_name])
    return sources


def _later_layers_consume_input(
    layers: Sequence[Sequence[StepNode]],
    index: int,
    input_name: str,
) -> bool:
    return any(
        _step_consumes_field(step, input_name)
        for future_layer in layers[index + 1:]
        for step in future_layer
    )


def _prune_env(fields: Sequence[str], source: Optional[SourceSpan]) -> Node:
    selectors = {field: {"field": field} for field in fields}
    return _arr("std.pack", {"fields": selectors}, source)


def _append_unique(values: Sequence[str], additions: Iterable[str]) -> list[str]:
    out = list(values)
    seen = set(out)
    for value in additions:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def _dedupe(values: Iterable[str]) -> list[str]:
    return _append_unique([], values)


def _stamp_missing_sources(node: Node) -> Node:
    for child in node.children():
        _stamp_missing_sources(child)
    if node.source is None:
        for child in node.children():
            if child.source is not None:
                node.source = child.source
                break
    return node
