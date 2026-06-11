"""Define-by-construction ``@flow`` frontend.

``@flow`` is the primary authoring surface for composable-agents. The decorator
runs the user's function once at definition time with :class:`Handle` values:
registered tools, registered pures, ``think(...)``, ``cond(...)``,
``switch(...)``, ``each(...)``, and ``reschedule(...)`` append graph steps rather
than executing runtime work. Handles support only the deterministic dataflow
operators ``h1 | h2`` (``std.merge``) and ``h["key"]`` (``std.pluck``). Lowering
always goes through :mod:`composable_agents.dag` and the compiler; this frontend
does not emit wire-format IR directly.

Branch arms receive the branch subject by name: the remaining item parameter of
a ``cond``/``switch`` arm must match the subject Handle label. Other enclosing
values must be supplied as keyword captures with matching variable names.
``each`` bodies are different: the item parameter is positional and may be named
independently from the list-valued items Handle.

Determinism contract: every callable used on a Handle must be registered by its
raw function source (``@tool`` or ``@pure``), every captured constant must be
canonical JSON, and secret-shaped config must stay in environment-backed tools
rather than the frozen flow artifact. Static binding is capture-by-value for
JSON and capture-by-handle only from the enclosing graph. Names are
single-assignment graph fields derived from whole-function AST source when
available, with ``name=`` as the explicit escape hatch and deterministic
fallback names for REPL/``exec`` contexts.

JSON constant kwargs on registered pures become ``arr`` static args and execute
as ``fn(value, **kwargs)`` at runtime (SPEC §4.4). JSON constant kwargs on tools
and ``think`` lower to a ``std.bind`` const-merge into the flowing record before
the call.

Define-time diagnostics are part of the API: truthiness and iteration on
Handles point to ``cond``/``each``; unregistered callables point to
``@pure``/``@tool`` registration; unsaturated flows point to applying them or
passing them directly to ``each``; rebinding, unused parameters, foreign-scope
handle captures, invalid/secret/oversized captures, tuple-unpacking Handle
targets, and non-Handle returns all include a :class:`SourceSpan` when source is
available. Unused ``@flow`` parameters are blocking errors, not warnings,
because they otherwise freeze a misleading API and make closure conversion
ambiguous.
"""

from __future__ import annotations

import ast
import inspect
import math
import re
import textwrap
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from types import FrameType
from typing import TYPE_CHECKING, Any, Optional, TypeVar, overload

from . import dag, dsl
from .typed import FlowLike
from .ir import SLEEP_TOOL, Ann, CallStep, NativeTool, Node, SourceSpan, canonical_json
from .validate import SECRET_KEY_RE

if TYPE_CHECKING:
    from .dotctx import Brain


In = TypeVar("In")
Out = TypeVar("Out")
_JSON = (str, int, float, bool, type(None), list, dict)
_RESERVED_STEP_KWARGS = {"name", "retries", "retry_interval_s", "backoff_rate", "timeout_s"}
_CONTROL_HELPERS = {"cond", "switch", "each", "reschedule"}
_RESERVED_ENV_NAME_RE = re.compile(r"__.*__")
_CTX_STACK: list["_BuildContext"] = []


class DefineError(dag.GraphDefinitionError):
    """Actionable define-time error raised by the ``@flow`` frontend."""


@dataclass(frozen=True)
class _CallSite:
    output_name: Optional[str]
    span: SourceSpan
    callee: Optional[str] = None


