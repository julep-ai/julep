"""Trajectory plane foundation tests."""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import pytest

from julep.execution.blobstore import InMemoryBlobStore, content_ref
from julep.trajectory import (
    InMemoryTrajectoryStore,
    PostgresTrajectoryStore,
    TrajectoryRun,
    TrajectoryStep,
    TrajectoryValue,
    _best_effort,
    trajectory_best_effort_failures,
)


def _run(
    run_id: str = "run-root",
    *,
    root_run_id: str = "run-root",
    parent_run_id: str | None = None,
    segment_seq: int = 0,
    status: str = "running",
    logical_seq: int = 1,
) -> TrajectoryRun:
    return TrajectoryRun(
        run_id=run_id,
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        backend="memory",
        session_id="session-1",
        segment_seq=segment_seq,
        controller=None,
        flow_ref=None,
        status=status,
        policy=None,
        started_ts=1000.0 + segment_seq,
        finished_ts=None,
        logical_seq=logical_seq,
    )


def _step(
    step_id: str,
    *,
    run_id: str = "run-root",
    root_run_id: str = "run-root",
    logical_seq: int,
    causes: tuple[str, ...] = (),
    input_ref: str | None = None,
    output_ref: str | None = None,
    attrs: dict[str, Any] | None = None,
) -> TrajectoryStep:
    return TrajectoryStep(
        step_id=step_id,
        run_id=run_id,
        root_run_id=root_run_id,
        cid=f"cid-{step_id}",
        node_id=f"node-{step_id}",
        op="call",
        kind="native",
        causes=causes,
        status="did",
        input_ref=input_ref,
        output_ref=output_ref,
        error=None,
        cost=None,
        attrs=attrs or {},
        logical_seq=logical_seq,
    )


def _value(
    ref: str,
    *,
    root_run_id: str = "run-root",
    step_id: str = "step-1",
    kind: str = "output",
    size: int | None = None,
) -> TrajectoryValue:
    return TrajectoryValue(
        ref=ref,
        root_run_id=root_run_id,
        step_id=step_id,
        kind=kind,
        size=size,
    )


async def _put_json_blob(store: InMemoryBlobStore, tenant: str, value: Any) -> str:
    data = json.dumps(value, sort_keys=True).encode()
    ref = content_ref(tenant, data)
    assert await store.put(tenant, data) == ref
    return ref


def test_records_json_round_trip_camel_case_and_omit_none():
    run = _run()
    run_json = run.to_json()
    assert run_json["runId"] == "run-root"
    assert run_json["rootRunId"] == "run-root"
    assert run_json["sessionId"] == "session-1"
    assert run_json["segmentSeq"] == 0
    assert run_json["startedTs"] == 1000.0
    assert run_json["logicalSeq"] == 1
    assert "parentRunId" not in run_json
    assert "controller" not in run_json
    assert "flowRef" not in run_json
    assert "policy" not in run_json
    assert "finishedTs" not in run_json
    assert TrajectoryRun.from_json(run_json) == run

    step = _step(
        "step-1",
        logical_seq=2,
        causes=("cause-1", "cause-2"),
        attrs={},
    )
    step_json = step.to_json()
    assert step_json["stepId"] == "step-1"
    assert step_json["runId"] == "run-root"
    assert step_json["rootRunId"] == "run-root"
    assert step_json["nodeId"] == "node-step-1"
    assert step_json["causes"] == ["cause-1", "cause-2"]
    assert step_json["attrs"] == {}
    assert step_json["logicalSeq"] == 2
    assert "inputRef" not in step_json
    assert "outputRef" not in step_json
    assert "error" not in step_json
    assert "cost" not in step_json
    assert TrajectoryStep.from_json(step_json) == step

    value = _value("run-root/sha256:" + "a" * 64)
    value_json = value.to_json()
    assert value_json["rootRunId"] == "run-root"
    assert value_json["stepId"] == "step-1"
    assert "size" not in value_json
    assert TrajectoryValue.from_json(value_json) == value


def test_inmemory_steps_are_ordered_by_logical_seq():
    store = InMemoryTrajectoryStore()
    store.start_run(_run())
    store.append_steps([
        _step("step-3", logical_seq=3),
        _step("step-1", logical_seq=1),
        _step("step-2", logical_seq=2),
    ])

    assert [step.step_id for step in store.list_trajectory_steps("run-root")] == [
        "step-1",
        "step-2",
        "step-3",
    ]


def test_inmemory_step_listing_stitches_child_runs_recursively():
    store = InMemoryTrajectoryStore()
    store.start_run(_run())
    store.start_run(_run(
        "run-child",
        root_run_id="run-root",
        parent_run_id="run-root",
        segment_seq=1,
        logical_seq=2,
    ))
    store.append_steps([
        _step("root-step", logical_seq=1),
        _step(
            "child-step",
            run_id="run-child",
            root_run_id="run-root",
            logical_seq=2,
        ),
    ])

    assert [step.step_id for step in store.list_trajectory_steps("run-root")] == [
        "root-step",
        "child-step",
    ]
    assert [
        step.step_id
        for step in store.list_trajectory_steps("run-root", include_children=False)
    ] == ["root-step"]


