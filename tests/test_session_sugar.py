"""Coroutine sugar tests for sessions."""

from __future__ import annotations

from typing import Any

import pytest

from composable_agents import arr, recv, register_pure, seq
from composable_agents.kinds import Op
from composable_agents.purity import _REGISTRY, register_pure_with_source
from composable_agents.session import (
    SessionCompileError,
    drive_session,
    scan,
    session,
)
from composable_agents.transforms import normalize_ids
from conftest import run


def _echo_step(value: dict[str, Any]) -> tuple[list[Any], Any]:
    carrier = list(value["carrier"])
    msg = value["msg"]
    return [*carrier, msg], msg


def _accumulator_step(value: dict[str, Any]) -> tuple[int, int]:
    total = int(value["carrier"])
    msg = int(value["msg"])
    reply = total + msg
    return reply, reply


register_pure("tests.session_sugar.echo_step", _echo_step)
register_pure("tests.session_sugar.accumulator_step", _accumulator_step)


@session
async def echo_session(s: Any) -> None:
    seen = []
    while True:
        msg = await s.recv()
        await s.emit(msg)
        seen = [*seen, msg]


@session
async def accumulator_session(s: Any) -> None:
    total = 0
    while True:
        msg = await s.recv()
        reply = total + msg
        await s.emit(reply)
        total = reply


def _scrub_pure_names(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<pure>" if key == "pure" else _scrub_pure_names(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub_pure_names(item) for item in value]
    return value


def _normalized_body_json_without_pures(body: Any) -> Any:
    return _scrub_pure_names(normalize_ids(body).to_json())


def _session_pure_entries(name: str) -> list[Any]:
    prefix = f"session.{__name__}.{name}"
    return [
        entry
        for pure_name, entry in _REGISTRY.items()
        if pure_name == prefix or pure_name.startswith(f"{prefix}.")
    ]


def test_session_sugar_echo_matches_hand_scan_runtime_and_loop_shape() -> None:
    hand = scan(
        seq(recv("in"), arr("tests.session_sugar.echo_step")),
        init=[],
    )

    assert run(drive_session(echo_session, inputs=["a", "b", "c"])) == run(
        drive_session(hand, inputs=["a", "b", "c"])
    )

    assert echo_session.body.op == hand.body.op == Op.LOOP
    assert echo_session.body.channels == hand.body.channels
    assert echo_session.body.args == hand.body.args == {"split": True}
    assert _normalized_body_json_without_pures(echo_session.body) == (
        _normalized_body_json_without_pures(hand.body)
    )


def test_session_sugar_accumulator_matches_hand_scan_runtime() -> None:
    hand = scan(
        seq(recv("in"), arr("tests.session_sugar.accumulator_step")),
        init=0,
    )

    assert run(drive_session(accumulator_session, inputs=[1, 2, 3, 4])) == run(
        drive_session(hand, inputs=[1, 2, 3, 4])
    )


def test_session_sugar_distinct_sessions_have_distinct_source_hashes() -> None:
    @session
    async def hash_left(s: Any) -> None:
        while True:
            msg = await s.recv()
            await s.emit(msg + "!")

    @session
    async def hash_right(s: Any) -> None:
        while True:
            msg = await s.recv()
            await s.emit(msg + "?")

    del hash_left, hash_right

    left_entries = _session_pure_entries(
        "test_session_sugar_distinct_sessions_have_distinct_source_hashes.<locals>.hash_left"
    )
    right_entries = _session_pure_entries(
        "test_session_sugar_distinct_sessions_have_distinct_source_hashes.<locals>.hash_right"
    )
    assert len(left_entries) == 1
    assert len(right_entries) == 1
    assert left_entries[0].source_hash != right_entries[0].source_hash


def test_register_pure_with_source_is_idempotent_for_identical_source() -> None:
    name = "tests.session_sugar.with_source_idempotent"

    def first(value: int) -> int:
        return value + 1

    def second(value: int) -> int:
        return value + 2

    try:
        original = register_pure_with_source(name, first, "same source\n")
        repeated = register_pure_with_source(name, second, "same source\n")

        assert repeated is original
        assert _REGISTRY[name] is original

        with pytest.raises(ValueError, match="registered with different source"):
            register_pure_with_source(name, first, "different source\n")
    finally:
        _REGISTRY.pop(name, None)


def test_session_sugar_redecorating_same_factory_session_is_idempotent() -> None:
    def factory() -> Any:
        @session
        async def demo(s: Any) -> None:
            while True:
                msg = await s.recv()
                await s.emit(msg)

        return demo

    first = factory()
    second = factory()

    entries = _session_pure_entries(
        "test_session_sugar_redecorating_same_factory_session_is_idempotent."
        "<locals>.factory.<locals>.demo"
    )
    assert len(entries) == 1
    assert run(drive_session(first, inputs=["a"]))[1] == ["a"]
    assert run(drive_session(second, inputs=["b"]))[1] == ["b"]


def test_session_sugar_lifts_read_only_pre_loop_local() -> None:
    @session
    async def prefix_session(s: Any) -> None:
        prefix = ">> "
        while True:
            msg = await s.recv()
            await s.emit(prefix + msg)

    assert run(drive_session(prefix_session, inputs=["a", "b"]))[1] == [
        ">> a",
        ">> b",
    ]


def test_session_sugar_lifts_augassign_carried_state() -> None:
    @session
    async def counter_session(s: Any) -> None:
        count = 0
        while True:
            _msg = await s.recv()
            count += 1
            await s.emit(count)

    assert run(drive_session(counter_session, inputs=["a", "b", "c"]))[1] == [
        1,
        2,
        3,
    ]


def test_session_sugar_rejects_two_receives() -> None:
    with pytest.raises(SessionCompileError, match=r"scan\("):

        @session
        async def bad_two_receives(s: Any) -> None:
            seen = []
            while True:
                first = await s.recv()
                second = await s.recv()
                await s.emit(second)
                seen = [*seen, first, second]


def test_session_sugar_rejects_nested_capture_of_carried_local() -> None:
    with pytest.raises(SessionCompileError, match=r"scan\("):

        @session
        async def bad_nested_capture(s: Any) -> None:
            seen = []
            while True:
                msg = await s.recv()

                def reply() -> list[Any]:
                    return seen

                await s.emit(reply())
                seen = [*seen, msg]
