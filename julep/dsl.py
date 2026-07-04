"""The authoring DSL (blueprint §3.1).

Thin sugar that emits core IR :class:`~julep.ir.Node` trees. Every
combinator returns a ``Node``; nothing here does IO. Node ids are provisional
(a readable per-process counter) and get reassigned to deterministic paths by
:func:`julep.freeze.freeze`, so reusing a sub-flow in two places is
fine — the freeze round-trip unshares it.

Shapes are *derived*, never declared: ``par`` is Dataflow because ``Op.PAR`` is,
``iter_up_to`` is Feedback because ``Op.ITER_UP_TO`` is, and so on. The DSL can't lie
about cost.
"""

from __future__ import annotations

import inspect
import itertools
import os
from typing import Any, Optional, Sequence, Union

from .ir import (
    Ann,
    CallStep,
    ContextPolicy,
    McpTool,
    NativeTool,
    Node,
    SourceSpan,
    SubContract,
    SubStep,
    ThinkStep,
    ToolRef,
)
from .kinds import ContextScope, Op, Shape, SummaryPolicy

_counter = itertools.count()
_PACKAGE_ROOT = os.path.dirname(__file__)
_SOURCE_CAPTURE = os.environ.get("COMPOSABLE_AGENTS_SOURCE_CAPTURE") == "1"


def _nid(tag: str) -> str:
    return f"{tag}#{next(_counter)}"


def set_source_capture(enabled: bool) -> None:
    global _SOURCE_CAPTURE
    _SOURCE_CAPTURE = enabled


def source_capture_enabled() -> bool:
    return _SOURCE_CAPTURE


def _capture_source() -> Optional[SourceSpan]:
    if not source_capture_enabled():
        return None
    try:
        for frame_info in inspect.stack(context=1):
            package_root = os.path.abspath(_PACKAGE_ROOT)
            filename = os.path.abspath(frame_info.filename)
            if os.path.commonpath([package_root, filename]) != package_root:
                text = frame_info.code_context[0].strip() if frame_info.code_context else None
                return SourceSpan(
                    file=frame_info.filename,
                    line=frame_info.lineno,
                    function=frame_info.function,
                    text=text,
                )
    except Exception:
        return None
    return None


def _node(**kwargs: Any) -> Node:
    return Node(**kwargs, source=_capture_source())


CtxArg = Union[ContextPolicy, ContextScope, None]


def _ctx(c: CtxArg) -> Optional[ContextPolicy]:
    if c is None:
        return None
    if isinstance(c, ContextScope):
        return ContextPolicy(scope=c)
    return c


# --------------------------------------------------------------------------- #
# Leaves.
# --------------------------------------------------------------------------- #
def native(name: str) -> NativeTool:
    """Reference a native HTTP tool we own."""
    return NativeTool(name)


def mcp(server: str, tool: str) -> McpTool:
    """Reference a tool from an MCP server."""
    return McpTool(server=server, tool=tool)


def call(ref_or_name: str | ToolRef, *, ctx: CtxArg = None, ann: Optional[Ann] = None) -> Node:
    """Invoke a tool reference.

    A bare string is shorthand for :func:`native`; pass :func:`mcp` for MCP
    tools.
    """
    ref = native(ref_or_name) if isinstance(ref_or_name, str) else ref_or_name
    if not isinstance(ref, (NativeTool, McpTool)):
        raise TypeError("call() expects a ToolRef or native tool name")
    tag = "mcp" if isinstance(ref, McpTool) else "call"
    return _node(op=Op.PRIM, id=_nid(tag), ann=ann,
                 step=CallStep(tool=ref, ctx=_ctx(ctx)))


def think(reasoner: str, *, ctx: CtxArg = None, ann: Optional[Ann] = None) -> Node:
    """A single model call against a named reasoner config."""
    return _node(op=Op.PRIM, id=_nid("think"), ann=ann,
                 step=ThinkStep(reasoner=reasoner, ctx=_ctx(ctx)))


def reasoner_from_ctx(path: str, *, ctx: CtxArg = None) -> Node:
    """A think leaf backed by a dotctx prompt directory.

    The reasoner id is the dotctx path; the full settings.yaml -> Reasoner mapping is
    done by :mod:`julep.dotctx` at deploy. Context reading is always
    explicit, never ambient.
    """
    return think(path, ctx=_ctx(ctx) or ContextPolicy(scope=ContextScope.LOCAL))