def test_export_trajectory_jsonl_keeps_value_refs_unhydrated():
    store = InMemoryTrajectoryStore()
    ref = "run-root/sha256:" + "b" * 64
    store.start_run(_run())
    store.append_steps([_step("step-1", logical_seq=1, output_ref=ref)])
    store.record_values([_value(ref, step_id="step-1", size=21)])

    lines = store.export_trajectory_jsonl("run-root")
    assert lines
    for line in lines:
        json.loads(line)

    rendered = "\n".join(lines)
    assert ref in rendered
    assert "secret payload" not in rendered


class _CountingBlobStore:
    def __init__(self, inner: InMemoryBlobStore) -> None:
        self.inner = inner
        self.get_count = 0
        self.refs: list[str] = []

    async def get(self, tenant: str, ref: str) -> bytes:
        self.get_count += 1
        self.refs.append(ref)
        return await self.inner.get(tenant, ref)


def test_export_trajectory_jsonl_hydrated_resolves_each_unique_ref_once():
    async def scenario() -> None:
        blob_store = InMemoryBlobStore()
        first = await _put_json_blob(
            blob_store,
            "run-root",
            {"message": "first payload"},
        )
        second = await _put_json_blob(
            blob_store,
            "run-root",
            {"message": "second payload"},
        )
        counting = _CountingBlobStore(blob_store)

        store = InMemoryTrajectoryStore()
        store.start_run(_run())
        store.append_steps([
            _step("step-1", logical_seq=1, input_ref=first, output_ref=second),
            _step("step-2", logical_seq=2, input_ref=first, output_ref=second),
            _step("step-3", logical_seq=3, output_ref=second),
        ])
        store.record_values([
            _value(first, step_id="step-1", kind="input"),
            _value(second, step_id="step-1", kind="output"),
            _value(first, step_id="step-2", kind="input"),
            _value(second, step_id="step-2", kind="output"),
            _value(second, step_id="step-3", kind="output"),
        ])

        lines = await store.export_trajectory_jsonl_hydrated("run-root", counting)

        rendered = "\n".join(lines)
        assert "first payload" in rendered
        assert "second payload" in rendered
        assert counting.get_count == 2
        assert sorted(counting.refs) == sorted([first, second])

    asyncio.run(scenario())


def test_postgres_store_raises_loudly_without_execute():
    store = PostgresTrajectoryStore(execute=None)

    with pytest.raises(RuntimeError, match="PostgresTrajectoryStore needs an `execute` callable"):
        store.start_run(_run())
    with pytest.raises(RuntimeError, match="PostgresTrajectoryStore needs an `execute` callable"):
        store.append_steps([_step("step-1", logical_seq=1)])
    with pytest.raises(RuntimeError, match="PostgresTrajectoryStore needs an `execute` callable"):
        store.record_values([_value("run-root/sha256:" + "c" * 64)])


def test_postgres_store_insert_sql_and_camel_case_params():
    calls: list[tuple[str, dict[str, Any]]] = []

    def execute(sql: str, params: dict[str, Any]) -> None:
        calls.append((sql, params))

    store = PostgresTrajectoryStore(execute=execute)
    run = _run(parent_run_id="parent-run", status="continued")
    step = _step(
        "step-1",
        logical_seq=2,
        causes=("cause-1",),
        attrs={"shape": "turn"},
    )
    value = _value("run-root/sha256:" + "d" * 64, size=99)

    store.start_run(run)
    store.append_steps([step])
    store.record_values([value])

    assert calls[0][0] == store.INSERT_RUN_SQL
    assert calls[0][1]["runId"] == run.run_id
    assert calls[0][1]["rootRunId"] == run.root_run_id
    assert calls[0][1]["parentRunId"] == "parent-run"
    assert calls[0][1]["controller"] is None
    assert calls[0][1]["flowRef"] is None
    assert calls[0][1]["policy"] is None
    assert calls[0][1]["finishedTs"] is None
    assert calls[1][0] == store.INSERT_STEP_SQL
    assert calls[1][1]["stepId"] == step.step_id
    assert calls[1][1]["runId"] == step.run_id
    assert calls[1][1]["rootRunId"] == step.root_run_id
    assert calls[1][1]["causes"] == ["cause-1"]
    assert isinstance(calls[1][1]["attrs"], dict)
    assert calls[1][1]["inputRef"] is None
    assert calls[1][1]["outputRef"] is None
    assert calls[1][1]["error"] is None
    assert calls[1][1]["cost"] is None
    assert calls[2][0] == store.INSERT_VALUE_SQL
    assert calls[2][1]["ref"] == value.ref
    assert calls[2][1]["rootRunId"] == value.root_run_id
    assert calls[2][1]["stepId"] == value.step_id
    assert calls[2][1]["kind"] == value.kind
    assert calls[2][1]["size"] == 99

    for _, params in calls:
        assert all("_" not in key for key in params)


