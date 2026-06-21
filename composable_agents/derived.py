"""Derived combinators (blueprint §3.1, "sugar over the core").

Everything here lowers to the same core ops — there is no new runtime
primitive. The interesting cases are the *race family* (``race`` / ``hedge`` /
``quorum``): they emit an ordinary ``par`` tree, but every ``par`` node in the
group carries a :class:`~composable_agents.ir.Merge` marker describing the join
policy (first-success-wins, first-after-delay, m-of-n). Because the IR ``par`` is
binary, a single ``race(a, b, c)`` becomes a chain of ``par`` nodes that all
share the *same* merge kind; :func:`flatten_race_group` walks that chain to
recover the flat branch list, stopping at any child that isn't a same-kind
race-par (so a plain ``par`` nested inside a race stays one opaque branch).

The race family is the one place the framework owes a hard guarantee (§5): a
loser branch gets cancelled, so its effects must be either absent (read-only) or
safe to have happened (idempotent), and they must be *asserted* — untrusted MCP
hints don't count. :func:`check_race_admission` enforces that and is wired into
:func:`composable_agents.deploy.deploy` as a blocking gate.
"""

from __future__ import annotations

from typing import Optional, Sequence

from .contracts import ToolManifest
from .dsl import _nid, _node, think
from .ir import (
    Ann,
    CallStep,
    HUMAN_GATE_TOOL,
    Merge,
    NativeTool,
    Node,
    SLEEP_TOOL,
    SubStep,
)
from .kinds import (
    RACE_SAFE_IDEMPOTENCY,
    Effect,
    Op,
    Shape,
    shape_rank,
)
from .shapes import surface_shape
from .validate import Diagnostic

__all__ = [
    "HUMAN_GATE_TOOL",
    "SLEEP_TOOL",
    "race",
    "hedge",
    "quorum",
    "map_n",
    "map_reduce",
    "vote",
    "review",
    "human_gate",
    "delay",
    "flatten_race_group",
    "check_race_admission",
]


# --------------------------------------------------------------------------- #
# Lowering helpers.
# --------------------------------------------------------------------------- #
def _par_group(flows: Sequence[Node], merge: Merge, tag: str) -> Node:
    """Right-leaning ``par`` chain whose every node carries ``merge``.

    A single branch is returned unwrapped (a race of one is just that one). The
    uniform merge on every chain node is what makes :func:`flatten_race_group`
    able to recover the original branches regardless of fold direction.
    """
    if not flows:
        raise ValueError(f"{tag} needs at least one branch")
    if len(flows) == 1:
        return flows[0]
    acc = flows[-1]
    for nxt in reversed(flows[:-1]):
        acc = _node(op=Op.PAR, id=_nid(tag), left=nxt, right=acc, merge=merge)
    return acc


def flatten_race_group(root: Node) -> list[Node]:
    """Recover the flat branch list of a race-family ``par`` group.

    Descends only through ``par`` nodes whose merge kind matches ``root``'s; any
    other node (a plain ``par``, a different-kind race group, or a leaf) is
    returned as a single opaque branch.
    """
    if root.merge is None:
        return [root]
    kind = root.merge.kind
    out: list[Node] = []

    def rec(n: Node) -> None:
        if n.op == Op.PAR and n.merge is not None and n.merge.kind == kind:
            assert n.left is not None and n.right is not None
            rec(n.left)
            rec(n.right)
        else:
            out.append(n)

    rec(root)
    return out


# --------------------------------------------------------------------------- #
# The race family.
# --------------------------------------------------------------------------- #
def _branches(flows: tuple[Node | Sequence[Node], ...]) -> tuple[Node, ...]:
    if len(flows) == 1 and isinstance(flows[0], Sequence):
        return tuple(flows[0])
    return flows  # type: ignore[return-value]


def race(*flows: Node | Sequence[Node], reduce: Optional[str] = None) -> Node:
    """Run branches concurrently; first success wins, losers are cancelled.

    All branches must pass :func:`check_race_admission` (read-only or asserted
    idempotent calls, no sub-agents). ``reduce`` optionally names a pure applied
    to the winning result.
    """
    return _par_group(_branches(flows), Merge(kind="race", reducer=reduce), "race")


