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

    from composable_agents import (
        Agent,
        CapabilityManifest,
        arr,
        call,
        freeze,
        manifest_to_json,
        mcp,
        seq,
    )
    from composable_agents.contracts import McpAnnotations
    from composable_agents.derived import recv as recv_leaf
    from composable_agents.errors import ValidationError
    from composable_agents.errors import ComposableAgentsError, SessionTurnError
    from composable_agents.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec
    from composable_agents.session import SessionEvent, scan
    from composable_agents.execution.activities import WorkerContext, configure
    from composable_agents.execution.harness import (
        ExecutionPolicy,
        FlowWorkflow,
        FlowInput,
        SessionWorkflow,
        SessionInput,
        TemporalSessionHandle,
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


def _nonfatal_or_echo(value):
    if value["msg"] == "fail":
        raise SessionTurnError("try again", fatal=False)
    return _echo_step(value)


register_pure("test.session_nonfatal_or_echo", _nonfatal_or_echo)


def _fatal_step(value):
    del value
    raise SessionTurnError("fatal turn", fatal=True)


register_pure("test.session_fatal_step", _fatal_step)


def _make_session_flow():
    # scan(turn, init) where turn = recv -> arr(step). The scan marks the LOOP
    # ``split`` so the driver splits the 2-tuple into (carrier, emit).
    turn = seq(recv_leaf("in"), arr("test.session_echo_step"))
    return scan(turn, init=0, in_channel="in", out_channel="out")


def _make_timeout_session_flow():
    turn = seq(recv_leaf("in", timeout_s=1), arr("test.session_echo_step"))
    return scan(turn, init=0, in_channel="in", out_channel="out")


def _make_nonfatal_session_flow():
    turn = seq(recv_leaf("in"), arr("test.session_nonfatal_or_echo"))
    return scan(turn, init=0, in_channel="in", out_channel="out")


def _make_fatal_session_flow():
    turn = seq(recv_leaf("in"), arr("test.session_fatal_step"))
    return scan(turn, init=0, in_channel="in", out_channel="out")


def _frozen_session():
    session = _make_session_flow()
    fr = freeze(session.body, McpSnapshot())
    return fr, session


def _frozen_timeout_session():
    session = _make_timeout_session_flow()
    fr = freeze(session.body, McpSnapshot())
    return fr, session


def _call_session(tool="echo"):
    turn = seq(recv_leaf("in"), call(mcp("srv", tool)))
    return scan(turn, init=0, in_channel="in", out_channel="out")


async def _wait_for(predicate, *, attempts=100):
    for _ in range(attempts):
        if await predicate():
            return
        await asyncio.sleep(0.05)
    assert await predicate()


def _event_contract_tuple(event: SessionEvent):
    if event.is_turn:
        return ("turn", event.turn, None, None, None)
    if event.is_emit:
        return ("emit", None, event.seq, event.payload, None)
    if event.is_error:
        return ("error", None, None, event.reason, event.fatal)
    return (event.kind, None, None, event.reason, None)


def _expected_echo_event_contract(reason="done"):
    return [
        ("turn", "started", None, None, None),
        ("emit", None, 1, {"echo": "a", "turn": 1}, None),
        ("turn", "done", None, None, None),
        ("turn", "started", None, None, None),
        ("emit", None, 2, {"echo": "b", "turn": 2}, None),
        ("turn", "done", None, None, None),
        ("closed", None, None, reason, None),
    ]


async def _collect_two_turn_contract(handle):
    agen = handle.events()
    await handle.send("a")
    await handle.send("b")
    events = [
        _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
        for _ in range(6)
    ]
    await handle.close("done")
    events.append(
        _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
    )
    return events


# --------------------------------------------------------------------------- #
# Worker helper.
# --------------------------------------------------------------------------- #
async def _mcp(server, tool, value, idempotency_key):
    assert idempotency_key
    assert server == "srv"
    if tool == "echo":
        return value
    if tool == "double":
        return value * 2
    raise ValueError(tool)


def _mcp_snapshot():
    ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    return McpSnapshot(
        servers={
            "srv": McpServerSnapshot(
                server="srv",
                version="1",
                tools={
                    name: McpToolSpec(input_schema={}, annotations=ann)
                    for name in ("echo", "double")
                },
            )
        }
    )


def _mcp_caps(*, tools=None, budget=None):
    return CapabilityManifest.from_dict(
        {
            "tools": list(tools or []),
            "budget": budget,
        }
    )


def _agent_with_mcp_caps(caps):
    agent = Agent("test-model", llm=None)
    agent._snapshot = _mcp_snapshot()
    agent._capabilities = caps
    return agent


def _build_worker(env, task_queue, store, *, mcp_call=None):
    ctx = WorkerContext(session_store=store, mcp_call=mcp_call)
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
        await env.client.start_workflow(
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

            async def _committed(index=index):
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

        async def _first_emitted():
            snap = await handle.state()
            return len(snap.get("emitted", {}).get("out", [])) >= 1

        await _wait_for(_first_emitted, attempts=200)
        ack2 = await handle.send("yo")
        assert ack1 == {"seq": 1, "channel": "in"}
        assert ack2 == {"seq": 2, "channel": "in"}

        async def _emitted():
            snap = await handle.state()
            return len(snap.get("emitted", {}).get("out", [])) >= 2

        await _wait_for(_emitted, attempts=200)

        agen = handle.events()
        events = [
            _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
            for _ in range(6)
        ]

        assert events == [
            ("turn", "started", None, None, None),
            ("emit", None, 1, {"echo": "hi", "turn": 1}, None),
            ("turn", "done", None, None, None),
            ("turn", "started", None, None, None),
            ("emit", None, 2, {"echo": "yo", "turn": 2}, None),
            ("turn", "done", None, None, None),
        ]

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

        async def _event_log_has_emit():
            records = await handle._wfhandle.query("events")
            return any(item.get("kind") == "emit" for item in records)

        await _wait_for(_event_log_has_emit, attempts=200)

        agen = handle.events()
        first = await asyncio.wait_for(agen.__anext__(), timeout=5)
        assert first == SessionEvent.turn_started()

        events = await handle._wfhandle.query("events")
        assert any(int(item["eseq"]) == 1 for item in events), events

        second = await asyncio.wait_for(agen.__anext__(), timeout=5)
        assert second.is_emit
        assert second.seq == 1

        events = await handle._wfhandle.query("events")
        assert not any(int(item["eseq"]) == 1 for item in events), events
        assert any(
            int(item["eseq"]) == 2 and item.get("kind") == "emit"
            for item in events
        ), events

        await handle.close("done")
        remaining = []
        while True:
            ev = await asyncio.wait_for(agen.__anext__(), timeout=5)
            remaining.append(ev)
            if ev.is_closed:
                break
        assert any(ev == SessionEvent.turn_done() for ev in remaining)
        assert remaining[-1].reason == "done"


# --------------------------------------------------------------------------- #
# 4cd. Backend-agnostic SessionEvent contract: local and Temporal match.
# --------------------------------------------------------------------------- #
async def _facade_event_contract_matches_local(env):
    local_agent = Agent("test-model", llm=None)
    local_handle = await local_agent.open(session=_make_session_flow(), backend="local")
    local_events = await _collect_two_turn_contract(local_handle)

    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-event-contract"
    worker = _build_worker(env, tq, store)
    async with worker:
        temporal_agent = Agent("test-model", llm=None)
        temporal_handle = await temporal_agent.open(
            session=_make_session_flow(),
            backend="temporal",
            client=env.client,
            session_id=f"session-event-contract-{uuid.uuid4()}",
            task_queue=tq,
        )
        temporal_events = await _collect_two_turn_contract(temporal_handle)

    assert local_events == temporal_events
    assert temporal_events == _expected_echo_event_contract()


# --------------------------------------------------------------------------- #
# 4ce. Temporal close quiesces the in-flight turn before Closed.
# --------------------------------------------------------------------------- #
async def _facade_close_flushes_in_flight_turn(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-close-flush"
    worker = _build_worker(env, tq, store)
    async with worker:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=_make_session_flow(),
            backend="temporal",
            client=env.client,
            session_id=f"session-close-flush-{uuid.uuid4()}",
            task_queue=tq,
        )
        agen = handle.events()

        await handle.send("a")
        await handle.close("done")

        events = [
            _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
            for _ in range(4)
        ]
        assert events == [
            ("turn", "started", None, None, None),
            ("emit", None, 1, {"echo": "a", "turn": 1}, None),
            ("turn", "done", None, None, None),
            ("closed", None, None, "done", None),
        ]


async def _facade_close_returns_after_quiescence(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-close-quiesce"
    worker = _build_worker(env, tq, store)
    async with worker:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=_make_session_flow(),
            backend="temporal",
            client=env.client,
            session_id=f"session-close-quiesce-{uuid.uuid4()}",
            task_queue=tq,
        )

        await handle.send("a")
        await handle.close("done")
        snap = await handle.state()
        assert snap["closed"] is True, snap
        assert snap["emitted"]["out"] == [
            {"seq": 1, "payload": {"echo": "a", "turn": 1}},
        ], snap

        records = await handle._wfhandle.query("events")
        assert records[-1]["kind"] == "closed", records


async def _facade_events_single_consumer(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-single-events"
    worker = _build_worker(env, tq, store)
    async with worker:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=_make_session_flow(),
            backend="temporal",
            client=env.client,
            session_id=f"session-single-events-{uuid.uuid4()}",
            task_queue=tq,
        )
        handle.events()
        with pytest.raises(ComposableAgentsError, match="single-consumer"):
            handle.events()
        await handle.close("done")


async def _facade_output_capacity_progresses_with_event_ack(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-output-capacity"
    worker = _build_worker(env, tq, store)
    async with worker:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=_make_session_flow(),
            backend="temporal",
            client=env.client,
            session_id=f"session-output-capacity-{uuid.uuid4()}",
            task_queue=tq,
            channel_capacity=1,
        )
        agen = handle.events()

        await handle.send("a")
        first = [
            _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
            for _ in range(3)
        ]
        assert first == [
            ("turn", "started", None, None, None),
            ("emit", None, 1, {"echo": "a", "turn": 1}, None),
            ("turn", "done", None, None, None),
        ]

        await handle.send("b")
        second = [
            _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
            for _ in range(3)
        ]
        assert second == [
            ("turn", "started", None, None, None),
            ("emit", None, 2, {"echo": "b", "turn": 2}, None),
            ("turn", "done", None, None, None),
        ]

        snap = await handle.state()
        assert len(snap.get("emitted", {}).get("out", [])) <= 1, snap
        await handle.close("done")
        closed = await asyncio.wait_for(agen.__anext__(), timeout=5)
        assert closed == SessionEvent.closed("done")


async def _facade_carried_event_log_is_deterministic(env):
    store = InMemorySessionStore(empty_value=0)
    fr, session = _frozen_session()
    tq = "ca-session-event-log-can"
    worker = _build_worker(env, tq, store)
    async with worker:
        sid = f"session-event-log-can-{uuid.uuid4()}"
        await env.client.start_workflow(
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

        def _committed_count():
            return sum(len(revs) for revs in store._revisions.values())

        events = []
        for index, word in enumerate(("a", "b", "c"), start=1):
            chain = env.client.get_workflow_handle(sid)
            await chain.execute_update("send", {"channel": "in", "value": word})

            async def _committed(index=index):
                return _committed_count() >= index

            await _wait_for(_committed, attempts=400)

        public = TemporalSessionHandle(env.client.get_workflow_handle(sid))
        agen = public.events()
        for _ in range(9):
            events.append(
                _event_contract_tuple(
                    await asyncio.wait_for(agen.__anext__(), timeout=5)
                )
            )
        await public.close("done")
        events.append(
            _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
        )

        assert events == [
            ("turn", "started", None, None, None),
            ("emit", None, 1, {"echo": "a", "turn": 1}, None),
            ("turn", "done", None, None, None),
            ("turn", "started", None, None, None),
            ("emit", None, 2, {"echo": "b", "turn": 2}, None),
            ("turn", "done", None, None, None),
            ("turn", "started", None, None, None),
            ("emit", None, 3, {"echo": "c", "turn": 3}, None),
            ("turn", "done", None, None, None),
            ("closed", None, None, "done", None),
        ]


async def _facade_nonfatal_turn_error_books_and_proceeds(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-nonfatal"
    worker = _build_worker(env, tq, store)
    async with worker:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=_make_nonfatal_session_flow(),
            backend="temporal",
            client=env.client,
            session_id=f"session-nonfatal-{uuid.uuid4()}",
            task_queue=tq,
        )
        agen = handle.events()

        await handle.send("fail")
        first = [
            _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
            for _ in range(3)
        ]
        assert first == [
            ("turn", "started", None, None, None),
            ("error", None, None, "try again", False),
            ("turn", "done", None, None, None),
        ]
        snap = await handle.state()
        assert snap["carrier"] == 0, snap

        await handle.send("ok")
        second = [
            _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
            for _ in range(3)
        ]
        assert second == [
            ("turn", "started", None, None, None),
            ("emit", None, 1, {"echo": "ok", "turn": 1}, None),
            ("turn", "done", None, None, None),
        ]
        await handle.close("done")
        assert await asyncio.wait_for(agen.__anext__(), timeout=5) == SessionEvent.closed("done")


async def _facade_fatal_turn_error_appends_closed(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-fatal"
    worker = _build_worker(env, tq, store)
    async with worker:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=_make_fatal_session_flow(),
            backend="temporal",
            client=env.client,
            session_id=f"session-fatal-{uuid.uuid4()}",
            task_queue=tq,
        )
        agen = handle.events()

        await handle.send("boom")
        events = [
            _event_contract_tuple(await asyncio.wait_for(agen.__anext__(), timeout=5))
            for _ in range(3)
        ]
        assert events == [
            ("turn", "started", None, None, None),
            ("error", None, None, "fatal turn", True),
            ("closed", None, None, "fatal turn", None),
        ]


def _find_application_error(exc, *, error_type):
    cause = exc
    while cause is not None and not (
        isinstance(cause, ApplicationError) and cause.type == error_type
    ):
        cause = cause.__cause__
    return cause


def test_session_rehydrate_restamps_pre_rehydrate_pending_items():
    wf = SessionWorkflow()
    wf._pending = {
        "in": [
            {"seq": 1, "value": "late", "idempotency_key": "late-key"},
        ]
    }
    wf._seq_cursors = {"in:in": 1}
    wf._idempotency_index = {"in": {"late-key": 1}}
    wf._idempotency_fp = {"in": {"late-key": "late-fp"}}

    carried = [{"seq": seq, "value": f"old-{seq}"} for seq in range(1, 6)]
    wf._rehydrate(
        SessionInput(
            session_id="s",
            flow_json={},
            manifest_json={},
            init=None,
            inbox={"in": carried},
            seq_cursors={"in:in": 5},
            idempotency_index={},
            idempotency_fp={},
        )
    )

    pending = wf._pending["in"]
    assert [item["value"] for item in pending] == [
        "old-1",
        "old-2",
        "old-3",
        "old-4",
        "old-5",
        "late",
    ]
    assert [item["seq"] for item in pending] == [1, 2, 3, 4, 5, 6]
    assert wf._seq_cursors["in:in"] == 6
    assert wf._idempotency_index["in"]["late-key"] == 6


# --------------------------------------------------------------------------- #
# 4ca. Public Temporal facade enforces maxCalls across session turns.
# --------------------------------------------------------------------------- #
async def _facade_max_calls_denies_second_turn(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-guards-max"
    worker = _build_worker(env, tq, store, mcp_call=_mcp)
    caps = _mcp_caps(
        tools=[
            {
                "name": "srv/echo",
                "effect": "read",
                "idempotency": "native",
                "maxCalls": 1,
            }
        ],
        budget={"cost": 1000},
    )
    async with worker:
        agent = _agent_with_mcp_caps(caps)
        handle = await agent.open(
            session=_call_session("echo"),
            backend="temporal",
            client=env.client,
            session_id=f"session-guard-max-{uuid.uuid4()}",
            task_queue=tq,
        )

        await handle.send("first")

        async def _parked_again():
            recvs = await handle.open_receives()
            return any(r["channel"] == "in" and int(r["seq"]) >= 2 for r in recvs)

        await _wait_for(_parked_again, attempts=100)
        await handle.send("second", idempotency_key="guard-max-2")

        with pytest.raises(WorkflowFailureError) as raised:
            await handle._wfhandle.result()
        cause = _find_application_error(raised.value, error_type="CapabilityDenied")
        assert isinstance(cause, ApplicationError), raised.value
        assert "maxCalls=1" in str(cause)


# --------------------------------------------------------------------------- #
# 4cb. Public Temporal facade closes the session when its budget is exceeded.
# --------------------------------------------------------------------------- #
async def _facade_budget_closes_over_budget(env):
    store = InMemorySessionStore(empty_value=0)
    tq = "ca-session-guards-budget"
    worker = _build_worker(env, tq, store, mcp_call=_mcp)
    caps = _mcp_caps(
        tools=[
            {
                "name": "srv/echo",
                "effect": "read",
                "idempotency": "native",
            }
        ],
        budget={"cost": 0.5},
    )
    async with worker:
        agent = _agent_with_mcp_caps(caps)
        handle = await agent.open(
            session=_call_session("echo"),
            backend="temporal",
            client=env.client,
            session_id=f"session-guard-budget-{uuid.uuid4()}",
            task_queue=tq,
        )

        await handle.send("spend", idempotency_key="guard-budget-1")
        await asyncio.wait_for(handle._wfhandle.result(), timeout=10)
        snap = await handle.state()
        assert snap["closed"] is True, snap
        assert snap["close_reason"] == "over_budget", snap


# --------------------------------------------------------------------------- #
# 4cc. Public Temporal facade rejects ungranted session calls at deploy time.
# --------------------------------------------------------------------------- #
async def _facade_ungranted_tool_denied_at_open(env):
    caps = _mcp_caps(
        tools=[
            {
                "name": "srv/double",
                "effect": "read",
                "idempotency": "native",
            }
        ],
        budget={"cost": 1000},
    )
    agent = _agent_with_mcp_caps(caps)
    with pytest.raises(ValidationError):
        await agent.open(
            session=_call_session("echo"),
            backend="temporal",
            client=env.client,
            session_id=f"session-guard-deny-{uuid.uuid4()}",
            task_queue="ca-session-guards-deny",
        )


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
            await _facade_event_contract_matches_local(env)
            await _facade_close_flushes_in_flight_turn(env)
            await _facade_close_returns_after_quiescence(env)
            await _facade_events_single_consumer(env)
            await _facade_output_capacity_progresses_with_event_ack(env)
            await _facade_carried_event_log_is_deterministic(env)
            await _facade_nonfatal_turn_error_books_and_proceeds(env)
            await _facade_fatal_turn_error_appends_closed(env)
            await _facade_max_calls_denies_second_turn(env)
            await _facade_budget_closes_over_budget(env)
            await _facade_ungranted_tool_denied_at_open(env)
            await _idempotency_conflict(env)
            await _flowworkflow_rejects_loop(env)
            await _flowworkflow_rejects_nested_loop(env)
        finally:
            await env.shutdown()

    asyncio.run(main())