def ident() -> Node:
    return _node(op=Op.IDENT, id=_nid("ident"))


def arr(pure_name: str, args: Optional[dict[str, Any]] = None) -> Node:
    """Lift a registered pure function into a flow leaf."""
    return _node(op=Op.ARR, id=_nid("arr"), pure=pure_name, args=args)


def sub(
    ref: str,
    contract: Optional[SubContract] = None,
    *,
    summary_policy: Optional[SummaryPolicy] = None,
) -> Node:
    """An opaque child workflow carrying its contract across the firewall."""
    if contract is None:
        contract = SubContract(Shape.PIPELINE, summary_policy)
    if summary_policy is not None and contract.summary_policy is None:
        contract = SubContract(shape=contract.shape, summary_policy=summary_policy)
    return _node(op=Op.PRIM, id=_nid("sub"), step=SubStep(ref=ref, contract=contract))


# --------------------------------------------------------------------------- #
# Structural combinators.
# --------------------------------------------------------------------------- #
def _as_flows(flows: tuple[Node | Sequence[Node], ...]) -> tuple[Node, ...]:
    if len(flows) == 1 and isinstance(flows[0], Sequence):
        return tuple(flows[0])
    return flows  # type: ignore[return-value]


def _binary(op: Op, tag: str, flows: tuple[Node, ...]) -> Node:
    if not flows:
        raise ValueError(f"{tag} needs at least one flow")
    if len(flows) == 1:
        return flows[0]
    acc = flows[0]
    for nxt in flows[1:]:
        acc = _node(op=op, id=_nid(tag), left=acc, right=nxt)
    return acc


def seq(*flows: Node | Sequence[Node]) -> Node:
    """Run flows in sequence, threading output -> input (Pipeline)."""
    return _binary(Op.SEQ, "seq", _as_flows(flows))


def par(*flows: Node | Sequence[Node]) -> Node:
    """Run flows concurrently on the same input, then merge (Dataflow)."""
    return _binary(Op.PAR, "par", _as_flows(flows))


def fanout(*flows: Node | Sequence[Node]) -> Node:
    """Fan one input out to N branches concurrently (Dataflow).

    Same IR as :func:`par`; the name documents intent (homogeneous fan-out
    vs heterogeneous join). The harness collects branch results into a list.
    """
    return _binary(Op.PAR, "par", _as_flows(flows))


def alt(
    pred: Optional[str] = None,
    if_true: Optional[Node] = None,
    if_false: Optional[Node] = None,
    *,
    select: Optional[str] = None,
    cases: Optional[dict[str, Node]] = None,
    default: Optional[Node] = None,
) -> Node:
    """Choose a branch by a registered pure predicate or classifier (Branching).

    ``pred(input)`` truthy -> ``if_true``, else ``if_false``. For a model-judged
    branch, put a ``think`` before an ``alt`` over its (pure) verdict so the
    workflow stays deterministic.
    """
    if cases is not None or default is not None:
        if pred is not None or if_true is not None or if_false is not None:
            raise ValueError("alt switch uses select/cases/default, not binary branches")
        if select is None:
            raise ValueError("alt switch needs a selector")
        if not cases:
            raise ValueError("alt switch needs at least one case")
        return _node(
            op=Op.ALT,
            id=_nid("alt"),
            select=select,
            cases=dict(cases),
            default=default,
        )

    pred = pred or select
    if pred is None:
        raise ValueError("alt needs a predicate")
    if if_true is None or if_false is None:
        raise ValueError("alt binary mode needs if_true and if_false")
    return _node(op=Op.ALT, id=_nid("alt"), pure=pred, left=if_true, right=if_false)


def each(body: Node, *, max_parallel: Optional[int] = None, reducer: Optional[str] = None) -> Node:
    """Run ``body`` once per element of the input list, concurrently (Dataflow).

    The dynamic counterpart of :func:`par`: ``par`` fans one value out to a
    *static* set of branches, ``each`` fans a *runtime list* out to one body per
    element and collects the outputs in input order (``[x] -> [y]``). The input
    must be a list at runtime; anything else is an error, never coerced.

    ``max_parallel`` bounds in-flight bodies for this node (evaluated in waves
    of that size); the engine-wide ``ExecutionPolicy.max_parallel`` still
    applies underneath. ``reducer`` names a registered pure folded over the
    collected list (``[y] -> z``), e.g. to flatten or aggregate.

    A model-generated (staged) plan may not contain ``each``: its cost scales
    with runtime data, so §8 plan admission cannot bound it.
    """
    if max_parallel is not None and max_parallel < 1:
        raise ValueError("each max_parallel must be >= 1")
    return _node(op=Op.EACH, id=_nid("each"), body=body, bound=max_parallel, pure=reducer)


