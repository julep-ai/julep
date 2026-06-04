from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar, cast

Out = TypeVar("Out")


class Result(dict[str, Any], Generic[Out]):
    """The typed result of an agent run (design §11).

    It IS the agent loop's terminal dict (so every existing dict access keeps
    working) plus typed attribute accessors. `Out` is the output type - `Any`
    for an agent edge.
    """

    @property
    def output(self) -> Out:
        """The run's output (typed `Out`; `Any` for an agent edge)."""
        return cast(Out, self.get("output"))

    @property
    def status(self) -> str:
        return str(self.get("status", ""))

    @property
    def ok(self) -> bool:
        """True iff the run finished successfully (status == 'done')."""
        return self.get("status") == "done"

    @property
    def trace(self) -> list[Any]:
        return list(self.get("trace", []))

    @property
    def cost(self) -> float:
        """USD spent (the terminal dict's 'spentUsd')."""
        return float(self.get("spentUsd", 0.0))

    @property
    def rounds(self) -> int:
        return int(self.get("rounds", 0))

    @property
    def reason(self) -> Optional[str]:
        value = self.get("reason")
        return None if value is None else str(value)

    @property
    def prod_gap(self) -> Optional[list[str]]:
        """Dev-mode would-block diagnostics, when present ('prodGap')."""
        value = self.get("prodGap")
        return None if value is None else list(value)