def hedge(*flows: Node | Sequence[Node], hedge_ms: int, reduce: Optional[str] = None) -> Node:
    """Race with a delay: start the first branch, launch the rest only after
    ``hedge_ms`` if it hasn't returned. Same admission rules as :func:`race`."""
    if hedge_ms < 0:
        raise ValueError("hedge hedge_ms must be >= 0")
    return _par_group(_branches(flows), Merge(kind="hedge", hedge_ms=hedge_ms, reducer=reduce), "hedge")


def quorum(*flows: Node | Sequence[Node], k: int, reduce: Optional[str] = None) -> Node:
    """Run branches concurrently; settle once ``k`` have succeeded, cancel the
    rest. Same admission rules as :func:`race`."""
    branches = _branches(flows)
    if k < 1 or k > len(branches):
        raise ValueError(f"quorum k must be in 1..{len(branches)}, got {k}")
    return _par_group(branches, Merge(kind="quorum", quorum_m=k, reducer=reduce), "quorum")


# --------------------------------------------------------------------------- #
# Non-racing fan-out helpers (ordinary "all" merge — no cancellation, so no
# admission restriction beyond what `validate` already does for `par`).
# --------------------------------------------------------------------------- #
def map_n(*flows: Node, reducer: Optional[str] = None) -> Node:
    """Run every branch concurrently and wait for all of them (Dataflow).

    Like :func:`composable_agents.dsl.par`, but attaches an explicit ``all``
    merge so an optional named ``reducer`` can fold the collected results.
    """
    return _par_group(flows, Merge(kind="all", reducer=reducer), "mapn")


def map_reduce(mappers: Sequence[Node], reduce: str) -> Node:
    """Fan out ``mappers`` concurrently, then combine results with pure ``reduce``."""
    if not mappers:
        raise ValueError("map_reduce needs at least one mapper")
    return _par_group(list(mappers), Merge(kind="all", reducer=reduce), "mapreduce")


def vote(reasoners: Sequence[str], agg: str) -> Node:
    """Ask several reasoners the same question in parallel; aggregate with pure ``agg``.

    A cheap ensemble: ``agg`` (e.g. a majority/median pure) folds the per-reasoner
    answers. Reasoners are read-only by construction, so this is race-safe, but the
    ``all`` merge waits for every vote rather than cancelling.
    """
    if not reasoners:
        raise ValueError("vote needs at least one reasoner")
    branches = [think(b) for b in reasoners]
    return _par_group(branches, Merge(kind="all", reducer=agg), "vote")


def review(main: Node, reviewer: str, k: int, *, agg: Optional[str] = None) -> Node:
    """Run ``main``, then fan its output to ``k`` independent ``reviewer`` passes.

    Lowers to ``main`` sequenced before a ``k``-way parallel of the reviewer
    reasoner. ``agg`` optionally names a pure that folds the reviews (e.g. into a
    pass/fail or a merged critique).
    """
    if k < 1:
        raise ValueError("review k must be >= 1")
    reviewers = _par_group([think(reviewer) for _ in range(k)],
                           Merge(kind="all", reducer=agg), "review")
    return _node(op=Op.SEQ, id=_nid("seq"), left=main, right=reviewers)


def human_gate(*, prompt: Optional[str] = None, timeout_s: Optional[int] = None) -> Node:
    """A leaf that blocks on a human signal, with an optional timeout.

    Emits a ``call`` to the reserved tool ``__human_gate__``; the harness turns
    it into a Temporal signal-wait instead of an HTTP call. The leaf's input is
    surfaced to the human as the prompt and the signal payload becomes its
    output. ``timeout_s`` (carried on the annotation) bounds the wait.
    """
    ann = Ann(timeout_s=timeout_s) if timeout_s is not None else None
    return _node(op=Op.PRIM, id=_nid("gate"), ann=ann,
                 step=CallStep(tool=NativeTool(HUMAN_GATE_TOOL)), prompt=prompt)


