"""End-to-end tests for the durable session runtime (design §6, §7, M2).

These run against Temporal's time-skipping test server. They exercise
``SessionWorkflow`` (the generalized FlowWorkflow for a root ``Op.LOOP``):
durable recv/emit, the ``send`` Update, ``open_receives``/``state`` queries,
carrier persistence across a forced continue-as-new, replay determinism, and
``FlowWorkflow`` rejecting a frozen ``Op.LOOP``.

Skipped entirely when ``temporalio`` is not installed.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from composable_agents import HAVE_TEMPORAL, register_pure

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.client import WorkflowFailureError
    from temporalio.exceptions import ApplicationError
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Worker
    from temporalio.worker.workflow_sandbox import (
        SandboxedWorkflowRunner,
        SandboxRestrictions,
    )

    from composable_agents import Agent, arr, freeze, manifest_to_json, seq
    from composable_agents.derived import emit as emit_leaf
    from composable_agents.derived import recv as recv_leaf
    from composable_agents.freeze import McpSnapshot
    from composable_agents.session import loop, scan
    from composable_agents.execution.activities import WorkerContext, configure
    from composable_agents.execution.harness import (
        ExecutionPolicy,
        FlowWorkflow,
        FlowInput,
        SessionWorkflow,
        SessionInput,
        run_flow,
    )
    from composable_agents.execution.session_store import InMemorySessionStore
    from composable_agents.execution.worker import ACTIVITIES, WORKFLOWS


# --------------------------------------------------------------------------- #
# Pure turn bodies (registered so frozen ``arr`` leaves resolve in the worker).
# --------------------------------------------------------------------------- #
def _echo_step(value):
    # ``scan`` body: receives ``{"carrier": s, "msg": m}`` (recv output threaded
    # via the turn), returns ``(next_carrier, output)``. Here the carrier counts
    # turns; the output echoes the message with the running count.
    carrier = value["carrier"]
    msg = value["msg"]
    n = (carrier or 0) + 1
    return (n, {"echo": msg, "turn": n})


register_pure("test.session_echo_step", _echo_step)


def _identity_step(value):
    return value


register_pure("test.session_identity_step", _identity_step)


def _make_session_flow():
    # scan(turn, init) where turn = recv -> arr(step). The scan marks the LOOP
    # ``split`` so the driver splits the 2-tuple into (carrier, emit).
    turn = seq(recv_leaf("in"), arr("test.session_echo_step"))
    return scan(turn, init=0, in_channel="in", out_channel="out")


def _make_timeout_session_flow():
    turn = seq(recv_leaf("in", timeout_s=1), arr("test.session_echo_step"))
    return scan(turn, init=0, in_channel="in", out_channel="out")


def _frozen_session():
    session = _make_session_flow()
    fr = freeze(session.body, McpSnapshot())
    return fr, session


def _frozen_timeout_session():
    session = _make_timeout_session_flow()
    fr = freeze(session.body, McpSnapshot())
    return fr, session


async def _wait_for(predicate, *, attempts=100):
    for _ in range(attempts):
        if await predicate():
            return
        await asyncio.sleep(0.05)
    assert await predicate()


# --------------------------------------------------------------------------- #
# Worker helper.
# --------------------------------------------------------------------------- #
def _build_worker(env, task_queue, store):
    ctx = WorkerContext(session_store=store)
    configure(ctx)
    return Worker(
        env.client,
        task_queue=task_queue,
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
        workflow_runner=SandboxedWorkflowRunner(
            restrictions=SandboxRestrictions.default.with_passthrough_modules(
                "composable_agents"
            )
        ),
    )


# --------------------------------------------------------------------------- #
# 1. Multi-turn session: send drives turns; events() collects emits.
# --------------------------------------------------------------------------- #
async def _multi_turn(env):
    store = InMemorySessionStore(empty_value=0)
    fr, session = _frozen_session()
    tq = "ca-session-multi"
    worker = _build_worker(env, tq, store)
    async with worker:
        sid = f"session-{uuid.uuid4()}"
        handle = await env.client.start_workflow(
            SessionWorkflow.run,
            SessionInput(
                session_id=sid,
                flow_json=fr.flow.to_json(),
                manifest_json=manifest_to_json(fr.manifest),
                init=0,
                in_channel="in",
                out_channel="out",
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue=tq,
        )

        # send is a Temporal Update: synchronous ack with assigned seq.
        ack1 = await handle.execute_update("send", {"channel": "in", "value": "hi"})
        assert ack1["seq"] == 1, ack1
        ack2 = await handle.execute_update("send", {"channel": "in", "value": "yo"})
        assert ack2["seq"] == 2, ack2

        # Drain emits via the state query until both turns have run.
        async def _drained():
            snap = await handle.query("state")
            return len(snap.get("emitted", {}).get("out", [])) >= 2

        await _wait_for(_drained, attempts=50)

        snap = await handle.query("state")
        emits = snap["emitted"]["out"]
        assert [e["payload"]["echo"] for e in emits] == ["hi", "yo"], snap
        assert [e["payload"]["turn"] for e in emits] == [1, 2], snap
        # per-channel monotonic seq on emits.
        assert [e["seq"] for e in emits] == [1, 2], snap

        ack = await handle.execute_update("ack", {"channel": "out", "seq": 1})
        assert ack == {"channel": "out", "acked": 1}
        snap = await handle.query("state")
        assert snap["ack_cursors"] == {"out": 1}, snap
        emits = snap["emitted"]["out"]
        assert [e["seq"] for e in emits] == [2], snap

        await handle.execute_update("close", {})
        await handle.result()


# --------------------------------------------------------------------------- #
# 2. open_receives / state queries.
# --------------------------------------------------------------------------- #
async def _queries(env):
    store = InMemorySessionStore(empty_value=0)
    fr, session = _frozen_session()
    tq = "ca-session-queries"
    worker = _build_worker(env, tq, store)
    async with worker:
        sid = f"session-q-{uuid.uuid4()}"
        handle = await env.client.start_workflow(
            SessionWorkflow.run,
            SessionInput(
                session_id=sid,
                flow_json=fr.flow.to_json(),
                manifest_json=manifest_to_json(fr.manifest),
                init=0,
                in_channel="in",
                out_channel="out",
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue=tq,
        )

        # With nothing sent, the loop parks on recv("in").
        async def _parked():
            recvs = await handle.query("open_receives")
            return any(r["channel"] == "in" for r in recvs)

        await _wait_for(_parked, attempts=50)
        recvs = await handle.query("open_receives")
        assert any(r["channel"] == "in" for r in recvs), recvs

        snap = await handle.query("state")
        assert "capacity" in snap, snap

        await handle.execute_update("close", {})
        await handle.result()


# --------------------------------------------------------------------------- #
# 3. Carrier persists across forced, repeated continue-as-new.
# --------------------------------------------------------------------------- #
async def _carrier_survives_continue_as_new(env):
    store = InMemorySessionStore(empty_value=0)
    fr, session = _frozen_session()
    tq = "ca-session-can"
    worker = _build_worker(env, tq, store)
    async with worker:
        sid = f"session-can-{uuid.uuid4()}"
        # history_threshold=1 forces continue-as-new after each completed turn.
        handle = await env.client.start_workflow(
            SessionWorkflow.run,
            SessionInput(
                session_id=sid,
                flow_json=fr.flow.to_json(),
                manifest_json=manifest_to_json(fr.manifest),
                init=0,
                in_channel="in",
                out_channel="out",
                policy=ExecutionPolicy().to_json(),
                history_threshold=1,
            ),
            id=sid,
            task_queue=tq,
        )

        words = ("a", "b", "c", "d", "e")

        def _committed_count():
            return sum(len(revs) for revs in store._revisions.values())

        async def _parked_on_recv():
            try:
                recvs = await env.client.get_workflow_handle(sid).query("open_receives")
            except Exception:
                return False
            return any(r["channel"] == "in" for r in recvs)

        for index, word in enumerate(words, start=1):
            await _wait_for(_parked_on_recv, attempts=400)
            chain = env.client.get_workflow_handle(sid)
            await chain.execute_update("send", {"channel": "in", "value": word})

            async def _committed():
                return _committed_count() >= index

            await _wait_for(_committed, attempts=400)

        chain = env.client.get_workflow_handle(sid)

        async def _all_done():
            try:
                snap = await chain.query("state")
            except Exception:
                return False
            return len(snap.get("emitted", {}).get("out", [])) >= len(words)

        await _wait_for(_all_done)

        snap = await chain.query("state")
        emits = snap["emitted"]["out"]
        # The carrier (turn counter) survived the forced continue-as-new: turn
        # numbers keep incrementing rather than resetting.
        assert [e["payload"]["echo"] for e in emits] == list(words), snap
        assert [e["payload"]["turn"] for e in emits] == [1, 2, 3, 4, 5], snap
        assert [e["seq"] for e in emits] == [1, 2, 3, 4, 5], snap
        # The store committed the carrier at >=1 cursor.
        committed = _committed_count()
        assert committed > 1, committed

        await chain.execute_update("close", {})
        await chain.result()


# --------------------------------------------------------------------------- #
# 3b. Per-recv timeout retries the receive instead of ending the session.
# --------------------------------------------------------------------------- #
async def _recv_timeout_keeps_session_alive(env):
    store = InMemorySessionStore(empty_value=0)
    fr, session = _frozen_timeout_session()
    tq = "ca-session-timeout"
    worker = _build_worker(env, tq, store)
    async with worker:
        sid = f"session-timeout-{uuid.uuid4()}"
        handle = await env.client.start_workflow(
            SessionWorkflow.run,
            SessionInput(
                session_id=sid,
                flow_json=fr.flow.to_json(),
                manifest_json=manifest_to_json(fr.manifest),
                init=0,
                in_channel="in",
                out_channel="out",
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue=tq,
        )

        async def _parked_after_timeout():
            recvs = await handle.query("open_receives")
            return any(r["channel"] == "in" for r in recvs)

        # The first receive times out under the time-skipping server. The loop
        # should re-enter recv and expose the channel as open again.
        await asyncio.sleep(2)
        await _wait_for(_parked_after_timeout)

        await handle.execute_update("send", {"channel": "in", "value": "after"})

        async def _emitted():
            snap = await handle.query("state")
            return len(snap.get("emitted", {}).get("out", [])) >= 1

        await _wait_for(_emitted)
        snap = await handle.query("state")
        emits = snap["emitted"]["out"]
        assert [e["payload"]["echo"] for e in emits] == ["after"], snap
        assert [e["payload"]["turn"] for e in emits] == [1], snap

        await handle.execute_update("close", {})
        await handle.result()


# --------------------------------------------------------------------------- #
# 4. ChannelFull rejection on a bounded buffer.
# --------------------------------------------------------------------------- #
async def _channel_full(env):
    store = InMemorySessionStore(empty_value=0)
    fr, session = _frozen_session()
    tq = "ca-session-full"
    worker = _build_worker(env, tq, store)
    async with worker:
        sid = f"session-full-{uuid.uuid4()}"
        # capacity=1: with the loop parked consuming exactly one at a time, a
        # burst eventually overflows the bounded inbox and the Update rejects.
        handle = await env.client.start_workflow(
            SessionWorkflow.run,
            SessionInput(
                session_id=sid,
                flow_json=fr.flow.to_json(),
                manifest_json=manifest_to_json(fr.manifest),
                init=0,
                in_channel="in",
                out_channel="out",
                policy=ExecutionPolicy().to_json(),
                channel_capacity=1,
            ),
            id=sid,
            task_queue=tq,
        )
        rejected = False
        try:
            for i in range(50):
                await handle.execute_update("send", {"channel": "in", "value": i})
        except WorkflowFailureError as exc:
            cause = exc
            while cause is not None and not (
                isinstance(cause, ApplicationError) and cause.type == "ChannelFull"
            ):
                cause = cause.__cause__
            rejected = isinstance(cause, ApplicationError) and cause.type == "ChannelFull"
        except Exception as exc:  # pragma: no cover - update rejection class varies
            rejected = "ChannelFull" in repr(exc)
        assert rejected, "expected a ChannelFull rejection on the bounded buffer"

        await handle.execute_update("close", {})
        await handle.result()


# --------------------------------------------------------------------------- #
# 4b. Public Temporal facade: Agent.open + TemporalSessionHandle.events().
# --------------------------------------------------------------------------- #
async def _facade(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-facade"
    worker = _build_worker(env, tq, store)
    async with worker:
        session = _make_session_flow()
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=session,
            backend="temporal",
            client=env.client,
            session_id=f"session-facade-{uuid.uuid4()}",
            task_queue=tq,
        )

        ack1 = await handle.send("hi")
        ack2 = await handle.send("yo")
        assert ack1 == {"seq": 1, "channel": "in"}
        assert ack2 == {"seq": 2, "channel": "in"}

        async def _emitted():
            snap = await handle.state()
            return len(snap.get("emitted", {}).get("out", [])) >= 2

        await _wait_for(_emitted, attempts=50)

        agen = handle.events()
        emits = []
        for _ in range(2):
            ev = await asyncio.wait_for(agen.__anext__(), timeout=5)
            assert ev.is_emit
            emits.append(ev)

        assert [ev.seq for ev in emits] == [1, 2]
        assert [ev.payload["echo"] for ev in emits] == ["hi", "yo"]
        assert [ev.payload["turn"] for ev in emits] == [1, 2]

        await handle.close("done")
        closed = await asyncio.wait_for(agen.__anext__(), timeout=5)
        assert closed.is_closed
        assert closed.reason == "done"
        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()


# --------------------------------------------------------------------------- #
# 4c. Public Temporal facade: events() acks only after yielded delivery advances.
# --------------------------------------------------------------------------- #
async def _facade_ack_lags_delivery(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-facade-ack"
    worker = _build_worker(env, tq, store)
    async with worker:
        session = _make_session_flow()
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=session,
            backend="temporal",
            client=env.client,
            session_id=f"session-facade-ack-{uuid.uuid4()}",
            task_queue=tq,
        )

        await handle.send("hi")
        await handle.send("yo")

        async def _emitted():
            snap = await handle.state()
            return len(snap.get("emitted", {}).get("out", [])) >= 2

        await _wait_for(_emitted, attempts=50)

        agen = handle.events()
        first = await asyncio.wait_for(agen.__anext__(), timeout=5)
        assert first.is_emit
        assert first.seq == 1

        snap = await handle.state()
        emits = snap.get("emitted", {}).get("out", [])
        assert any(int(item["seq"]) == 1 for item in emits), snap
        assert snap.get("ack_cursors", {}).get("out", 0) < 1, snap

        second = await asyncio.wait_for(agen.__anext__(), timeout=5)
        assert second.is_emit
        assert second.seq == 2

        snap = await handle.state()
        emits = snap.get("emitted", {}).get("out", [])
        assert not any(int(item["seq"]) == 1 for item in emits), snap
        assert any(int(item["seq"]) == 2 for item in emits), snap
        assert snap.get("ack_cursors", {}).get("out", 0) >= 1, snap

        await handle.close("done")
        closed = await asyncio.wait_for(agen.__anext__(), timeout=5)
        assert closed.is_closed
        assert closed.reason == "done"


# --------------------------------------------------------------------------- #
# 4d. Durable send idempotency rejects conflicting payload reuse.
# --------------------------------------------------------------------------- #
async def _idempotency_conflict(env):
    store = InMemorySessionStore(empty_value=0)
    fr, session = _frozen_session()
    tq = "ca-session-idem"
    worker = _build_worker(env, tq, store)
    async with worker:
        sid = f"session-idem-{uuid.uuid4()}"
        handle = await env.client.start_workflow(
            SessionWorkflow.run,
            SessionInput(
                session_id=sid,
                flow_json=fr.flow.to_json(),
                manifest_json=manifest_to_json(fr.manifest),
                init=0,
                in_channel="in",
                out_channel="out",
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue=tq,
        )

        ack1 = await handle.execute_update(
            "send",
            {"channel": "in", "value": "a", "idempotency_key": "k1"},
        )
        ack2 = await handle.execute_update(
            "send",
            {"channel": "in", "value": "a", "idempotency_key": "k1"},
        )
        assert ack1 == {"seq": 1, "channel": "in"}
        assert ack2 == ack1

        with pytest.raises(Exception) as raised:
            await handle.execute_update(
                "send",
                {"channel": "in", "value": "DIFFERENT", "idempotency_key": "k1"},
            )

        cause = raised.value
        while cause is not None and not (
            isinstance(cause, ApplicationError) and cause.type == "ValidationError"
        ):
            cause = cause.__cause__
        assert isinstance(cause, ApplicationError), raised.value
        assert cause.type == "ValidationError"

        await handle.execute_update("close", {})
        await handle.result()


# --------------------------------------------------------------------------- #
# 5. FlowWorkflow rejects a frozen Op.LOOP (no channel machinery -> fail fast).
# --------------------------------------------------------------------------- #
async def _flowworkflow_rejects_loop(env):
    store = InMemorySessionStore(empty_value=0)
    fr, session = _frozen_session()
    tq = "ca-session-reject"
    worker = _build_worker(env, tq, store)
    async with worker:
        sid = f"reject-{uuid.uuid4()}"
        with pytest.raises(WorkflowFailureError) as raised:
            await env.client.execute_workflow(
                FlowWorkflow.run,
                FlowInput(
                    session_id=sid,
                    flow_json=fr.flow.to_json(),
                    manifest_json=manifest_to_json(fr.manifest),
                    input=None,
                    policy=ExecutionPolicy().to_json(),
                ),
                id=sid,
                task_queue=tq,
            )
        cause = raised.value.__cause__
        while cause is not None and not (
            isinstance(cause, ApplicationError) and cause.type == "ValidationError"
        ):
            cause = cause.__cause__
        assert isinstance(cause, ApplicationError), raised.value
        assert cause.type == "ValidationError"
        assert "LOOP" in str(cause)


# --------------------------------------------------------------------------- #
# 6. FlowWorkflow rejects nested Op.LOOP artifacts, not only root LOOP.
# --------------------------------------------------------------------------- #
async def _flowworkflow_rejects_nested_loop(env):
    store = InMemorySessionStore(empty_value=0)
    session = _make_session_flow()
    nested = seq(arr("test.session_identity_step"), session.body)
    fr = freeze(nested, McpSnapshot())
    tq = "ca-session-reject-nested"
    worker = _build_worker(env, tq, store)
    async with worker:
        sid = f"reject-nested-{uuid.uuid4()}"
        with pytest.raises(WorkflowFailureError) as raised:
            await env.client.execute_workflow(
                FlowWorkflow.run,
                FlowInput(
                    session_id=sid,
                    flow_json=fr.flow.to_json(),
                    manifest_json=manifest_to_json(fr.manifest),
                    input=None,
                    policy=ExecutionPolicy().to_json(),
                ),
                id=sid,
                task_queue=tq,
            )
        cause = raised.value.__cause__
        while cause is not None and not (
            isinstance(cause, ApplicationError) and cause.type == "ValidationError"
        ):
            cause = cause.__cause__
        assert isinstance(cause, ApplicationError), raised.value
        assert cause.type == "ValidationError"
        assert "LOOP" in str(cause)


# --------------------------------------------------------------------------- #
# Single environment, run all session scenarios.
# --------------------------------------------------------------------------- #
def test_durable_sessions():
    async def main():
        env = await WorkflowEnvironment.start_time_skipping()
        try:
            await _multi_turn(env)
            await _queries(env)
            await _carrier_survives_continue_as_new(env)
            await _recv_timeout_keeps_session_alive(env)
            await _channel_full(env)
            await _facade(env)
            await _facade_ack_lags_delivery(env)
            await _idempotency_conflict(env)
            await _flowworkflow_rejects_loop(env)
            await _flowworkflow_rejects_nested_loop(env)
        finally:
            await env.shutdown()

    asyncio.run(main())
