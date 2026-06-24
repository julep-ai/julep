"""Static validation for long-lived session LOOP flows."""

from __future__ import annotations

import pytest

from composable_agents.derived import emit, hedge, human_gate, quorum, race, recv
from composable_agents.dsl import alt, each, ident, iter_up_to, par, seq, stage, think
from composable_agents.ir import Node
from composable_agents.kinds import Op
from composable_agents.session import loop, scan
from composable_agents.validate import blocking, validate


def codes(flow: Node) -> set[str]:
    return {d.code for d in validate(flow)}


def err_codes(flow: Node) -> set[str]:
    return {d.code for d in blocking(validate(flow))}


def session_codes(flow: Node) -> set[str]:
    return {code for code in codes(flow) if code.startswith("SESSION_")}


def assert_no_session_codes(flow: Node) -> None:
    assert session_codes(flow) == set()


# --------------------------------------------------------------------------- #
# Sequential-position fence.
# --------------------------------------------------------------------------- #
def test_recv_under_plain_par_is_rejected() -> None:
    flow = scan(par(recv("in"), think("a")), init={}).body

    assert "SESSION_RECV_IN_PARALLEL" in err_codes(flow)


def test_emit_under_plain_par_is_rejected() -> None:
    flow = scan(seq(recv("in"), par(emit("out"), think("a"))), init={}).body

    assert "SESSION_EMIT_IN_PARALLEL" in err_codes(flow)


def test_recv_under_each_is_rejected() -> None:
    flow = scan(each(recv("in")), init={}).body

    assert "SESSION_RECV_IN_PARALLEL" in err_codes(flow)


@pytest.mark.parametrize(
    "flow",
    [
        race(recv("a"), recv("b")),
        hedge(recv("a"), recv("b"), hedge_ms=25),
        quorum(recv("a"), recv("b"), k=1),
    ],
)
def test_recv_under_race_like_par_is_rejected(flow: Node) -> None:
    session = scan(flow, init={}).body

    assert "SESSION_RECV_IN_PARALLEL" in err_codes(session)


def test_recv_and_emit_under_alt_are_accepted_by_fence() -> None:
    flow = scan(
        seq(
            recv("in"),
            alt(pred="p", if_true=emit("out"), if_false=emit("out")),
        ),
        init={},
    ).body

    session = session_codes(flow)
    assert "SESSION_RECV_IN_PARALLEL" not in session
    assert "SESSION_EMIT_IN_PARALLEL" not in session
    assert "SESSION_LOOP_NOT_RECV_GUARDED" not in session
    assert "SESSION_LOOP_EMIT_BEFORE_RECV" not in session


def test_recv_and_emit_under_seq_are_accepted() -> None:
    flow = scan(seq(recv("in"), emit("out")), init={}).body

    assert_no_session_codes(flow)


# --------------------------------------------------------------------------- #
# LOOP placement.
# --------------------------------------------------------------------------- #
def test_loop_at_session_root_is_accepted_by_placement() -> None:
    flow = scan(seq(recv("in"), emit("out")), init={}).body

    session = session_codes(flow)
    assert "SESSION_LOOP_IN_EVAL_PLAN" not in session
    assert "SESSION_LOOP_NESTED" not in session
    assert "SESSION_LOOP_IN_PARALLEL" not in session


def test_loop_nested_under_loop_is_rejected() -> None:
    inner = scan(seq(recv("in"), emit("out")), init={}).body
    outer = loop(inner, init={}).body

    assert "SESSION_LOOP_NESTED" in err_codes(outer)


def test_loop_inside_eval_plan_plan_is_rejected() -> None:
    inner = scan(seq(recv("in"), emit("out")), init={}).body
    flow = Node(op=Op.EVAL_PLAN, id="ev-loop-plan", plan=inner)

    assert "SESSION_LOOP_IN_EVAL_PLAN" in err_codes(flow)