def iter_up_to(max: int, body: Node, *, until: Optional[str] = None) -> Node:
    """Iterate ``body`` up to ``max`` times (Feedback).

    ``until`` names a registered convergence predicate; when it returns truthy
    the loop stops early. Omit it to always run ``max`` rounds.
    """
    return _node(op=Op.ITER_UP_TO, id=_nid("iter"), bound=max, body=body, pure=until)


def stage(planner: str) -> Node:
    """Stage a model-generated plan (Staged).

    ``planner`` is a reasoner/dotctx that emits a Plan. At runtime the plan is
    compiled, validated (<= Feedback, granted tools only) and run as ordinary IR.
    """
    return _node(op=Op.EVAL_PLAN, id=_nid("stage"), controller=planner)


def app(
    controller: str,
    *,
    tools: Optional[Any] = None,
    subflows: Optional[Any] = None,
    budget: Optional[Any] = None,
    max_rounds: Optional[int] = None,
    ctx: CtxArg = None,
    summarizer: Optional[str] = None,
    round_note: Optional[str] = None,
    native_tools: bool = False,
    require_tool_call: bool = False,
    subflow_queues: Optional[dict[str, str]] = None,
) -> Node:
    """Open-ended controller loop (Agent — the top of the lattice; use sparingly).

    ``ctx`` declares how much session context the controller sees each round
    (docs/design/agent-transcripts.md): ``WHOLE_SESSION``/``SUMMARY`` require
    ``ctx.max_tokens``, and ``SUMMARY`` additionally requires ``summarizer``
    (a named reasoner) — both are deploy-time blocking diagnostics, never implicit
    defaults. Omitting ``ctx`` keeps today's LOCAL behavior and wire format.
    ``round_note`` names a registered pure ``(ctx) -> Optional[str]`` computed
    fresh each round from loop state (``{'round','maxRounds','spent','callCounts'}``)
    and injected as the controller payload's ``note``; unregistered names are
    deploy-time ``UNKNOWN_PURE`` diagnostics. ``std.rounds_remaining_note``
    reproduces mem-mcp's ``[REMAINING ROUNDS: N]``.
    """
    return _node(
        op=Op.APP,
        id=_nid("app"),
        controller=controller,
        tools=tools,
        subflows=subflows,
        budget=budget,
        max_rounds=max_rounds,
        ctx=_ctx(ctx),
        summarizer=summarizer,
        round_note=round_note,
        native_tools=native_tools or None,
        require_tool_call=require_tool_call or None,
        subflow_queues=subflow_queues,
    )


# --------------------------------------------------------------------------- #
# Contract helper for Sub.
# --------------------------------------------------------------------------- #
class Contract:
    """Construct :class:`SubContract` values for ``sub``."""

    @staticmethod
    def of(shape: Shape, summary_policy: Optional[SummaryPolicy] = None) -> SubContract:
        return SubContract(shape=shape, summary_policy=summary_policy)

    @staticmethod
    def pipeline(summary_policy: Optional[SummaryPolicy] = None) -> SubContract:
        return SubContract(Shape.PIPELINE, summary_policy)

    @staticmethod
    def dataflow(summary_policy: Optional[SummaryPolicy] = None) -> SubContract:
        return SubContract(Shape.DATAFLOW, summary_policy)

    @staticmethod
    def feedback(summary_policy: Optional[SummaryPolicy] = None) -> SubContract:
        return SubContract(Shape.FEEDBACK, summary_policy)

    @staticmethod
    def staged(summary_policy: Optional[SummaryPolicy] = None) -> SubContract:
        return SubContract(Shape.STAGED, summary_policy)

    @staticmethod
    def agent(summary_policy: Optional[SummaryPolicy] = SummaryPolicy.RESULT_ONLY) -> SubContract:
        return SubContract(Shape.AGENT, summary_policy)