class _SourceMap:
    def __init__(self, fn: Callable[..., Any]) -> None:
        self.fn = fn
        self.filename = inspect.getsourcefile(fn) or inspect.getfile(fn)
        self.function = fn.__name__
        self._by_line: dict[int, list[_CallSite]] = defaultdict(list)
        self._source_lines: list[str] = []
        self._base_line = 1
        self._fallback_counts: dict[str, int] = defaultdict(int)
        self._tree: Optional[ast.FunctionDef | ast.AsyncFunctionDef] = None
        self._globals = fn.__globals__
        self._closure = inspect.getclosurevars(fn)
        self._param_lines: dict[str, int] = {}
        self._return_lines: list[int] = []
        self._parse()

    def _parse(self) -> None:
        try:
            source, start = inspect.getsourcelines(self.fn)
        except (OSError, TypeError):
            return
        self._source_lines = source
        self._base_line = start
        try:
            module = ast.parse(textwrap.dedent("".join(source)))
        except SyntaxError:
            return
        functions = [node for node in module.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if not functions:
            return
        self._tree = functions[0]
        for arg in self._tree.args.args:
            self._param_lines[arg.arg] = self._actual_line(arg)
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Return):
                self._return_lines.append(self._actual_line(node))
            if not isinstance(node, ast.Assign):
                continue
            target_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if len(target_names) != 1:
                continue
            for child, site in self._expr_call_sites(node.value, target_names[0], is_outer=True):
                self._by_line[self._actual_line(child)].append(site)

    def _expr_call_sites(
        self,
        node: ast.AST,
        target_name: str,
        *,
        is_outer: bool,
    ) -> list[tuple[ast.AST, _CallSite]]:
        output_name = target_name if is_outer else None
        if isinstance(node, ast.Call):
            sites: list[tuple[ast.AST, _CallSite]] = []
            for arg in node.args:
                sites.extend(self._expr_call_sites(arg, target_name, is_outer=False))
            for keyword in node.keywords:
                if keyword.value is not None:
                    sites.extend(self._expr_call_sites(keyword.value, target_name, is_outer=False))
            sites.append((node, _CallSite(output_name, self._span(node), self._call_name(node))))
            return sites
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            sites = self._expr_call_sites(node.left, target_name, is_outer=False)
            sites.extend(self._expr_call_sites(node.right, target_name, is_outer=False))
            sites.append((node, _CallSite(output_name, self._span(node), "std.merge")))
            return sites
        if isinstance(node, ast.Subscript):
            sites = self._expr_call_sites(node.value, target_name, is_outer=False)
            sites.append((node, _CallSite(output_name, self._span(node), "std.pluck")))
            return sites

        sites = []
        for child in ast.iter_child_nodes(node):
            sites.extend(self._expr_call_sites(child, target_name, is_outer=False))
        return sites

    def validate_plain_handle_calls(self, param_names: list[str]) -> None:
        if self._tree is None:
            return
        handle_names = set(param_names)
        for stmt in self._tree.body:
            if isinstance(stmt, ast.Assign) and any(isinstance(target, (ast.Tuple, ast.List)) for target in stmt.targets):
                if self._expr_produces_handle(stmt.value, handle_names):
                    raise DefineError(
                        "tuple-unpacking targets cannot bind Handle results"
                        f"{_source_suffix(self._span(stmt))}; "
                        "assign the step to one name or pass name=... to the step"
                    )
            for call in [node for node in ast.walk(stmt) if isinstance(node, ast.Call)]:
                if self._call_uses_handle(call, handle_names) and not self._is_allowed_call(call):
                    name = self._call_name(call)
                    raise DefineError(
                        "unregistered callable "
                        f"{name!r}{_source_suffix(self._span(call))}; "
                        "decorate it with @pure or @tool, or call think(...) for a brain step; "
                        "registered Tool, Pure, and @flow functions are the only direct Handle callables"
                    )
            if isinstance(stmt, ast.Assign):
                target_names = [target.id for target in stmt.targets if isinstance(target, ast.Name)]
                if target_names and self._expr_produces_handle(stmt.value, handle_names):
                    handle_names.add(target_names[0])

    def _call_uses_handle(self, call: ast.Call, handle_names: set[str]) -> bool:
        return any(isinstance(node, ast.Name) and node.id in handle_names for node in ast.walk(call))

    def _expr_produces_handle(self, expr: ast.AST, handle_names: set[str]) -> bool:
        if isinstance(expr, ast.Name):
            return expr.id in handle_names
        if isinstance(expr, (ast.Call, ast.BinOp, ast.Subscript)):
            return any(isinstance(node, ast.Name) and node.id in handle_names for node in ast.walk(expr))
        return False

    def _is_allowed_call(self, call: ast.Call) -> bool:
        target = self._resolve_call_target(call)
        if target is None:
            return False
        return _is_control_helper(target) or _is_tool(target) or _is_pure(target) or isinstance(target, FlowDef)

    def _resolve_call_target(self, call: ast.Call) -> Any:
        return self._resolve_expr(call.func)

    def _resolve_expr(self, expr: ast.AST) -> Any:
        if isinstance(expr, ast.Name):
            name = expr.id
            if name in self._closure.nonlocals:
                return self._closure.nonlocals[name]
            if name in self._closure.globals:
                return self._closure.globals[name]
            return self._globals.get(name)
        if isinstance(expr, ast.Attribute):
            parent = self._resolve_expr(expr.value)
            if parent is None:
                return None
            return getattr(parent, expr.attr, None)
        return None

    def _call_name(self, call: ast.Call) -> str:
        return ast.unparse(call.func)

    def return_span(self) -> SourceSpan:
        if self._return_lines:
            return self._span_for_line(self._return_lines[-1])
        if self._source_lines:
            return self._span_for_line(self._base_line + len(self._source_lines) - 1)
        return self._span_for_line(1)

    def param_span(self, name: str) -> SourceSpan:
        return self._span_for_line(self._param_lines.get(name, self._base_line))

    def current_span(self, fallback: Optional[SourceSpan]) -> Optional[SourceSpan]:
        frame = _CTX_STACK[-1].frame() if _CTX_STACK else None
        if frame is not None:
            return self._span_for_line(frame.f_lineno)
        return fallback

    def call_site(self, frame: Optional[FrameType], ref: str) -> _CallSite:
        if frame is not None:
            sites = self._by_line.get(frame.f_lineno)
            if sites:
                for index, site in enumerate(sites):
                    if _site_matches_ref(site, ref):
                        return sites.pop(index)
                return sites.pop(0)
            return _CallSite(None, self._span_for_line(frame.f_lineno))
        self._fallback_counts[ref] += 1
        return _CallSite(None, SourceSpan(file=self.filename, line=1, function=self.function))

    def fallback_name(self, ref: str) -> str:
        clean = re.sub(r"[^0-9A-Za-z_]+", "_", ref).strip("_") or "ref"
        self._fallback_counts[clean] += 1
        return f"{clean}_{self._fallback_counts[clean]}"

    def _span(self, node: ast.AST) -> SourceSpan:
        return self._span_for_line(self._actual_line(node))

    def _span_for_line(self, line: int) -> SourceSpan:
        text = None
        index = line - self._base_line
        if 0 <= index < len(self._source_lines):
            text = self._source_lines[index].strip()
        return SourceSpan(file=self.filename, line=line, function=self.function, text=text)

    def _actual_line(self, node: ast.AST) -> int:
        return self._base_line + getattr(node, "lineno", 1) - 1


class _BuildContext:
    def __init__(self, flow_def: "FlowDef", source_map: _SourceMap) -> None:
        self.flow_def = flow_def
        self.source_map = source_map
        self.graph = dag.Graph(input_name=flow_def.param_names[0] if flow_def.param_names else "__input__")
        self.bound_names = set(flow_def.param_names)

    def frame(self) -> Optional[FrameType]:
        frame = inspect.currentframe()
        while frame is not None:
            if (
                frame.f_code.co_filename == self.source_map.filename
                and frame.f_code.co_name == self.source_map.function
            ):
                return frame
            frame = frame.f_back
        return None

    def output_name(self, ref: str, explicit: Optional[str], site: _CallSite) -> str:
        span = site.span
        name = explicit or site.output_name
        if name is None:
            name = self.source_map.fallback_name(ref)
        if _RESERVED_ENV_NAME_RE.fullmatch(name):
            raise DefineError(
                f"step output name {name!r} is reserved{_source_suffix(span)}; "
                "__*__ names are internal env keys"
            )
        if name in self.bound_names:
            raise DefineError(
                f"step output name {name!r} is already bound{_source_suffix(span)}; "
                "choose a new Python variable name or pass name=..."
            )
        self.bound_names.add(name)
        return name

    def validate_current_handle(self, handle: "Handle", span: Optional[SourceSpan]) -> None:
        if handle.graph is self.graph:
            return
        raise DefineError(
            f"foreign-scope handle {handle.label!r} captured in @flow {self.flow_def.name!r}"
            f"{_source_suffix(span)}; "
            "pass it as a parameter or bind it through each(body, items, ...) closure conversion"
        )


