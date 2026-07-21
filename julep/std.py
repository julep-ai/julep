"""Closed standard pure family emitted by julep frontends.

These pures are registered at package import so frozen artifacts can reference a
small, wire-format-stable glue vocabulary instead of ad hoc closures.
"""

from __future__ import annotations

from typing import Any

from .registry import DEFAULT_REGISTRY


def std_merge(value: Any, *, fields: list[str] | None = None) -> dict[str, Any]:
    """Wire-format-stable std.merge; body frozen once any artifact references it.

    With no static args, ``value`` is the binary pair-input layout used by ``|``:
    ``[left, right]``. With ``fields``, ``value`` is an env record and each named
    env field is merged in list order. In both layouts, later dictionaries win.
    Deliberate behavior changes require registering a new std name.
    """
    if fields is None:
        left, right = value
        pair_merged = dict(left)
        pair_merged.update(right)
        return pair_merged

    projected: dict[str, Any] = {}
    for field in fields:
        projected.update(value[field])
    return projected


def std_pluck(value: Any, *, key: str) -> Any:
    """Wire-format-stable std.pluck; body frozen once any artifact references it.

    Projects one key from the flowing record. Deliberate behavior changes
    require registering a new std name.
    """
    return value[key]


def std_init(value: Any, *, key: str) -> dict[str, Any]:
    """Wire-format-stable std.init; body frozen once any artifact references it.

    Starts an env record by wrapping the raw flowing value under ``key``.
    Deliberate behavior changes require registering a new std name.
    """
    return {key: value}


def std_assign(value: Any, *, key: str) -> dict[str, Any]:
    """Wire-format-stable std.assign; body frozen once any artifact references it.

    Extends an existing env record from a fixed pair-input layout ``[env, item]``.
    This is distinct from std.init and never sniffs the flowing value to choose
    env-entry vs env-extend behavior. Deliberate behavior changes require
    registering a new std name.
    """
    env, item = value
    copied = dict(env)
    copied[key] = item
    return copied


def std_collect(value: Any, *, fields: list[str]) -> dict[str, Any]:
    """Wire-format-stable std.collect; body frozen once any artifact references it.

    Extends an env record from the flat par fold-back layout
    ``[env, item1, item2, ...]``. ``fields`` names each item in order. This is
    the multi-result sibling of std.assign. Deliberate behavior changes require
    registering a new std name.
    """
    expected = len(fields) + 1
    if len(value) != expected:
        raise ValueError(f"std.collect expected {expected} values, got {len(value)}")
    copied = dict(value[0])
    for idx, field in enumerate(fields, start=1):
        copied[field] = value[idx]
    return copied


def std_pack(value: Any, *, fields: dict[str, Any]) -> dict[str, Any]:
    """Wire-format-stable std.pack; body frozen once any artifact references it.

    Builds a named record for closure conversion. Each output name maps to one
    selector: ``{"field": "source"}`` copies a field from the flowing input,
    ``{"input": true}`` copies the whole flowing input, and ``{"const": value}``
    embeds a JSON static arg value. Deliberate behavior changes require
    registering a new std name.
    """
    packed: dict[str, Any] = {}
    for name, selector in fields.items():
        if isinstance(selector, dict) and set(selector) == {"field"}:
            packed[name] = value[selector["field"]]
        elif isinstance(selector, dict) and set(selector) == {"input"} and selector["input"] is True:
            packed[name] = value
        elif isinstance(selector, dict) and set(selector) == {"const"}:
            packed[name] = selector["const"]
        else:
            raise ValueError(f"std.pack invalid selector for field {name!r}")
    return packed


def std_unpack(value: Any, *, fields: dict[str, str]) -> dict[str, Any]:
    """Wire-format-stable std.unpack; body frozen once any artifact references it.

    Unpacks a named closure-conversion record. ``fields`` maps output env names
    to packed-record field names. Deliberate behavior changes require
    registering a new std name.
    """
    unpacked: dict[str, Any] = {}
    for name, source in fields.items():
        unpacked[name] = value[source]
    return unpacked


def std_bind(value: Any, *, consts: dict[str, Any]) -> dict[str, Any]:
    """Wire-format-stable std.bind; body frozen once any artifact references it.

    Adds static JSON constants to the flowing input. If a const key is already
    present in the flowing input, raises a deterministic collision error.
    Deliberate behavior changes require registering a new std name.
    """
    collisions = [key for key in sorted(consts) if key in value]
    if collisions:
        raise ValueError("std.bind key collision: " + ", ".join(collisions))

    merged = dict(value)
    for key in sorted(consts):
        merged[key] = consts[key]
    return merged


