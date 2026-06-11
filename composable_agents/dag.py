"""Frontend-neutral DAG model and compiler to core IR.

The future ``@flow`` frontend will build this graph, but the model is deliberately
plain data so tests and other frontends can construct it directly.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Optional, Sequence

from . import dsl
from .contracts import CONSERVATIVE_DEFAULT, ToolContract
from .ir import Ann, Node, SourceSpan
from .kinds import Effect, Op


class GraphDefinitionError(ValueError):
    """Define-time graph construction or compilation error."""


class StepKind(str, Enum):
    TOOL = "tool"
    THINK = "think"
    PURE = "pure"
    PASSTHROUGH = "passthrough"


@dataclass(frozen=True)
class InputEdge:
    """A declared data edge from a prior step output into a named input slot."""

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
    order: int = 0


InputSpec = str | InputEdge | tuple[str, str]


@dataclass
class Graph:
    """A collection of authored steps with unique output names."""

    input_name: str = "__input__"
    output_name: Optional[str] = None

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
            inputs=tuple(_coerce_input(inp) for inp in inputs),
            output=output,
            contract=resolved_contract,
            ann=ann,
            source=source,
            order=len(self.steps),
        )
        self.steps.append(node)
        self._outputs[output] = node
        if not self._explicit_output_name:
            self.output_name = output
        return node


def compile(graph: Graph) -> Node:
    """Compile a frontend DAG into core :class:`~composable_agents.ir.Node` IR."""
    ordered = _toposort(graph)
    if not ordered:
        return dsl.ident()

    final_output = graph.output_name or ordered[-1].output
    if _is_linear_chain(ordered, final_output):
        return _seq([_leaf(step) for step in ordered])

    layers = _effect_fenced_layers(ordered)
    pieces: list[Node] = []
    env_started = False

    for index, layer in enumerate(layers):
        if index == len(layers) - 1 and len(layer) == 1 and layer[0].output == final_output:
            if not env_started:
                pieces.append(_leaf(layer[0]))
            else:
                pieces.extend(_seq_items(_step_from_env(layer[0], graph.input_name)))
            return _seq(pieces)

        if not env_started and len(layer) == 1 and not layer[0].inputs:
            first = layer[0]
            pieces.append(_leaf(first))
            pieces.append(_arr("std.init", {"key": first.output}, first.source))
            env_started = True
            continue

        if not env_started:
            pieces.append(_arr("std.init", {"key": graph.input_name}, None))
            env_started = True

        pieces.extend(_compile_env_layer(layer, graph.input_name))

    pieces.append(_arr("std.pluck", {"key": final_output}, _source_for_output(ordered, final_output)))
    return _seq(pieces)


def _coerce_input(value: InputSpec) -> InputEdge:
    if isinstance(value, InputEdge):
        return value
    if isinstance(value, str):
        return InputEdge(name=value, source=value)
    name, source = value
    return InputEdge(name=name, source=source)


def _toposort(graph: Graph) -> list[StepNode]:
    by_output = {step.output: step for step in graph.steps}
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
        for edge in step.inputs:
            dep = by_output.get(edge.source)
            if dep is not None:
                visit(dep, stack)
            elif edge.source != graph.input_name:
                raise GraphDefinitionError(f"unknown input edge source: {edge.source}")
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
    if steps[0].inputs:
        return False
    for idx, step in enumerate(steps[1:], start=1):
        if len(step.inputs) != 1 or step.inputs[0].source != steps[idx - 1].output:
            return False
    consumers: dict[str, int] = defaultdict(int)
    for step in steps:
        for edge in step.inputs:
            consumers[edge.source] += 1
    return all(consumers.get(step.output, 0) <= 1 for step in steps)


def _effect_fenced_layers(steps: Sequence[StepNode]) -> list[list[StepNode]]:
    remaining = list(steps)
    done: set[str] = set()
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
    return all(edge.source in done for edge in step.inputs)


def _is_barrier(step: StepNode) -> bool:
    if step.kind is not StepKind.TOOL:
        return False
    contract = step.contract or CONSERVATIVE_DEFAULT
    return contract.effect in {Effect.WRITE, Effect.EXTERNAL, Effect.DANGEROUS}


def _compile_env_layer(layer: Sequence[StepNode], input_name: str) -> list[Node]:
    branches = [_step_from_env(step, input_name) for step in layer]
    if len(branches) == 1:
        step = layer[0]
        return [
            dsl.par(dsl.ident(), branches[0]),
            _arr("std.assign", {"key": step.output}, step.source),
        ]
    return [
        dsl.par([dsl.ident(), *branches]),
        _arr("std.collect", {"fields": [step.output for step in layer]}, layer[0].source),
    ]


def _step_from_env(step: StepNode, input_name: str) -> Node:
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
        return _with_source(dsl.arr(step.ref), step.source)
    if step.kind is StepKind.PASSTHROUGH:
        return _with_source(dsl.ident(), step.source)
    raise AssertionError(f"unhandled step kind: {step.kind}")


def _arr(name: str, args: dict[str, Any], source: Optional[SourceSpan]) -> Node:
    return _with_source(dsl.arr(name, args), source)


def _with_source(node: Node, source: Optional[SourceSpan]) -> Node:
    node.source = source
    return node


def _seq(nodes: Iterable[Node]) -> Node:
    return dsl.seq(list(nodes))


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