class Handle:
    """Authoring-time data handle produced by ``@flow`` step applications."""

    __slots__ = ("label", "graph", "source")

    def __init__(self, label: str, graph: Optional[dag.Graph], source: Optional[SourceSpan]) -> None:
        self.label = label
        self.graph = graph
        self.source = source

    @classmethod
    def synthetic(cls, label: str) -> "Handle":
        return cls(label, None, SourceSpan(file="<synthetic>", line=1, function=None))

    def __or__(self, other: object) -> "Handle":
        ctx = _current_context()
        site = _call_site(ctx, "std.merge")
        span = site.span
        ctx.validate_current_handle(self, span)
        rhs = _ensure_handle(other, span)
        ctx.validate_current_handle(rhs, span)
        output = ctx.output_name("merge", None, site)
        ctx.graph.add_step(
            dag.StepKind.PURE,
            "std.merge",
            inputs=[self.label, rhs.label],
            output=output,
            source=span,
        )
        return Handle(output, ctx.graph, span)

    def __getitem__(self, key: str) -> "Handle":
        ctx = _current_context()
        site = _call_site(ctx, "std.pluck")
        span = site.span
        ctx.validate_current_handle(self, span)
        output = ctx.output_name(str(key), None, site)
        ctx.graph.add_step(
            dag.StepKind.PURE,
            "std.pluck",
            inputs=_single_input(self, ctx.graph.input_name),
            output=output,
            source=span,
            args={"key": str(key)},
        )
        return Handle(output, ctx.graph, span)

    def __getattr__(self, name: str) -> object:
        raise AttributeError(
            f"Handle attribute access is not runtime data{_source_suffix(self.source)}; "
            f"got {self.label}.{name}. Use {self.label}[{name!r}] for std.pluck."
        )

    def __bool__(self) -> bool:
        source = _active_source(self.source)
        suffix = _source_suffix(source)
        raise TypeError(
            f"Handle truthiness is not runtime data{suffix}; "
            "use cond(pred, input, then=..., orelse=...) instead."
        )

    def __iter__(self) -> object:
        source = _active_source(self.source)
        suffix = _source_suffix(source)
        raise TypeError(
            f"Handle iteration is not runtime data{suffix}; "
            "use each(body, items, max_parallel=..., reducer=...) instead."
        )

    def __eq__(self, other: object) -> bool:
        source = _active_source(self.source)
        suffix = _source_suffix(source)
        raise DefineError(
            f"Handle equality comparison is not runtime data{suffix}; "
            "use cond(pred, input, then=..., orelse=...) instead."
        )

    def __ne__(self, other: object) -> bool:
        source = _active_source(self.source)
        suffix = _source_suffix(source)
        raise DefineError(
            f"Handle equality comparison is not runtime data{suffix}; "
            "use cond(pred, input, then=..., orelse=...) instead."
        )

    __hash__ = object.__hash__

    def __repr__(self) -> str:
        return f"Handle({self.label})"