def std_record(
    value: Any,
    *,
    fields: list[list[str | int | None]],
    consts: dict[str, Any],
) -> dict[str, Any]:
    """Wire-format-stable std.record; body frozen once artifacts reference it.

    Builds a named record from the positional multi-input layout. Each ordered
    ``fields`` entry is ``[name, input_index]``; a null index selects ``name``
    from ``consts``. Repeated indexes preserve aliases while graph inputs stay
    deduplicated. Deliberate behavior changes require registering a new std name.
    """
    parsed: list[tuple[str, int | None]] = []
    input_count = 0
    for position, field_spec in enumerate(fields):
        if len(field_spec) != 2:
            raise ValueError(f"std.record invalid field spec at index {position}")
        name, input_index = field_spec
        if not isinstance(name, str) or (
            input_index is not None
            and (
                not isinstance(input_index, int)
                or isinstance(input_index, bool)
                or input_index < 0
            )
        ):
            raise ValueError(f"std.record invalid field spec at index {position}")
        parsed.append((name, input_index))
        if input_index is not None:
            input_count = max(input_count, input_index + 1)

    values = [] if input_count == 0 else [value] if input_count == 1 else value
    if len(values) != input_count:
        raise ValueError(f"std.record expected {input_count} values, got {len(values)}")

    record: dict[str, Any] = {}
    for position, (name, input_index) in enumerate(parsed):
        if input_index is None:
            if name not in consts:
                raise ValueError(f"std.record missing const for field {name!r}")
            record[name] = consts[name]
        elif input_index >= input_count:
            raise ValueError(f"std.record invalid field spec at index {position}")
        else:
            record[name] = values[input_index]
    return record


def std_each_pack(
    value: Any,
    *,
    items: str,
    item: str,
    fields: dict[str, str],
    consts: dict[str, Any],
) -> list[dict[str, Any]]:
    """Wire-format-stable std.each_pack; body frozen once artifacts reference it.

    Builds closure-conversion records for a dynamic fan-out before the each node.
    ``items`` names the list-valued env field, ``item`` names each per-item
    field in the packed record, ``fields`` maps packed names to copied env
    fields, and ``consts`` embeds static JSON values. Deliberate behavior
    changes require registering a new std name.
    """
    packed_items: list[dict[str, Any]] = []
    for element in value[items]:
        packed = {item: element}
        for name, source in fields.items():
            packed[name] = value[source]
        for name in sorted(consts):
            packed[name] = consts[name]
        packed_items.append(packed)
    return packed_items


def std_branch_predicate(value: Any) -> bool:
    """Wire-format-stable std.branch_predicate; body frozen once referenced.

    Frontends use this fixed adapter after evaluating an authored subject-shaped
    predicate into the internal ``__branch__`` env field. Deliberate behavior
    changes require registering a new std name.
    """
    return bool(value["__branch__"])


def std_branch_selector(value: Any) -> str:
    """Wire-format-stable std.branch_selector; body frozen once referenced.

    Frontends use this fixed adapter after evaluating an authored subject-shaped
    selector into the internal ``__branch__`` env field. Deliberate behavior
    changes require registering a new std name.
    """
    return str(value["__branch__"])


def std_continue_with(value: Any) -> dict[str, Any]:
    """Wire-format-stable std.continue_with; body frozen once referenced.

    Wraps the final value in the continuation sentinel. Deliberate behavior
    changes require registering a new std name.
    """
    return {"__continue__": value}


def std_rounds_remaining_note(value: Any) -> str:
    """Wire-format-stable std.rounds_remaining_note; body frozen once referenced.

    Builds the controller note used by the mem-mcp port mapping:
    record/execute.ctx's ``[REMAINING ROUNDS: N]`` maps to
    ``round_note="std.rounds_remaining_note"``. Deliberate behavior changes
    require registering a new std name.
    """
    return f"[REMAINING ROUNDS: {value['maxRounds'] - value['round']}]"


DEFAULT_REGISTRY.register_pure("std.merge", std_merge)
DEFAULT_REGISTRY.register_pure("std.pluck", std_pluck)
DEFAULT_REGISTRY.register_pure("std.init", std_init)
DEFAULT_REGISTRY.register_pure("std.assign", std_assign)
DEFAULT_REGISTRY.register_pure("std.collect", std_collect)
DEFAULT_REGISTRY.register_pure("std.pack", std_pack)
DEFAULT_REGISTRY.register_pure("std.unpack", std_unpack)
DEFAULT_REGISTRY.register_pure("std.bind", std_bind)
DEFAULT_REGISTRY.register_pure("std.record", std_record)
DEFAULT_REGISTRY.register_pure("std.each_pack", std_each_pack)
DEFAULT_REGISTRY.register_pure("std.branch_predicate", std_branch_predicate)
DEFAULT_REGISTRY.register_pure("std.branch_selector", std_branch_selector)
DEFAULT_REGISTRY.register_pure("std.continue_with", std_continue_with)
DEFAULT_REGISTRY.register_pure("std.rounds_remaining_note", std_rounds_remaining_note)
