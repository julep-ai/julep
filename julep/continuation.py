"""Flow continuation: the chaining convention shared by every backend.

A flow signals "re-dispatch me with this input" by making its *final value*
``continue_with(next_input)``. The engine binding decides how a segment becomes
durable (Temporal: ``continue_as_new``; DBOS: a fresh workflow per segment);
this module only owns the sentinel and the generic driver. The sentinel is part
of the wire format: ``{"__continue__": <next input>}``, optionally enriched by
a backend with bookkeeping keys (which :func:`continuation_value` ignores).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from .errors import JulepError

CONTINUATION_KEY = "__continue__"


def continue_with(value: Any) -> dict[str, Any]:
    """Wrap ``value`` as a continuation: the flow ends, a new segment starts on it."""
    return {CONTINUATION_KEY: value}


def is_continuation(value: Any) -> bool:
    return isinstance(value, dict) and CONTINUATION_KEY in value


def continuation_value(value: dict[str, Any]) -> Any:
    return value[CONTINUATION_KEY]


async def run_chained(
    run_segment: Callable[[Any], Awaitable[Any]],
    input: Any,
    *,
    max_segments: int = 1000,
) -> Any:
    """Drive ``run_segment`` until it settles on a non-continuation value."""
    value = input
    for _ in range(max_segments):
        out = await run_segment(value)
        if not is_continuation(out):
            return out
        value = continuation_value(out)
    raise JulepError(
        f"flow did not settle within {max_segments} segments"
    )
