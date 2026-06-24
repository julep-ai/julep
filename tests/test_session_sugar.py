"""Coroutine sugar tests for sessions."""

from __future__ import annotations

from typing import Any

import pytest

from composable_agents import arr, recv, register_pure, seq
from composable_agents.kinds import Op
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