def delay(*, seconds: int) -> Node:
    """A leaf that durably pauses the flow, passing its input through unchanged.

    Emits a ``call`` to the reserved tool ``__sleep__``; each harness turns it
    into its engine's durable timer (Temporal timer / ``DBOS.sleep``) instead of
    an HTTP call. The duration rides on the annotation's timeout.
    """
    if seconds < 1:
        raise ValueError("delay seconds must be >= 1")
    return _node(op=Op.PRIM, id=_nid("delay"), ann=Ann(timeout_s=seconds),
                 step=CallStep(tool=NativeTool(SLEEP_TOOL)))


# --------------------------------------------------------------------------- #
# §5 race admission.
# --------------------------------------------------------------------------- #
def _branch_admission(branch: Node, manifest: ToolManifest) -> list[Diagnostic]:
    diags: list[Diagnostic] = []

    for d in branch.walk():
        step = d.step
        if isinstance(step, SubStep):
            diags.append(
                Diagnostic(
                    "RACE_SUB",
                    d.id,
                    "sub-agent inside a race/hedge/quorum branch: its effects are "
                    "opaque and can't be guaranteed cancellable",
                    severity="error",
                )
            )
        elif isinstance(step, CallStep):
            if step.frozen_hash is None:
                diags.append(
                    Diagnostic("RACE_UNFROZEN", d.id,
                               "call in a race branch was not frozen", severity="error")
                )
                continue
            tool = manifest.get(step.frozen_hash)
            if tool is None:
                diags.append(
                    Diagnostic("RACE_NO_MANIFEST", d.id,
                               f"race branch call {step.frozen_hash} absent from manifest",
                               severity="error")
                )
                continue
            c = tool.contract
            race_safe = c.effect == Effect.READ or c.idempotency in RACE_SAFE_IDEMPOTENCY
            if not tool.asserted:
                diags.append(
                    Diagnostic(
                        "RACE_UNASSERTED",
                        d.id,
                        f"tool {tool.hash} has an unasserted contract (defaulted from "
                        "untrusted MCP hints); assert it in the capability manifest to "
                        "race it",
                        severity="error",
                    )
                )
            elif not race_safe:
                diags.append(
                    Diagnostic(
                        "RACE_UNSAFE",
                        d.id,
                        f"tool {tool.hash} is effect={c.effect.value}/"
                        f"idempotency={c.idempotency.value}; a cancelled loser could "
                        "leave a side effect. Only read or native/required-idempotent "
                        "calls may race",
                        severity="error",
                    )
                )

    # A loser that owns a continuation (>= Feedback) can't be cancelled cleanly
    # mid-loop — surface it, but don't block: the leaf-effect rules above already
    # bound the actual side effects.
    s = surface_shape(branch)
    if shape_rank(s) >= shape_rank(Shape.FEEDBACK):
        diags.append(
            Diagnostic(
                "RACE_RICH_BRANCH",
                branch.id,
                f"race branch has shape {s.value} (>= Feedback); cancelling a loser "
                "mid-iteration may strand partial work",
                severity="warning",
            )
        )
    return diags


def check_race_admission(flow: Node, manifest: ToolManifest) -> list[Diagnostic]:
    """Diagnostics for every race/hedge/quorum group in ``flow`` (blueprint §5).

    For each group root we recover the flat branch list and check each branch:
    every ``call`` leaf must resolve to an *asserted* contract that is read-only
    or natively/required-idempotent, and no ``sub`` leaf may appear. Branches
    richer than Feedback get a (non-blocking) warning. Nested race groups inside
    a branch are checked too.
    """
    out: list[Diagnostic] = []
    seen: set[int] = set()

    def scan(n: Node, in_chain_of: Optional[str]) -> None:
        merge = n.merge
        is_race = merge is not None and n.op == Op.PAR and merge.kind in {
            "race", "hedge", "quorum"
        }
        # Group root = a race-par that is not the chain-continuation of a
        # same-kind race-par directly above it.
        if is_race and merge is not None and merge.kind != in_chain_of:
            if id(n) not in seen:
                seen.add(id(n))
                for branch in flatten_race_group(n):
                    out.extend(_branch_admission(branch, manifest))
                    # recurse into the branch to catch nested race groups
                    scan(branch, None)
            return
        # Either not a race node, or we're walking down a same-kind chain.
        next_chain = merge.kind if is_race and merge is not None else None
        for child in n.children():
            scan(child, next_chain)

    scan(flow, None)
    return out
