from __future__ import annotations

import pytest

from julep import (
    JulepError,
    InMemoryProjection,
    ProjectionEmitter,
    arr,
    blocking,
    call,
    freeze,
    mcp,
    register_pure,
    seq,
    validate,
)
from julep.dsl import alt
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.ir import Node
from julep.kinds import Op
from conftest import read_snapshot, run


def _case_key(value):
    return value["case"]


def _outer_key(value):
    return value["outer"]


def _inner_key(value):
    return value["inner"]


def _to_a(value):
    return ("a", value["value"])


def _to_b(value):
    return ("b", value["value"])


def _default(value):
    return ("default", value["value"])


def _env(flow, *, snapshot=None, tools=None):
    fr = freeze(flow, snapshot or read_snapshot("inc", "double", "tag"))
    store = InMemoryProjection()
    return fr, InMemoryEnv(fr.manifest, ProjectionEmitter(store), tools=tools or {})


def _register_alt_switch_pures() -> None:
    register_pure("a2.case_key", _case_key)
    register_pure("a2.default_key", _case_key)
    register_pure("a2.outer_key", _outer_key)
    register_pure("a2.inner_key", _inner_key)
    register_pure("a2.to_a", _to_a)
    register_pure("a2.to_b", _to_b)
    register_pure("a2.default", _default)


def test_alt_switch_dispatches_to_matching_case():
    _register_alt_switch_pures()
    flow = alt(
        select="a2.case_key",
        cases={
            "a": arr("a2.to_a"),
            "b": arr("a2.to_b"),
        },
    )

    fr, env = _env(flow)

    assert run(interpret(fr.flow, {"case": "a", "value": 10}, env)).value == ("a", 10)
    fr2, env2 = _env(flow)
    assert run(interpret(fr2.flow, {"case": "b", "value": 20}, env2)).value == ("b", 20)


def test_alt_switch_uses_default_for_missing_key_and_raises_without_default():
    _register_alt_switch_pures()
    with_default = alt(
        select="a2.default_key",
        cases={"a": arr("a2.to_a")},
        default=arr("a2.default"),
    )
    fr, env = _env(with_default)
    assert run(interpret(fr.flow, {"case": "missing", "value": 3}, env)).value == (
        "default",
        3,
    )

    without_default = alt(select="a2.default_key", cases={"a": arr("a2.to_a")})
    fr2, env2 = _env(without_default)
    with pytest.raises(JulepError, match="alt: no case for key 'missing'"):
        run(interpret(fr2.flow, {"case": "missing", "value": 3}, env2))


def test_nested_alt_switch_freezes_validates_and_runs_calls():
    _register_alt_switch_pures()
    flow = alt(
        select="a2.outer_key",
        cases={
            "nested": seq(
                alt(
                    select="a2.inner_key",
                    cases={
                        "inc": call(mcp("srv", "inc")),
                        "double": call(mcp("srv", "double")),
                    },
                ),
                call(mcp("srv", "tag")),
            ),
        },
    )
    tools = {
        "srv/inc": lambda v: {**v, "value": v["value"] + 1},
        "srv/double": lambda v: {**v, "value": v["value"] * 2},
        "srv/tag": lambda v: ("tag", v["value"]),
    }

    fr, env = _env(flow, tools=tools)

    assert blocking(validate(fr.flow, fr.manifest)) == []
    assert run(
        interpret(fr.flow, {"outer": "nested", "inner": "inc", "value": 4}, env)
    ).value == ("tag", 5)


def test_alt_switch_json_round_trips():
    _register_alt_switch_pures()
    flow = alt(
        select="a2.case_key",
        cases={"b": arr("a2.to_b"), "a": arr("a2.to_a")},
        default=arr("a2.default"),
    )

    back = Node.from_json(flow.to_json())

    assert back.to_json() == flow.to_json()
    assert back.select == "a2.case_key"
    assert set(back.cases or {}) == {"a", "b"}
    assert back.default is not None


def test_binary_alt_json_is_unchanged():
    flow = Node(
        op=Op.ALT,
        id="alt",
        pure="is_even",
        left=Node(op=Op.IDENT, id="if_true"),
        right=Node(op=Op.IDENT, id="if_false"),
    )

    assert flow.to_json() == {
        "op": "alt",
        "id": "alt",
        "left": {"op": "ident", "id": "if_true"},
        "right": {"op": "ident", "id": "if_false"},
        "pure": "is_even",
    }