def test_postgres_store_sets_optional_placeholders_so_no_keyerror():
    def execute(sql: str, params: dict[str, Any]) -> None:
        for name in re.findall(r"%\((\w+)\)s", sql):
            if name not in params:
                raise KeyError(name)

    store = PostgresTrajectoryStore(execute=execute)

    store.start_run(_run())
    store.append_steps([_step("step-1", logical_seq=1)])
    store.record_values([_value("run-root/sha256:" + "e" * 64)])


def test_postgres_store_list_steps_stitches_child_runs():
    root = _run()
    child = _run(
        "run-child",
        root_run_id="run-root",
        parent_run_id="run-root",
        segment_seq=1,
        logical_seq=2,
    )
    root_step = _step("root-step", logical_seq=1)
    child_step = _step(
        "child-step",
        run_id="run-child",
        root_run_id="run-root",
        logical_seq=2,
    )
    run_rows = [
        {
            "run_id": root.run_id,
            "root_run_id": root.root_run_id,
            "parent_run_id": root.parent_run_id,
            "backend": root.backend,
            "session_id": root.session_id,
            "segment_seq": root.segment_seq,
            "controller": root.controller,
            "flow_ref": root.flow_ref,
            "status": root.status,
            "policy": root.policy,
            "started_ts": root.started_ts,
            "finished_ts": root.finished_ts,
            "logical_seq": root.logical_seq,
        },
        {
            "run_id": child.run_id,
            "root_run_id": child.root_run_id,
            "parent_run_id": child.parent_run_id,
            "backend": child.backend,
            "session_id": child.session_id,
            "segment_seq": child.segment_seq,
            "controller": child.controller,
            "flow_ref": child.flow_ref,
            "status": child.status,
            "policy": child.policy,
            "started_ts": child.started_ts,
            "finished_ts": child.finished_ts,
            "logical_seq": child.logical_seq,
        },
    ]
    step_rows = [
        {
            "step_id": root_step.step_id,
            "run_id": root_step.run_id,
            "root_run_id": root_step.root_run_id,
            "cid": root_step.cid,
            "node_id": root_step.node_id,
            "op": root_step.op,
            "kind": root_step.kind,
            "causes": list(root_step.causes),
            "status": root_step.status,
            "input_ref": root_step.input_ref,
            "output_ref": root_step.output_ref,
            "error": root_step.error,
            "cost": root_step.cost,
            "attrs": root_step.attrs,
            "logical_seq": root_step.logical_seq,
        },
        {
            "step_id": child_step.step_id,
            "run_id": child_step.run_id,
            "root_run_id": child_step.root_run_id,
            "cid": child_step.cid,
            "node_id": child_step.node_id,
            "op": child_step.op,
            "kind": child_step.kind,
            "causes": list(child_step.causes),
            "status": child_step.status,
            "input_ref": child_step.input_ref,
            "output_ref": child_step.output_ref,
            "error": child_step.error,
            "cost": child_step.cost,
            "attrs": child_step.attrs,
            "logical_seq": child_step.logical_seq,
        },
    ]

    def fetch(sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        if "trajectory_runs" in sql:
            if "rootRunId" in params:
                return [
                    row for row in run_rows if row["root_run_id"] == params["rootRunId"]
                ]
            if "runId" in params:
                return [row for row in run_rows if row["run_id"] == params["runId"]]
        if "trajectory_steps" in sql:
            if "runIds" in params:
                return [
                    row for row in step_rows if row["run_id"] in set(params["runIds"])
                ]
            if "runId" in params:
                return [row for row in step_rows if row["run_id"] == params["runId"]]
        raise AssertionError(f"unexpected query: {sql} {params}")

    store = PostgresTrajectoryStore(fetch=fetch)

    assert [
        step.step_id
        for step in store.list_trajectory_steps("run-root", include_children=True)
    ] == ["root-step", "child-step"]
    assert [
        step.step_id
        for step in store.list_trajectory_steps("run-root", include_children=False)
    ] == ["root-step"]


def test_best_effort_returns_success_and_counts_swallowed_failures():
    before = trajectory_best_effort_failures()

    assert _best_effort(lambda: "ok") == "ok"
    assert trajectory_best_effort_failures() == before

    def boom() -> None:
        raise ValueError("broken")

    assert _best_effort(boom) is None
    assert trajectory_best_effort_failures() == before + 1
