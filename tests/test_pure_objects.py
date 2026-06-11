from __future__ import annotations

import hashlib
import inspect

from composable_agents import Pure
from composable_agents import dsl
from composable_agents.typed import alt, as_flow, each, par
from composable_agents.ir import Node, canonical_json
from composable_agents.purity import get_pure, pure, source_hash_of
from composable_agents.transforms import normalize_ids


def _canonical_ir(node: Node) -> str:
    return canonical_json(normalize_ids(Node.from_json(node.to_json())).to_json())


def _expected_source_hash(fn: object) -> str:
    source = inspect.getsource(fn)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return f"pure:{digest}"


@pure
def p1_bare_increment(value: int) -> int:
    """Increment a value for bare pure decorator coverage."""
    return value + 1


@pure("p1.named.double")
def p1_named_double(value: int) -> int:
    """Double a value for named pure decorator coverage."""
    return value * 2


@pure("p1.route.is_positive")
def p1_route_is_positive(value: int) -> bool:
    return value > 0


@pure("p1.reduce.sum")
def p1_reduce_sum(values: list[int]) -> int:
    return sum(values)


def test_bare_pure_registers_under_function_name_and_returns_pure_object() -> None:
    assert isinstance(p1_bare_increment, Pure)
    assert p1_bare_increment.name == "p1_bare_increment"
    assert p1_bare_increment.__name__ == "p1_bare_increment"
    assert p1_bare_increment.__doc__ == "Increment a value for bare pure decorator coverage."
    assert get_pure("p1_bare_increment") is p1_bare_increment.fn


def test_named_pure_keeps_explicit_name_and_is_callable() -> None:
    assert isinstance(p1_named_double, Pure)
    assert p1_named_double.name == "p1.named.double"
    assert p1_named_double(4) == 8
    assert get_pure("p1.named.double") is p1_named_double.fn


def test_pure_to_ir_matches_arr_and_composes_like_flowlike() -> None:
    assert _canonical_ir(p1_named_double.to_ir()) == _canonical_ir(dsl.arr("p1.named.double"))

    composed = p1_bare_increment >> p1_named_double
    expected = dsl.seq(dsl.arr("p1_bare_increment"), dsl.arr("p1.named.double"))
    assert _canonical_ir(composed.to_ir()) == _canonical_ir(expected)


def test_source_hash_uses_original_function_not_pure_wrapper() -> None:
    assert get_pure("p1.named.double") is p1_named_double.fn
    assert get_pure("p1.named.double") is not p1_named_double
    assert source_hash_of("p1.named.double") == _expected_source_hash(p1_named_double.fn)


def test_typed_flow_helpers_accept_pure_objects_and_strings_match() -> None:
    true_branch = as_flow(p1_bare_increment)
    false_branch = as_flow(p1_named_double)

    pure_alt = alt(p1_route_is_positive, true_branch, false_branch)
    string_alt = alt("p1.route.is_positive", true_branch, false_branch)
    assert _canonical_ir(pure_alt.to_ir()) == _canonical_ir(string_alt.to_ir())

    pure_each = each(p1_named_double, reducer=p1_reduce_sum)
    string_each = each(p1_named_double, reducer="p1.reduce.sum")
    assert _canonical_ir(pure_each.to_ir()) == _canonical_ir(string_each.to_ir())

    pure_par = par([p1_bare_increment, p1_named_double], join=p1_reduce_sum)
    string_par = par([p1_bare_increment, p1_named_double], join="p1.reduce.sum")
    assert _canonical_ir(pure_par.to_ir()) == _canonical_ir(string_par.to_ir())
