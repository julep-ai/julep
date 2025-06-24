"""Local typing stub for the external ``uuid_extensions`` package.

Only the parts actually used by this code-base are declared.  We provide a
more precise return type for :func:`uuid_extensions.uuid7` so that static type
checkers (pytype / pyright) do not complain when the function is invoked with
default arguments.

The real implementation allows selecting an alternative output representation
(str / int / bytes) via the ``as_type`` keyword.  We model this behaviour with
proper ``typing.overload`` definitions – when ``as_type`` is omitted or
``None`` the return value is a ``uuid.UUID`` which is how it is used across
Julep.

Note: This stub is *only* imported by the type-checker – the actual runtime
module from the third-party package is still used.  Keeping the stub here
avoids having to sprinkle ``cast()`` calls throughout the code-base or wrap
the function in a helper.
"""

from __future__ import annotations

import datetime as _dt
import uuid as _uuid
from collections.abc import Callable
from typing import Literal, overload

__all__ = [
    "check_timing_precision",
    "time_ns",
    "uuid7",
    "uuid7str",
    "uuid_to_datetime",
]

# ---------------------------------------------------------------------------
# Public helpers mirrored from the original package
# ---------------------------------------------------------------------------

def time_ns() -> int:  # pragma: no cover – implementation lives upstream.
    """Return the current time in nanoseconds since Unix epoch."""

@overload
def uuid7(
    ns: int | None = ...,
    *,
    as_type: None = ...,
    time_func: Callable[[], int] = ...,
) -> _uuid.UUID: ...
@overload
def uuid7(
    ns: int | None = ...,
    *,
    as_type: Literal["uuid"] = ...,
    time_func: Callable[[], int] = ...,
) -> _uuid.UUID: ...
@overload
def uuid7(
    ns: int | None = ...,
    *,
    as_type: Literal["str", "hex"] = ...,
    time_func: Callable[[], int] = ...,
) -> str: ...
@overload
def uuid7(
    ns: int | None = ...,
    *,
    as_type: Literal["int"] = ...,
    time_func: Callable[[], int] = ...,
) -> int: ...
@overload
def uuid7(
    ns: int | None = ...,
    *,
    as_type: Literal["bytes"] = ...,
    time_func: Callable[[], int] = ...,
) -> bytes: ...
def uuid7(*args, **kwargs):  # type: ignore[override]
    """Runtime implementation lives in the real package – stub only."""

def uuid7str(ns: int | None = ...) -> str: ...
def check_timing_precision(timing_func: Callable[[], int] | None = ...) -> str: ...
def uuid_to_datetime(value: _uuid.UUID) -> _dt.datetime: ...
