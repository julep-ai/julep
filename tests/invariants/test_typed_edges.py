from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # mypy targets 3.10 (no typing.assert_type); runtime may be 3.10 too
    from typing_extensions import assert_type
else:
    try:
        from typing import assert_type
    except ImportError:  # Python 3.10: assert_type is a static-only helper; no-op at runtime

        def assert_type(val, typ, /):
            return val

from julep import dsl
from julep.agent import tool
from julep.dsl import call, native
from julep.typed import Flow
from julep.ir import Node
from julep.transforms import normalize_ids


@dataclass(frozen=True)
class Query:
    text: str


@dataclass(frozen=True)
class Priority:
    value: int


@dataclass(frozen=True)
class Result:
    summary: str


def _canonical(node: Node) -> str:
    unshared = Node.from_json(node.to_json())
    return json.dumps(
        normalize_ids(unshared).to_json(), sort_keys=True, separators=(",", ":")
    )


def assert_same_ir(typed: Flow[Any, Any], string_node: Node) -> None:
    assert _canonical(typed.to_ir()) == _canonical(string_node)


def test_tool_rshift_type_threads_and_lowers_to_seq() -> None:
    @tool
    def prioritize(query: Query) -> Priority:
        return Priority(value=len(query.text))

    @tool
    def summarize(priority: Priority) -> Result:
        return Result(summary=str(priority.value))

    composed = prioritize >> summarize

    assert_type(composed, Flow[Query, Result])
    assert_same_ir(
        composed,
        dsl.seq(call(native(prioritize.name)), call(native(summarize.name))),
    )
