"""Leaf enums and the shape join-semilattice.

This module is the bottom of the dependency graph: it knows nothing about
``Node``, so ``ir``, ``shapes``, ``contracts`` and the rest can all import it
without creating cycles. Everything here serializes to a plain string, which is
what keeps the JSON IR identical across the Python and TypeScript front ends.
"""

from __future__ import annotations

from enum import Enum


class Op(str, Enum):
    """Structural operators of the IR (blueprint §4)."""

    PRIM = "prim"
    IDENT = "ident"
    ARR = "arr"
    SEQ = "seq"
    PAR = "par"
    EACH = "each"
    ALT = "alt"
    ITER_UP_TO = "iter_up_to"
    EVAL_PLAN = "eval_plan"
    APP = "app"


class Shape(str, Enum):
    """Cost classes of a flow, ordered cheapest -> costliest.

    The order *is* the cost of owning the continuation: a ``Pipeline`` tools its
    continuation straight to the next step, an ``Agent`` owns an open-ended loop.
    """

    PIPELINE = "Pipeline"
    DATAFLOW = "Dataflow"
    BRANCHING = "Branching"
    FEEDBACK = "Feedback"
    STAGED = "Staged"
    AGENT = "Agent"


class EnforcementMode(str, Enum):
    """Compile-time enforcement disposition for deploy diagnostics."""

    STRICT = "strict"
    DEV = "dev"

    @classmethod
    def coerce(cls, value: "EnforcementMode | str") -> "EnforcementMode":
        if isinstance(value, cls):
            return value
        if value == "prod":
            return cls.STRICT
        return cls(value)


# Total order over Shape (cheapest first). The lattice join is "max in this order".
_SHAPE_ORDER: tuple[Shape, ...] = (
    Shape.PIPELINE,
    Shape.DATAFLOW,
    Shape.BRANCHING,
    Shape.FEEDBACK,
    Shape.STAGED,
    Shape.AGENT,
)
_SHAPE_RANK: dict[Shape, int] = {s: i for i, s in enumerate(_SHAPE_ORDER)}


def shape_rank(s: Shape) -> int:
    return _SHAPE_RANK[s]


def shape_leq(a: Shape, b: Shape) -> bool:
    """``a <= b`` in the cost order (``a`` is no costlier than ``b``)."""
    return _SHAPE_RANK[a] <= _SHAPE_RANK[b]


def shape_join(*shapes: Shape) -> Shape:
    """Least upper bound. Composition takes the join of its children."""
    if not shapes:
        return Shape.PIPELINE
    return max(shapes, key=lambda s: _SHAPE_RANK[s])


class Effect(str, Enum):
    """What a tool does to the world. Drives retry and race admission."""

    READ = "read"
    WRITE = "write"
    EXTERNAL = "external"
    DANGEROUS = "dangerous"


class Idempotency(str, Enum):
    """Whether repeating a call is safe. Drives retry policy."""

    REQUIRED = "required"      # caller guarantees an idempotency key is honored
    NATIVE = "native"          # the tool is naturally idempotent
    BEST_EFFORT = "best_effort"
    NONE = "none"              # conservative default; unsafe to blindly retry


class ContextScope(str, Enum):
    """How much session context a leaf reads. Never ambient — always explicit."""

    NONE = "none"                    # nothing but the immediate input
    LOCAL = "local"                  # this node's input only
    SUMMARY = "summary"              # a compressed summary of the session
    WHOLE_SESSION = "whole_session"  # the full transcript (serializes par edges)


class SummaryPolicy(str, Enum):
    """What a Sub returns across the Joined firewall to its parent."""

    RESULT_ONLY = "result_only"
    COMPRESSED_TRACE = "compressed_trace"
    FULL_CHILD_REF = "full_child_ref"


# Effects that may legally appear inside race / hedge / quorum (read-only).
RACE_SAFE_EFFECTS: frozenset[Effect] = frozenset({Effect.READ})
# Idempotency levels that make a non-read branch safe to race.
RACE_SAFE_IDEMPOTENCY: frozenset[Idempotency] = frozenset(
    {Idempotency.NATIVE, Idempotency.REQUIRED}
)
