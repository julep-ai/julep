from __future__ import annotations

import pytest

from composable_agents import (
    Effect,
    Idempotency,
    ToolContract,
    blocking,
    call,
    freeze,
    native,
    race,
    snapshot_from_tools,
    tool,
    validate,
)
from composable_agents.derived import check_race_admission


def test_tool_contract_mapping() -> None:
    @tool(effect="read", idempotent=True)
    def read_tool(q: str) -> int:
        return len(q)

    @tool
    def default_tool(x: str) -> int:
        return len(x)

    @tool(effect="dangerous")
    def dangerous_tool(x: str) -> str:
        return x

    assert read_tool.contract == ToolContract(Effect.READ, Idempotency.NATIVE)
    assert default_tool.contract == ToolContract(Effect.WRITE, Idempotency.NONE)
    assert dangerous_tool.contract.effect == Effect.DANGEROUS

    with pytest.raises(ValueError, match="read"):
        tool(effect="invalid")


def test_tool_schema_mapping() -> None:
    @tool(effect="read", idempotent=True)
    def web_search(q: str) -> list[str]:
        return [q]

    @tool
    def unannotated(value):  # type: ignore[no-untyped-def]
        return value

    @tool
    def int_tool(value: int) -> bool:
        return value > 0

    @tool
    def float_tool(value: float) -> float:
        return value

    assert web_search.input_schema == {"type": "string"}
    assert web_search.output_schema == {"type": "array", "items": {"type": "string"}}
    assert unannotated.input_schema == {"type": "object"}
    assert int_tool.input_schema == {"type": "integer"}
    assert int_tool.output_schema == {"type": "boolean"}
    assert float_tool.input_schema == {"type": "number"}
    assert float_tool.output_schema == {"type": "number"}


def test_tool_stays_callable() -> None:
    @tool(effect="read", idempotent=True)
    def web_search(q: str) -> list[str]:
        return [f"result:{q}"]

    assert web_search("hi") == ["result:hi"]


def test_tool_snapshot_freezes_native_and_race_validates_clean() -> None:
    @tool(effect="read", idempotent=True, name="web_search")
    def web_search(q: str) -> list[str]:
        return [q]

    @tool(effect="read", idempotent=True)
    def lookup(q: str) -> str:
        return q

    snap = snapshot_from_tools([web_search, lookup])
    frozen = freeze(call(native("web_search")), snap)
    (frozen_tool,) = frozen.manifest.values()

    assert frozen_tool.contract == web_search.contract
    assert frozen_tool.asserted is True

    race_frozen = freeze(race(call(native("web_search")), call(native("lookup"))), snap)
    assert not blocking(validate(race_frozen.flow, race_frozen.manifest))
    assert not blocking(check_race_admission(race_frozen.flow, race_frozen.manifest))


def test_tool_name_override() -> None:
    @tool(name="x")
    def original(q: str) -> str:
        return q

    assert original.name == "x"
