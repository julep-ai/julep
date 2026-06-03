"""The authoring DSL (blueprint §3.1).

Thin sugar that emits core IR :class:`~composable_agents.ir.Node` trees. Every
combinator returns a ``Node``; nothing here does IO. Node ids are provisional
(a readable per-process counter) and get reassigned to deterministic paths by
:func:`composable_agents.freeze.freeze`, so reusing a sub-flow in two places is
fine — the freeze round-trip unshares it.

Shapes are *derived*, never declared: ``parallel`` is Dataflow because ``par`` is,
``critique`` is Feedback because ``iter_up_to`` is, and so on. The DSL can't lie
about cost.
"""

from __future__ import annotations

import itertools
from typing import Optional, Union

from .ir import (
    Ann,
    CallStep,
    ContextPolicy,
    McpTool,
    NativeTool,
    Node,
    SubContract,
    SubStep,
    ThinkStep,
)
from .kinds import ContextScope, Op, Shape, SummaryPolicy

_counter = itertools.count()


def _nid(tag: str) -> str:
    return f"{tag}#{next(_counter)}"


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
def call(name: str, *, ctx: CtxArg = None, ann: Optional[Ann] = None) -> Node:
    """A native HTTP hand we own."""
    return Node(op=Op.PRIM, id=_nid("call"), ann=ann,
                step=CallStep(tool=NativeTool(name), ctx=_ctx(ctx)))


def mcp_call(server: str, tool: str, *, ctx: CtxArg = None, ann: Optional[Ann] = None) -> Node:
    """A tool from an MCP server (resolved + frozen at run start)."""
    return Node(op=Op.PRIM, id=_nid("mcp"), ann=ann,
                step=CallStep(tool=McpTool(server=server, tool=tool), ctx=_ctx(ctx)))


def think(brain: str, *, ctx: CtxArg = None, ann: Optional[Ann] = None) -> Node:
    """A single model call against a named brain config."""
    return Node(op=Op.PRIM, id=_nid("think"), ann=ann,
                step=ThinkStep(brain=brain, ctx=_ctx(ctx)))


def brain_from_ctx(path: str, *, ctx: CtxArg = None) -> Node:
    """A think leaf backed by a dotctx prompt directory.

    The brain id is the dotctx path; the full settings.yaml -> Brain mapping is
    done by :mod:`composable_agents.dotctx` at deploy. Context reading is always
    explicit, never ambient.
    """
    return think(path, ctx=_ctx(ctx) or ContextPolicy(scope=ContextScope.LOCAL))


def ident() -> Node:
    return Node(op=Op.IDENT, id=_nid("ident"))


def arr(pure_name: str) -> Node:
    """Lift a registered pure function into a flow leaf."""
    return Node(op=Op.ARR, id=_nid("arr"), pure=pure_name)


def subagent(ref: str, contract: SubContract,
             *, summary_policy: Optional[SummaryPolicy] = None) -> Node:
    """An opaque child workflow carrying its contract across the firewall."""
    if summary_policy is not None and contract.summary_policy is None:
        contract = SubContract(shape=contract.shape, summary_policy=summary_policy)
    return Node(op=Op.PRIM, id=_nid("sub"), step=SubStep(ref=ref, contract=contract))


# --------------------------------------------------------------------------- #
# Structural combinators.
# --------------------------------------------------------------------------- #
def _binary(op: Op, tag: str, flows: tuple[Node, ...]) -> Node:
    if not flows:
        raise ValueError(f"{tag} needs at least one flow")
    if len(flows) == 1:
        return flows[0]
    acc = flows[0]
    for nxt in flows[1:]:
        acc = Node(op=op, id=_nid(tag), left=acc, right=nxt)
    return acc


def pipeline(*flows: Node) -> Node:
    """Run flows in sequence, threading output -> input (Pipeline)."""
    return _binary(Op.SEQ, "seq", flows)


def parallel(*flows: Node) -> Node:
    """Run flows concurrently on the same input, then merge (Dataflow)."""
    return _binary(Op.PAR, "par", flows)


def fanout(*flows: Node) -> Node:
    """Fan one input out to N branches concurrently (Dataflow).

    Same IR as :func:`parallel`; the name documents intent (homogeneous fan-out
    vs heterogeneous join). The harness collects branch results into a list.
    """
    return _binary(Op.PAR, "par", flows)


def route(pred: str, if_true: Node, if_false: Node) -> Node:
    """Choose a branch by a registered pure predicate (Branching).

    ``pred(input)`` truthy -> ``if_true``, else ``if_false``. For a model-judged
    route, put a ``think`` before a ``route`` over its (pure) verdict so the
    workflow stays deterministic.
    """
    return Node(op=Op.ALT, id=_nid("alt"), pure=pred, left=if_true, right=if_false)


def critique(bound: int, body: Node, *, until: Optional[str] = None) -> Node:
    """Iterate ``body`` up to ``bound`` times (Feedback).

    ``until`` names a registered convergence predicate; when it returns truthy
    the loop stops early. Omit it to always run ``bound`` rounds.
    """
    return Node(op=Op.ITER_UP_TO, id=_nid("iter"), bound=bound, body=body, pure=until)


def stage(planner: str) -> Node:
    """Stage a model-generated plan (Staged).

    ``planner`` is a brain/dotctx that emits a Plan. At runtime the plan is
    compiled, validated (<= Feedback, granted tools only) and run as ordinary IR.
    """
    return Node(op=Op.EVAL_PLAN, id=_nid("stage"), controller=planner)


def escalate(controller: str) -> Node:
    """Open-ended controller loop (Agent — the top of the lattice; use sparingly)."""
    return Node(op=Op.APP, id=_nid("app"), controller=controller)


# --------------------------------------------------------------------------- #
# Contract helper for Sub.
# --------------------------------------------------------------------------- #
class Contract:
    """Construct :class:`SubContract` values for ``subagent``."""

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