def test_loop_under_par_is_rejected_by_fence() -> None:
    inner = scan(seq(recv("in"), emit("out")), init={}).body
    flow = par(inner, ident())

    assert "SESSION_LOOP_IN_PARALLEL" in err_codes(flow)


# --------------------------------------------------------------------------- #
# recv_guarded productivity.
# --------------------------------------------------------------------------- #
def test_guarded_loop_body_is_accepted() -> None:
    flow = scan(seq(recv("in"), emit("out")), init={}).body

    session = session_codes(flow)
    assert "SESSION_LOOP_NOT_RECV_GUARDED" not in session
    assert "SESSION_LOOP_EMIT_BEFORE_RECV" not in session


def test_emit_before_recv_is_rejected() -> None:
    flow = scan(seq(emit("out"), recv("in")), init={}).body

    assert "SESSION_LOOP_EMIT_BEFORE_RECV" in err_codes(flow)


def test_missing_recv_on_loop_body_path_is_rejected() -> None:
    flow = scan(ident(), init={}).body

    assert "SESSION_LOOP_NOT_RECV_GUARDED" in err_codes(flow)


def test_human_gate_does_not_satisfy_recv_guard() -> None:
    flow = scan(human_gate(prompt="approve"), init={}).body

    assert "SESSION_LOOP_NOT_RECV_GUARDED" in err_codes(flow)


def test_conditional_recv_under_alt_is_rejected() -> None:
    flow = scan(
        alt(pred="p", if_true=recv("in"), if_false=ident()),
        init={},
    ).body

    assert "SESSION_LOOP_NOT_RECV_GUARDED" in err_codes(flow)


def test_recv_on_both_alt_branches_is_accepted() -> None:
    flow = scan(
        alt(pred="p", if_true=recv("in"), if_false=recv("in")),
        init={},
    ).body

    assert "SESSION_LOOP_NOT_RECV_GUARDED" not in session_codes(flow)


def test_baked_eval_plan_with_recv_in_loop_body_is_accepted() -> None:
    body = Node(
        op=Op.EVAL_PLAN,
        id="ev-baked-recv",
        plan=seq(recv("in"), emit("out")),
    )
    flow = scan(body, init={}).body

    session = session_codes(flow)
    assert "SESSION_LOOP_NOT_RECV_GUARDED" not in session
    assert "SESSION_LOOP_EVAL_PLAN_CONTROLLER" not in session


def test_controller_only_eval_plan_in_loop_body_is_rejected() -> None:
    flow = scan(stage("planner"), init={}).body

    session = err_codes(flow)
    assert "SESSION_LOOP_EVAL_PLAN_CONTROLLER" in session
    assert "SESSION_LOOP_NOT_RECV_GUARDED" in session


def test_iter_up_to_does_not_satisfy_recv_guard() -> None:
    flow = scan(iter_up_to(3, recv("in")), init={}).body

    assert "SESSION_LOOP_NOT_RECV_GUARDED" in err_codes(flow)


def test_recv_before_iter_up_to_satisfies_recv_guard() -> None:
    flow = scan(seq(recv("in"), iter_up_to(3, ident())), init={}).body

    assert_no_session_codes(flow)


# --------------------------------------------------------------------------- #
# Declared-channel check (non-blocking warning).
# --------------------------------------------------------------------------- #
def test_undeclared_channel_emits_warning() -> None:
    # recv targets "typo" but the loop only declares "in"/"out".
    flow = scan(seq(recv("typo"), emit("out")), init={}).body

    assert "CHANNEL_UNDECLARED" in codes(flow)
    # It is a non-blocking warning: never surfaces as an error, never as SESSION_*.
    assert "CHANNEL_UNDECLARED" not in err_codes(flow)
    assert "CHANNEL_UNDECLARED" not in session_codes(flow)


def test_declared_channels_emit_no_warning() -> None:
    flow = scan(seq(recv("in"), emit("out")), init={}).body

    assert "CHANNEL_UNDECLARED" not in codes(flow)
