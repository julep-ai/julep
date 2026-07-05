"""Static validation for long-lived session LOOP flows."""

from __future__ import annotations

import pytest

from julep.derived import emit, hedge, human_gate, quorum, race, recv
from julep.dsl import alt, each, ident, iter_up_to, par, seq, stage, think
from julep.errors import JulepError
from julep.ir import ChannelRef, Node
from julep.kinds import Op
from julep.session import scan
from julep.validate import blocking, validate


def raw_loop(body: Node, **kwargs: object) -> Node:
    return Node(
        op=Op.LOOP,
        id="raw-loop",
        body=body,
        channels=[ChannelRef("in"), ChannelRef("out")],
        **kwargs,
    )


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
    flow = raw_loop(par(recv("in"), think("a")))

    assert "SESSION_RECV_IN_PARALLEL" in err_codes(flow)


def test_emit_under_plain_par_is_rejected() -> None:
    flow = raw_loop(seq(recv("in"), par(emit("out"), think("a"))))

    assert "SESSION_EMIT_IN_PARALLEL" in err_codes(flow)


def test_recv_under_each_is_rejected() -> None:
    flow = raw_loop(each(recv("in")))

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
    session = raw_loop(flow)

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
    inner = raw_loop(seq(recv("in"), emit("out")))
    outer = raw_loop(inner)

    assert "SESSION_LOOP_NESTED" in err_codes(outer)


def test_loop_inside_eval_plan_plan_is_rejected() -> None:
    inner = raw_loop(seq(recv("in"), emit("out")))
    flow = Node(op=Op.EVAL_PLAN, id="ev-loop-plan", plan=inner)

    assert "SESSION_LOOP_IN_EVAL_PLAN" in err_codes(flow)


def test_loop_under_par_is_rejected_by_fence() -> None:
    inner = raw_loop(seq(recv("in"), emit("out")))
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
    flow = raw_loop(seq(emit("out"), recv("in")))

    assert "SESSION_LOOP_EMIT_BEFORE_RECV" in err_codes(flow)


def test_missing_recv_on_loop_body_path_is_rejected() -> None:
    flow = raw_loop(ident())

    assert "SESSION_LOOP_NOT_RECV_GUARDED" in err_codes(flow)


def test_human_gate_does_not_satisfy_recv_guard() -> None:
    flow = raw_loop(human_gate(prompt="approve"))

    assert "SESSION_LOOP_NOT_RECV_GUARDED" in err_codes(flow)


def test_conditional_recv_under_alt_is_rejected() -> None:
    flow = raw_loop(
        alt(pred="p", if_true=recv("in"), if_false=ident()),
    )

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
    flow = raw_loop(body)

    session = session_codes(flow)
    assert "SESSION_LOOP_NOT_RECV_GUARDED" not in session
    assert "SESSION_LOOP_EVAL_PLAN_CONTROLLER" not in session


def test_controller_only_eval_plan_in_loop_body_is_rejected() -> None:
    flow = raw_loop(stage("planner"))

    session = err_codes(flow)
    assert "SESSION_LOOP_EVAL_PLAN_CONTROLLER" in session
    assert "SESSION_LOOP_NOT_RECV_GUARDED" in session


def test_iter_up_to_does_not_satisfy_recv_guard() -> None:
    flow = raw_loop(iter_up_to(3, recv("in")))

    assert "SESSION_LOOP_NOT_RECV_GUARDED" in err_codes(flow)


def test_recv_before_iter_up_to_satisfies_recv_guard() -> None:
    flow = scan(seq(recv("in"), iter_up_to(3, ident())), init={}).body

    assert_no_session_codes(flow)


def test_multiple_recv_on_loop_body_path_is_rejected() -> None:
    flow = raw_loop(seq(recv("in"), emit("out"), recv("in")))

    assert "SESSION_LOOP_MULTIPLE_RECV" in err_codes(flow)


def test_scan_raises_for_multiple_recv_on_loop_body_path() -> None:
    with pytest.raises(
        JulepError,
        match="SESSION_LOOP_MULTIPLE_RECV",
    ):
        scan(seq(recv("in"), emit("out"), recv("in")), init={})