class FlowDef(FlowLike[Any, Any]):
    """A decorated ``@flow`` function lowered through :mod:`dag`."""

    __slots__ = ("fn", "name", "param_names", "graph", "_source_map")

    def __init__(self, fn: Callable[..., Any]) -> None:
        self.fn = fn
        self.name = fn.__name__
        signature = inspect.signature(fn)
        self.param_names = list(signature.parameters)
        if not self.param_names:
            raise DefineError("@flow functions need at least one parameter")
        self._source_map = _SourceMap(fn)
        self._source_map.validate_plain_handle_calls(self.param_names)
        ctx = _BuildContext(self, self._source_map)
        self.graph = ctx.graph
        handles = [Handle(name, self.graph, self._source_map._span_for_line(1)) for name in self.param_names]
        _CTX_STACK.append(ctx)
        try:
            result = fn(*handles)
        finally:
            _CTX_STACK.pop()
        if isinstance(result, BoundFlow):
            span = self._source_map.return_span()
            raise DefineError(
                "unsaturated @flow application cannot be returned as runtime data"
                f"{_source_suffix(span)}; "
                "apply it to a Handle or pass it directly to each(body, items, ...)"
            )
        if not isinstance(result, Handle):
            span = self._source_map.return_span()
            raise DefineError(
                f"@flow function {self.name!r} must return a Handle"
                f"{_source_suffix(span)}; "
                "return the result of a Tool, Pure, think(...), h[key], or h1 | h2"
            )
        self._validate_used_params(result)
        if result.label == self.graph.input_name and self.graph.steps:
            raise DefineError(
                f"@flow function {self.name!r} returns its own input "
                f"{result.label!r} after authoring steps{_source_suffix(result.source)}; "
                "return a step output handle instead (e.g. the write status), or "
                "merge the input into the returned value with input | step_output"
            )
        self.graph.output_name = result.label

    def _validate_used_params(self, result: Handle) -> None:
        used: set[str] = set()
        if result.label in self.param_names:
            used.add(result.label)
        for step in self.graph.steps:
            if not step.inputs and step.kind in {
                dag.StepKind.TOOL,
                dag.StepKind.THINK,
                dag.StepKind.PURE,
                dag.StepKind.PASSTHROUGH,
            }:
                used.add(self.graph.input_name)
            for edge in step.inputs:
                used.add(edge.source)
            if step.branch_subject is not None:
                used.add(step.branch_subject)
        for name in self.param_names:
            if name not in used:
                span = self._source_map.param_span(name)
                raise DefineError(
                    f"@flow function {self.name!r} has unused parameter {name!r}"
                    f"{_source_suffix(span)}; "
                    "@flow uses single-assignment dataflow; remove the parameter or pass it to a step"
                )

    def __call__(self, *args: Any, **kwargs: Any) -> Handle | "BoundFlow":
        supplied = self._supplied(args, kwargs)
        if _CTX_STACK and all(isinstance(value, Handle) for value in supplied.values()):
            if len(supplied) == len(self.param_names):
                if len(supplied) != 1:
                    site = _call_site(_CTX_STACK[-1], self.name)
                    raise DefineError(
                        f"fully bound multi-parameter @flow cannot be inlined"
                        f"{_source_suffix(site.span)}; "
                        "merge handles (h1 | h2) into a one-parameter @flow before calling it"
                    )
                return _apply_flowdef(self, _ensure_handle(next(iter(supplied.values()))))
            if len(supplied) == 1 and len(self.param_names) == 1:
                return _apply_flowdef(self, _ensure_handle(next(iter(supplied.values()))))
            if not supplied:
                raise DefineError(
                    f"@flow subcall {self.name!r} needs a Handle argument; "
                    "pass it directly to each(...) after binding captures"
                )
            return BoundFlow.from_supplied(self, supplied)
        return BoundFlow.from_supplied(self, supplied)

    def _supplied(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        supplied: dict[str, Any] = {}
        for index, arg in enumerate(args):
            if index >= len(self.param_names):
                raise TypeError(f"flow {self.name!r} expected at most {len(self.param_names)} arguments")
            supplied[self.param_names[index]] = arg
        for key, value in kwargs.items():
            if key not in self.param_names:
                raise TypeError(f"flow {self.name!r} has no parameter {key!r}")
            if key in supplied:
                raise TypeError(f"flow {self.name!r} got multiple values for {key!r}")
            supplied[key] = value
        return supplied

    def to_ir(self) -> Node:
        if len(self.param_names) != 1:
            raise DefineError(
                f"@flow {self.name!r} has {len(self.param_names)} parameters; "
                "partially apply JSON kwargs until one runtime parameter remains"
            )
        return dag.compile(self.graph)


@dataclass(frozen=True)
class BoundFlow(FlowLike[Any, Any]):
    flow: FlowDef
    bound_args: dict[str, Any]

    @classmethod
    def from_supplied(cls, flow_def: FlowDef, supplied: dict[str, Any]) -> "BoundFlow":
        for name, value in supplied.items():
            if isinstance(value, Handle):
                continue
            _validate_json_value(name, value)
        return cls(flow_def, {name: supplied[name] for name in flow_def.param_names if name in supplied})

    @property
    def remaining_param_names(self) -> list[str]:
        return [name for name in self.flow.param_names if name not in self.bound_args]

    def to_ir(self) -> Node:
        remaining = self.remaining_param_names
        if len(remaining) != 1:
            raise DefineError(
                f"bound @flow {self.flow.name!r} must leave exactly one runtime parameter; "
                f"remaining={remaining!r}"
            )
        fields: dict[str, Any] = {remaining[0]: {"input": True}}
        for name in self.flow.param_names:
            if name in self.bound_args:
                fields[name] = {"const": self.bound_args[name]}
        return dsl.seq(
            dsl.arr("std.pack", {"fields": fields}),
            dag.compile_env(self.flow.graph, self.flow.param_names),
        )


def flow(fn: Callable[..., Any]) -> FlowDef:
    """Decorate a Python function into a define-by-construction flow."""
    return FlowDef(fn)


@overload
def think(brain_or_name: str | Brain, value: None = None, /, **kwargs: Any) -> Node: ...


@overload
def think(brain_or_name: str | Brain, value: Handle, /, **kwargs: Any) -> Handle: ...


def think(brain_or_name: str | Brain, value: Optional[Handle] = None, /, **kwargs: Any) -> Node | Handle:
    """Dispatch to ``dsl.think(name)`` or append a brain step inside ``@flow``."""
    name = _brain_name(brain_or_name)
    if value is None:
        return dsl.think(name, **kwargs)
    handle = _ensure_handle(value)
    return _append_step(dag.StepKind.THINK, name, handle, target=None, **kwargs)


def cond(
    pred: str | Any,
    subject: Handle,
    *,
    then: FlowDef | BoundFlow,
    orelse: FlowDef | BoundFlow,
) -> Handle:
    """Branch on ``pred(subject)`` while lowering through DAG env branches.

    DAG branch predicates receive the pruned env record. The frontend bridges
    authored subject-shaped predicates by evaluating ``pred`` on ``subject``
    immediately before ``alt`` and storing the boolean in the internal
    ``__branch__`` env field consumed by ``std.branch_predicate``. Users do not
    need to author env-aware predicates.

    Arm item parameters bind the branch subject by name, so each arm's remaining
    runtime parameter must equal ``subject.label``. Bind other enclosing values
    as keyword captures.
    """
    ctx = _current_context()
    site = _call_site(ctx, "cond")
    span = site.span
    handle = _ensure_handle(subject, span)
    ctx.validate_current_handle(handle, span)
    pred_name = _registered_pure_name(pred, "cond predicate", span)
    then_graph, _ = _flow_graph_and_captures(
        then,
        "cond then arm",
        span,
        allow_consts=False,
        subject_label=handle.label,
    )
    else_graph, _ = _flow_graph_and_captures(
        orelse,
        "cond orelse arm",
        span,
        allow_consts=False,
        subject_label=handle.label,
    )
    output = ctx.output_name("cond", None, site)
    ctx.graph.add_cond(
        pred_name,
        output=output,
        if_true=then_graph,
        if_false=else_graph,
        source=span,
        branch_subject=handle.label,
    )
    return Handle(output, ctx.graph, span)


def switch(
    selector: str | Any,
    subject: Handle,
    *,
    cases: dict[str, FlowDef | BoundFlow],
    default: FlowDef | BoundFlow | None = None,
) -> Handle:
    """Select one arm by ``selector(subject)`` without env-aware user pures.

    Like :func:`cond`, the frontend evaluates the authored subject-shaped
    selector before the low-level ``alt`` and stores the selected key in the
    internal ``__branch__`` env field consumed by ``std.branch_selector``.

    Case and default arm item parameters bind the branch subject by name, so
    each arm's remaining runtime parameter must equal ``subject.label``. Bind
    other enclosing values as keyword captures.
    """
    ctx = _current_context()
    site = _call_site(ctx, "switch")
    span = site.span
    handle = _ensure_handle(subject, span)
    ctx.validate_current_handle(handle, span)
    selector_name = _registered_pure_name(selector, "switch selector", span)
    if not cases:
        raise DefineError(
            f"switch needs at least one case{_source_suffix(span)}; "
            "pass cases={key: flow, ...} and optionally default=flow"
        )
    arm_graphs = {
        str(key): _flow_graph_and_captures(
            arm,
            f"switch case {key!r}",
            span,
            allow_consts=False,
            subject_label=handle.label,
        )[0]
        for key, arm in cases.items()
    }
    default_graph = (
        None
        if default is None
        else _flow_graph_and_captures(
            default,
            "switch default arm",
            span,
            allow_consts=False,
            subject_label=handle.label,
        )[0]
    )
    output = ctx.output_name("switch", None, site)
    ctx.graph.add_switch(
        selector_name,
        output=output,
        cases=arm_graphs,
        default=default_graph,
        source=span,
        branch_subject=handle.label,
    )
    return Handle(output, ctx.graph, span)


def each(
    body: FlowDef | BoundFlow | Node,
    items: Optional[Handle] = None,
    *,
    max_parallel: Optional[int] = None,
    reducer: str | Any | None = None,
) -> Node | Handle:
    """Frontend dynamic fan-out or the existing ``dsl.each`` outside ``@flow``."""
    if items is None or not isinstance(items, Handle):
        if isinstance(body, Node):
            reducer_name = None if reducer is None else _pure_name_unchecked(reducer)
            return dsl.each(body, max_parallel=max_parallel, reducer=reducer_name)
        source = _call_site(_CTX_STACK[-1], "each").span if _CTX_STACK else None
        raise DefineError(
            f"each(body, items, ...) needs a Handle items argument inside @flow{_source_suffix(source)}; "
            "outside @flow use dsl.each(Node, ...) or composable_agents.typed.each(FlowLike, ...)"
        )

    ctx = _current_context()
    site = _call_site(ctx, "each")
    span = site.span
    item_handle = _ensure_handle(items, span)
    ctx.validate_current_handle(item_handle, span)
    body_graph, consts = _flow_graph_and_captures(body, "each body", span, allow_consts=True)
    reducer_name = None if reducer is None else _registered_pure_name(reducer, "each reducer", span)
    output = ctx.output_name("each", None, site)
    ctx.graph.add_each(
        body_graph,
        items=item_handle.label,
        output=output,
        max_parallel=max_parallel,
        reducer=reducer_name,
        const_captures=consts,
        source=span,
    )
    return Handle(output, ctx.graph, span)


def reschedule(
    state: Handle,
    *,
    after_s: Optional[int] = None,
    after: Optional[Node] = None,
    mark: Any = None,
) -> Handle:
    """Terminal owned-continuation primitive for ``@flow`` authoring.

    Lowering reuses the existing reserved ``__sleep__`` delay hand and the
    continuation sentinel: optional dirty-mark step, sleep, then
    ``std.continue_with``. External-dispatch dirty marking is not a primitive:
    author a normal terminal dirty-mark tool/status flow and let the dispatcher
    re-enqueue dirty rows.
    """
    ctx = _current_context()
    site = _call_site(ctx, "reschedule")
    span = site.span
    current = _ensure_handle(state, span)
    ctx.validate_current_handle(current, span)
    seconds = _reschedule_seconds(after_s=after_s, after=after, source=span)
    if mark is not None:
        if not _is_tool(mark):
            raise DefineError(
                f"reschedule mark must be a registered Tool{_source_suffix(span)}; "
                "for external dispatch, end with the dirty-mark tool and return a status"
            )
        current = _append_step(dag.StepKind.TOOL, mark.name, current, target=mark)
    sleep_output = ctx.source_map.fallback_name("reschedule_sleep")
    ctx.bound_names.add(sleep_output)
    ctx.graph.add_step(
        dag.StepKind.TOOL,
        SLEEP_TOOL,
        inputs=_single_input(current, ctx.graph.input_name),
        output=sleep_output,
        ann=Ann(timeout_s=seconds),
        source=span,
    )
    current = Handle(sleep_output, ctx.graph, span)
    output = ctx.output_name("reschedule", None, site)
    ctx.graph.add_step(
        dag.StepKind.PURE,
        "std.continue_with",
        inputs=_single_input(current, ctx.graph.input_name),
        output=output,
        source=span,
    )
    return Handle(output, ctx.graph, span)


def apply_if_authoring(fn: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    """Called by Tool/Pure hooks; returns NotImplemented outside authoring."""
    if not _contains_handle(args, kwargs):
        return NotImplemented
    if not _CTX_STACK:
        raise DefineError(
            "Handle escaped its @flow definition; "
            "a tool or pure was called outside @flow authoring"
        )
    if not args or not isinstance(args[0], Handle):
        raise DefineError(
            "step application needs a Handle as the first argument; "
            "pass runtime data through @flow parameters"
        )
    handle = args[0]
    if len(args) > 1:
        raise DefineError("step application accepts one Handle plus JSON keyword constants")
    if _is_tool(fn):
        return _append_step(dag.StepKind.TOOL, fn.name, handle, target=fn, **kwargs)
    if _is_pure(fn):
        return _append_step(dag.StepKind.PURE, fn.name, handle, target=fn, **kwargs)
    if isinstance(fn, FlowDef):
        return _apply_flowdef(fn, handle)
    raise DefineError(
        "unregistered callable "
        f"{getattr(fn, '__name__', type(fn).__name__)!r}; "
        "use a registered Tool, Pure, @flow function, or think(...)"
    )


def _append_step(
    kind: dag.StepKind,
    ref: str,
    handle: Handle,
    *,
    target: Any,
    **kwargs: Any,
) -> Handle:
    ctx = _current_context()
    site = _call_site(ctx, ref)
    span = site.span
    ctx.validate_current_handle(handle, span)
    explicit_name = _pop_optional_name(kwargs)
    ann = _ann_from_kwargs(kwargs)
    consts = {key: value for key, value in kwargs.items() if not isinstance(value, Handle)}
    handle_kwargs = {key: value for key, value in kwargs.items() if isinstance(value, Handle)}
    if handle_kwargs:
        raise DefineError(
            f"step {ref!r} got Handle keyword arguments{_source_suffix(span)}; "
            "use h1 | h2 to build the flowing input"
        )
    current = handle
    if consts:
        for key, value in consts.items():
            _validate_json_value(key, value, span)
        if kind is not dag.StepKind.PURE:
            bind_output = ctx.source_map.fallback_name(f"{ref}_bind")
            ctx.bound_names.add(bind_output)
            ctx.graph.add_step(
                dag.StepKind.PURE,
                "std.bind",
                inputs=_single_input(current, ctx.graph.input_name),
                output=bind_output,
                source=span,
                args={"consts": consts},
            )
            current = Handle(bind_output, ctx.graph, span)
    output = ctx.output_name(ref, explicit_name, site)
    ctx.graph.add_step(
        kind,
        ref,
        inputs=_single_input(current, ctx.graph.input_name),
        output=output,
        contract=getattr(target, "contract", None),
        ann=ann,
        source=span,
        args=consts if kind is dag.StepKind.PURE and consts else None,
        tool=target if kind is dag.StepKind.TOOL else None,
    )
    return Handle(output, ctx.graph, span)


def _apply_flowdef(flow_def: FlowDef, handle: Handle) -> Handle:
    ctx = _current_context()
    site = _call_site(ctx, flow_def.name)
    span = site.span
    ctx.validate_current_handle(handle, span)
    output = ctx.output_name(flow_def.name, None, site)
    if not flow_def.graph.steps or flow_def.graph.output_name == flow_def.graph.input_name:
        ctx.graph.add_step(
            dag.StepKind.PASSTHROUGH,
            flow_def.name,
            inputs=_single_input(handle, ctx.graph.input_name),
            output=output,
            source=flow_def.graph.source or span,
        )
        return Handle(output, ctx.graph, span)

    _inline_flow_graph(ctx, flow_def, handle, output)
    return Handle(output, ctx.graph, span)


def _inline_flow_graph(ctx: _BuildContext, flow_def: FlowDef, handle: Handle, output: str) -> None:
    final_output = flow_def.graph.output_name
    if final_output is None:
        raise DefineError(
            f"@flow subcall {flow_def.name!r} has no return handle; "
            "return a Handle from the sub-flow before calling it inside another flow"
        )

    remap: dict[str, str] = {flow_def.graph.input_name: handle.label}
    for step in flow_def.graph.steps:
        if step.output == final_output:
            remap[step.output] = output
        else:
            remap[step.output] = _inline_output_name(ctx, output, step.output)

    for step in flow_def.graph.steps:
        _copy_step(ctx.graph, step, remap, flow_def.graph.input_name, ctx.graph.input_name)


def _inline_output_name(ctx: _BuildContext, call_output: str, original: str) -> str:
    if original not in ctx.bound_names:
        ctx.bound_names.add(original)
        return original
    base = f"{call_output}__{original}"
    candidate = base
    index = 1
    while candidate in ctx.bound_names:
        candidate = f"{base}_{index}"
        index += 1
    ctx.bound_names.add(candidate)
    return candidate


def _copy_step(
    graph: dag.Graph,
    step: dag.StepNode,
    remap: dict[str, str],
    source_input: str,
    target_input: str,
) -> None:
    output = remap[step.output]
    inputs = _remap_inputs(step, remap, source_input, target_input)
    if step.kind in {dag.StepKind.TOOL, dag.StepKind.THINK, dag.StepKind.PURE, dag.StepKind.PASSTHROUGH}:
        graph.add_step(
            step.kind,
            step.ref,
            inputs=inputs,
            output=output,
            contract=step.contract,
            ann=step.ann,
            source=step.source,
            args=None if step.args is None else dict(step.args),
        )
        return
    if step.kind is dag.StepKind.COND:
        if step.if_true is None or step.if_false is None:
            raise DefineError(f"@flow subcall branch {step.output!r} is missing an arm")
        graph.add_cond(
            step.ref,
            inputs=inputs,
            output=output,
            if_true=_copy_graph_with_external_renames(step.if_true, remap, remap_input_name=True),
            if_false=_copy_graph_with_external_renames(step.if_false, remap, remap_input_name=True),
            source=step.source,
            branch_subject=_remap_source(step.branch_subject, remap, source_input, target_input),
        )
        return
    if step.kind is dag.StepKind.SWITCH:
        if step.cases is None:
            raise DefineError(f"@flow subcall switch {step.output!r} is missing cases")
        graph.add_switch(
            step.ref,
            inputs=inputs,
            output=output,
            cases={
                key: _copy_graph_with_external_renames(arm, remap, remap_input_name=True)
                for key, arm in step.cases.items()
            },
            default=None
            if step.default is None
            else _copy_graph_with_external_renames(step.default, remap, remap_input_name=True),
            source=step.source,
            branch_subject=_remap_source(step.branch_subject, remap, source_input, target_input),
        )
        return
    if step.kind is dag.StepKind.EACH:
        if step.body is None:
            raise DefineError(f"@flow subcall each {step.output!r} is missing a body")
        if len(inputs) != 1:
            raise DefineError(f"@flow subcall each {step.output!r} needs one list input")
        graph.add_each(
            _copy_graph_with_external_renames(
                step.body,
                remap,
                remap_input_name=False,
                excluded=set(step.const_captures or {}),
            ),
            items=inputs[0],
            output=output,
            max_parallel=step.max_parallel,
            reducer=step.reducer,
            const_captures=step.const_captures,
            source=step.source,
        )
        return
    raise AssertionError(f"unhandled step kind: {step.kind}")


def _copy_graph_with_external_renames(
    graph: dag.Graph,
    remap: dict[str, str],
    *,
    remap_input_name: bool,
    excluded: set[str] | None = None,
) -> dag.Graph:
    """Copy a nested graph only when external references need inline renaming."""
    shadowed = {step.output for step in graph.steps}
    excluded_names = set(excluded or ())
    effective = {
        source: target
        for source, target in remap.items()
        if source != target and source not in shadowed and source not in excluded_names
    }
    if not remap_input_name:
        effective.pop(graph.input_name, None)

    step_copies: list[dag.StepNode] = []
    nested_changed = False
    for step in graph.steps:
        copied_step, changed = _copy_step_node_with_external_renames(step, effective)
        step_copies.append(copied_step)
        nested_changed = nested_changed or changed

    direct_refs = _graph_direct_references(graph, remap_input_name=remap_input_name)
    direct_changed = any(name in effective for name in direct_refs)
    if not direct_changed and not nested_changed:
        return graph

    input_name = effective.get(graph.input_name, graph.input_name) if remap_input_name else graph.input_name
    output_name = graph.output_name
    if output_name is not None and output_name not in shadowed:
        output_name = effective.get(output_name, output_name)
    copied = dag.Graph(input_name=input_name, output_name=output_name, source=graph.source)
    for step in step_copies:
        _append_copied_step(copied, step)
    return copied


def _copy_step_node_with_external_renames(
    step: dag.StepNode,
    effective: dict[str, str],
) -> tuple[dag.StepNode, bool]:
    inputs = tuple(
        dag.InputEdge(name=edge.name, source=effective.get(edge.source, edge.source))
        for edge in step.inputs
    )
    branch_subject = None if step.branch_subject is None else effective.get(step.branch_subject, step.branch_subject)
    changed = inputs != step.inputs or branch_subject != step.branch_subject

    if_true = step.if_true
    if step.if_true is not None:
        if_true = _copy_graph_with_external_renames(step.if_true, effective, remap_input_name=True)
        changed = changed or if_true is not step.if_true

    if_false = step.if_false
    if step.if_false is not None:
        if_false = _copy_graph_with_external_renames(step.if_false, effective, remap_input_name=True)
        changed = changed or if_false is not step.if_false

    cases = step.cases
    if step.cases is not None:
        cases = {
            key: _copy_graph_with_external_renames(arm, effective, remap_input_name=True)
            for key, arm in step.cases.items()
        }
        changed = changed or any(cases[key] is not step.cases[key] for key in step.cases)

    default = step.default
    if step.default is not None:
        default = _copy_graph_with_external_renames(step.default, effective, remap_input_name=True)
        changed = changed or default is not step.default

    body = step.body
    if step.body is not None:
        body = _copy_graph_with_external_renames(
            step.body,
            effective,
            remap_input_name=False,
            excluded=set(step.const_captures or {}),
        )
        changed = changed or body is not step.body

    if not changed:
        return step, False

    return (
        dag.StepNode(
            kind=step.kind,
            ref=step.ref,
            inputs=inputs,
            output=step.output,
            contract=step.contract,
            ann=step.ann,
            source=step.source,
            args=None if step.args is None else dict(step.args),
            order=step.order,
            if_true=if_true,
            if_false=if_false,
            cases=cases,
            default=default,
            body=body,
            max_parallel=step.max_parallel,
            reducer=step.reducer,
            const_captures=None if step.const_captures is None else dict(step.const_captures),
            branch_subject=branch_subject,
        ),
        True,
    )


def _append_copied_step(graph: dag.Graph, step: dag.StepNode) -> None:
    if step.kind in {dag.StepKind.TOOL, dag.StepKind.THINK, dag.StepKind.PURE, dag.StepKind.PASSTHROUGH}:
        graph.add_step(
            step.kind,
            step.ref,
            inputs=[edge.source for edge in step.inputs],
            output=step.output,
            contract=step.contract,
            ann=step.ann,
            source=step.source,
            args=None if step.args is None else dict(step.args),
        )
        return
    if step.kind is dag.StepKind.COND:
        if step.if_true is None or step.if_false is None:
            raise DefineError(f"copied cond step {step.output!r} is missing an arm")
        graph.add_cond(
            step.ref,
            inputs=[edge.source for edge in step.inputs],
            output=step.output,
            if_true=step.if_true,
            if_false=step.if_false,
            source=step.source,
            branch_subject=step.branch_subject,
        )
        return
    if step.kind is dag.StepKind.SWITCH:
        if step.cases is None:
            raise DefineError(f"copied switch step {step.output!r} is missing cases")
        graph.add_switch(
            step.ref,
            inputs=[edge.source for edge in step.inputs],
            output=step.output,
            cases=step.cases,
            default=step.default,
            source=step.source,
            branch_subject=step.branch_subject,
        )
        return
    if step.kind is dag.StepKind.EACH:
        if step.body is None or len(step.inputs) != 1:
            raise DefineError(f"copied each step {step.output!r} is malformed")
        graph.add_each(
            step.body,
            items=step.inputs[0].source,
            output=step.output,
            max_parallel=step.max_parallel,
            reducer=step.reducer,
            const_captures=step.const_captures,
            source=step.source,
        )
        return
    raise AssertionError(f"unhandled step kind: {step.kind}")


def _graph_direct_references(graph: dag.Graph, *, remap_input_name: bool) -> set[str]:
    references: set[str] = set()
    if remap_input_name:
        references.add(graph.input_name)
    if graph.output_name is not None:
        references.add(graph.output_name)
    for step in graph.steps:
        references.update(edge.source for edge in step.inputs)
        if step.branch_subject is not None:
            references.add(step.branch_subject)
    return references


def _remap_inputs(
    step: dag.StepNode,
    remap: dict[str, str],
    source_input: str,
    target_input: str,
) -> list[str]:
    if not step.inputs:
        mapped = remap[source_input]
        return [] if mapped == target_input else [mapped]
    return [remap.get(edge.source, edge.source) for edge in step.inputs]


def _remap_source(
    source: Optional[str],
    remap: dict[str, str],
    source_input: str,
    target_input: str,
) -> Optional[str]:
    if source is None:
        return None
    if source == source_input:
        mapped = remap[source_input]
        return target_input if mapped == target_input else mapped
    return remap.get(source, source)


def _current_context() -> _BuildContext:
    if not _CTX_STACK:
        raise DefineError("@flow authoring operation used outside a flow definition")
    return _CTX_STACK[-1]


def _call_site(ctx: _BuildContext, ref: str) -> _CallSite:
    return ctx.source_map.call_site(ctx.frame(), ref)


def _single_input(handle: Handle, input_name: str) -> list[str]:
    return [] if handle.label == input_name else [handle.label]


def _ensure_handle(value: object, source: Optional[SourceSpan] = None) -> Handle:
    if isinstance(value, Handle):
        return value
    if isinstance(value, BoundFlow):
        raise DefineError(
            "unsaturated @flow application is define-time only"
            f"{_source_suffix(source)}; "
            "apply it to a Handle or pass it directly to each(body, items, ...)"
        )
    raise DefineError(
        f"expected a Handle{_source_suffix(source)}; "
        "pass runtime values through @flow parameters"
    )


def _contains_handle(args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    return any(isinstance(value, Handle) for value in args) or any(
        isinstance(value, Handle) for value in kwargs.values()
    )


def _pop_optional_name(kwargs: dict[str, Any]) -> Optional[str]:
    raw = kwargs.pop("name", None)
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise DefineError("step name= must be a string")
    return raw


def _ann_from_kwargs(kwargs: dict[str, Any]) -> Optional[Ann]:
    retries = kwargs.pop("retries", None)
    retry_interval_s = kwargs.pop("retry_interval_s", None)
    backoff_rate = kwargs.pop("backoff_rate", None)
    timeout_s = kwargs.pop("timeout_s", None)
    if retries is None and retry_interval_s is None and backoff_rate is None and timeout_s is None:
        return None
    return Ann(
        timeout_s=timeout_s,
        max_attempts=retries,
        retry_interval_s=retry_interval_s,
        backoff_rate=backoff_rate,
    )


def _registered_pure_name(value: Any, role: str, source: Optional[SourceSpan]) -> str:
    from .purity import Pure, is_registered

    if isinstance(value, Pure):
        return value.name
    if isinstance(value, str):
        if not is_registered(value):
            raise DefineError(
                f"{role} {value!r} is not a registered Pure{_source_suffix(source)}; "
                "decorate a deterministic function with @pure or pass a Pure object"
            )
        return value
    raise DefineError(
        f"{role} must be a registered Pure or pure name{_source_suffix(source)}; "
        "decorate a deterministic function with @pure or pass its registered name"
    )


def _pure_name_unchecked(value: Any) -> str:
    from .purity import Pure

    if isinstance(value, Pure):
        return value.name
    if isinstance(value, str):
        return value
    raise DefineError("reducer must be a Pure object or pure name")


def _flow_graph_and_captures(
    value: FlowDef | BoundFlow | Node,
    role: str,
    source: Optional[SourceSpan],
    *,
    allow_consts: bool,
    subject_label: Optional[str] = None,
) -> tuple[dag.Graph, dict[str, Any]]:
    if isinstance(value, FlowDef):
        if len(value.param_names) != 1:
            raise DefineError(
                f"{role} {value.name!r} must be a one-parameter @flow{_source_suffix(source)}; "
                "partially apply JSON or handle captures until one item parameter remains"
            )
        _validate_branch_item_parameter(
            role,
            value.name,
            value.param_names[0],
            subject_label,
            source,
        )
        return value.graph, {}
    if isinstance(value, BoundFlow):
        remaining = value.remaining_param_names
        if len(remaining) != 1:
            raise DefineError(
                f"{role} {value.flow.name!r} must leave exactly one runtime parameter"
                f"{_source_suffix(source)}; remaining={remaining!r}; "
                "pass a bare one-parameter @flow or bind all captures before using it"
            )
        if remaining[0] != value.flow.graph.input_name:
            raise DefineError(
                f"{role} {value.flow.name!r} leaves item parameter {remaining[0]!r}"
                f"{_source_suffix(source)}; "
                f"put the item parameter first ({value.flow.graph.input_name!r}) or wrap it "
                "in a one-parameter @flow"
            )
        _validate_branch_item_parameter(
            role,
            value.flow.name,
            remaining[0],
            subject_label,
            source,
        )
        consts: dict[str, Any] = {}
        for name, bound in value.bound_args.items():
            if isinstance(bound, Handle):
                if bound.label != name:
                    raise DefineError(
                        f"{role} captures handle {bound.label!r} for parameter {name!r}"
                        f"{_source_suffix(source)}; "
                        "use matching Python variable names or wrap the body in a one-parameter @flow"
                    )
                continue
            if not allow_consts:
                raise DefineError(
                    f"{role} has JSON capture {name!r}{_source_suffix(source)}; "
                    "wrap the arm in a one-parameter @flow or use each(...) for closure conversion"
                )
            consts[name] = bound
        return value.flow.graph, consts
    raise DefineError(
        f"{role} must be an @flow function or partially applied @flow{_source_suffix(source)}; "
        "decorate the body with @flow"
    )


def _validate_branch_item_parameter(
    role: str,
    flow_name: str,
    item_parameter: str,
    subject_label: Optional[str],
    source: Optional[SourceSpan],
) -> None:
    if subject_label is None or item_parameter == subject_label:
        return
    raise DefineError(
        f"{role} {flow_name!r} item parameter {item_parameter!r} does not match "
        f"branch subject {subject_label!r}{_source_suffix(source)}; "
        f"rename the arm's item parameter to {subject_label!r} because cond/switch "
        "arms receive the branch subject; bind other enclosing values as keyword "
        "captures with matching variable names; for an unnamed or expression subject, "
        "bind it to a Python variable or pass name=... to the producing step"
    )


def _reschedule_seconds(
    *,
    after_s: Optional[int],
    after: Optional[Node],
    source: Optional[SourceSpan],
) -> int:
    if after_s is not None and after is not None:
        raise DefineError(
            f"reschedule accepts either after_s= or after=delay(...), not both{_source_suffix(source)}"
        )
    if after_s is not None:
        if after_s < 1:
            raise DefineError(f"reschedule after_s must be >= 1{_source_suffix(source)}")
        return after_s
    if after is not None:
        if not (
            isinstance(after.step, CallStep)
            and after.step.tool == NativeTool(SLEEP_TOOL)
            and after.ann is not None
            and after.ann.timeout is not None
        ):
            raise DefineError(
                f"reschedule after= must be delay(seconds=...){_source_suffix(source)}; "
                "use after_s=seconds or after=delay(seconds=seconds)"
            )
        return int(after.ann.timeout)
    raise DefineError(
        f"reschedule needs after_s=seconds or after=delay(seconds=...){_source_suffix(source)}"
    )


def _validate_json_value(name: str, value: Any, source: Optional[SourceSpan] = None) -> None:
    if isinstance(value, Handle):
        return
    secret_path = _secret_path(name, value)
    if secret_path is not None:
        raise DefineError(
            f"bound value {secret_path!r} looks secret-shaped{_source_suffix(source)}; "
            "secrets belong in environment-backed tools or run principals, not frozen flow constants"
        )
    if not _json_value_ok(value):
        raise DefineError(
            f"bound value {name!r} must be canonical JSON{_source_suffix(source)}; "
            "use JSON primitives, lists, and dicts only"
        )
    try:
        canonical_json(value)
    except TypeError as exc:
        raise DefineError(
            f"bound value {name!r} must be canonical JSON{_source_suffix(source)}; "
            "use JSON primitives, lists, and dicts only"
        ) from exc


def _json_value_ok(value: Any) -> bool:
    if isinstance(value, dict):
        return all(isinstance(key, str) and _json_value_ok(child) for key, child in value.items())
    if isinstance(value, list):
        return all(_json_value_ok(item) for item in value)
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    return False


def _secret_path(name: str, value: Any) -> Optional[str]:
    if SECRET_KEY_RE.search(name):
        return name
    if isinstance(value, dict):
        for key, child in value.items():
            if SECRET_KEY_RE.search(str(key)):
                return f"{name}.{key}"
            found = _secret_path(f"{name}.{key}", child)
            if found is not None:
                return found
    if isinstance(value, list):
        for index, child in enumerate(value):
            found = _secret_path(f"{name}[{index}]", child)
            if found is not None:
                return found
    return None


def _active_source(fallback: Optional[SourceSpan]) -> Optional[SourceSpan]:
    if not _CTX_STACK:
        return fallback
    return _CTX_STACK[-1].source_map.current_span(fallback)


def _brain_name(value: str | Brain) -> str:
    return value if isinstance(value, str) else value.name


def _is_tool(value: Any) -> bool:
    from .agent import Tool

    return isinstance(value, Tool)


def _is_pure(value: Any) -> bool:
    from .purity import Pure

    return isinstance(value, Pure)


def _is_control_helper(value: Any) -> bool:
    return any(value is helper for helper in (think, cond, switch, each, reschedule))


def _site_matches_ref(site: _CallSite, ref: str) -> bool:
    if site.callee is None:
        return False
    if site.callee == ref:
        return True
    if ref in {"think", *_CONTROL_HELPERS}:
        return site.callee.endswith(f".{ref}")
    return False


def _source_suffix(source: Optional[SourceSpan]) -> str:
    if source is None:
        return ""
    parts = [f" at {source.file}:{source.line}"]
    if source.function:
        parts.append(f" in {source.function}")
    if source.text:
        parts.append(f": {source.text}")
    return "".join(parts)


__all__ = [
    "BoundFlow",
    "DefineError",
    "FlowDef",
    "Handle",
    "cond",
    "each",
    "flow",
    "reschedule",
    "switch",
    "think",
    "apply_if_authoring",
]