def test_loop_with_non_body_child_is_rejected() -> None:
    flow = raw_loop(seq(recv("in"), emit("out")), left=recv("in"))

    assert "SESSION_LOOP_BAD_FIELDS" in err_codes(flow)


# --------------------------------------------------------------------------- #
# Declared-channel check (non-blocking warning).
# --------------------------------------------------------------------------- #
def test_undeclared_channel_emits_warning() -> None:
    # recv targets "typo" but the loop only declares "in"/"out".
    flow = raw_loop(seq(recv("typo"), emit("out")))

    assert "CHANNEL_UNDECLARED" in codes(flow)
    # The legacy warning remains non-blocking even though session construction
    # now also reports a blocking SESSION_* diagnostic.
    assert "CHANNEL_UNDECLARED" not in err_codes(flow)
    assert "SESSION_CHANNEL_UNDECLARED" in err_codes(flow)


def test_scan_raises_for_undeclared_session_channel() -> None:
    with pytest.raises(
        JulepError,
        match="SESSION_CHANNEL_UNDECLARED",
    ):
        scan(seq(recv("extra"), emit("out")), init={})


def test_declared_channels_emit_no_warning() -> None:
    flow = scan(seq(recv("in"), emit("out")), init={}).body

    assert "CHANNEL_UNDECLARED" not in codes(flow)
    assert "SESSION_CHANNEL_UNDECLARED" not in err_codes(flow)


# --------------------------------------------------------------------------- #
# Flow-vs-session target gate.
# --------------------------------------------------------------------------- #
def test_ordinary_flow_rejects_recv_emit_session_ops() -> None:
    flow = seq(recv("in"), emit("out"))

    errors = err_codes(flow)
    assert "SESSION_RECV_IN_FLOW" in errors
    assert "SESSION_EMIT_IN_FLOW" in errors


def test_ordinary_flow_without_session_ops_has_no_target_codes() -> None:
    assert_no_session_codes(ident())


def test_ordinary_flow_rejects_bare_emit() -> None:
    assert "SESSION_EMIT_IN_FLOW" in err_codes(emit("out"))


def test_well_formed_session_has_no_target_gate_codes() -> None:
    flow = scan(seq(recv("in"), emit("out")), init={}).body

    assert_no_session_codes(flow)


def test_explicit_flow_target_rejects_root_loop() -> None:
    flow = raw_loop(seq(recv("in"), emit("out")))

    errors = {d.code for d in blocking(validate(flow, target="flow"))}
    assert "SESSION_LOOP_IN_FLOW" in errors


def test_explicit_session_target_accepts_root_loop_target() -> None:
    flow = raw_loop(seq(recv("in"), emit("out")))

    errors = {d.code for d in blocking(validate(flow, target="session"))}
    assert "SESSION_LOOP_IN_FLOW" not in errors


def test_default_target_still_infers_plain_flow_mode() -> None:
    flow = seq(recv("in"), emit("out"))

    errors = err_codes(flow)
    assert "SESSION_RECV_IN_FLOW" in errors
    assert "SESSION_EMIT_IN_FLOW" in errors


def test_recv_reachable_outside_loop_is_rejected() -> None:
    flow = seq(recv("x"), raw_loop(seq(recv("in"), emit("out"))))

    assert "SESSION_RECV_OUTSIDE_LOOP" in err_codes(flow)


# --------------------------------------------------------------------------- #
# Build-time enforcement.
# --------------------------------------------------------------------------- #
def test_scan_raises_for_unguarded_loop_body() -> None:
    with pytest.raises(
        JulepError,
        match="SESSION_LOOP_NOT_RECV_GUARDED",
    ):
        scan(ident(), init={})


def test_scan_raises_for_recv_under_parallel_fence() -> None:
    with pytest.raises(
        JulepError,
        match="SESSION_RECV_IN_PARALLEL",
    ):
        scan(par(recv("in"), think("a")), init={})


def test_well_formed_session_builds() -> None:
    session = scan(seq(recv("in"), emit("out")), init={})

    assert session.body.op == Op.LOOP
