"""The trajectory plane (cross-run causal history, training-data plane).

The projection plane in :mod:`composable_agents.projection` is the per-run
blueprint and observability view: a pomset of planned/did/failed activations
that explains how one workflow segment walked the IR.

::

    projection plane                         trajectory plane
    ----------------                         ----------------
    one run / segment                        root run + child runs
    IR activation pomset                     stitched causal history
    observability + debugging               exportable training examples
    values are refs into a store             values are refs into BlobStore

Trajectory capture is intentionally best-effort and belongs only in the
effect/sink layer. It must never be part of ``interpret()`` or workflow
``run()`` logic: replay determinism depends on workflow code deriving the same
decisions without consulting an observational sink. Large values are persisted
through the existing ``putBlob`` path (canonical JSON in
:mod:`composable_agents.execution.effects`) keyed by ``tenant == root_run_id``;
this module records only those content-addressed refs and does not invent a
second addressing scheme.

``root_run_id`` is the root ``session_id``. ``segment_seq`` carries across
``continue_as_new`` and DBOS segments in the same spirit as principal and
``call_counts``: it is run context threaded forward, not sink state queried
back into deterministic execution.

The store is pluggable. :class:`InMemoryTrajectoryStore` backs tests and local
inspection, while :class:`PostgresTrajectoryStore` is the dependency-free
production seam. The host applies the SQL in
:mod:`composable_agents.execution.trajectory_sql`; this module stays pure
Python and importable without a database driver.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Iterable, Optional, Protocol, TypeVar

logger = logging.getLogger("composable_agents.trajectory")

_BEST_EFFORT_FAILURES = 0
T = TypeVar("T")


def trajectory_best_effort_failures() -> int:
    return _BEST_EFFORT_FAILURES


def _best_effort(fn: Callable[[], T]) -> Optional[T]:
    global _BEST_EFFORT_FAILURES
    try:
        return fn()
    except Exception:
        _BEST_EFFORT_FAILURES += 1
        logger.warning("trajectory best-effort operation failed", exc_info=True)
        return None


@dataclass(frozen=True)
class TrajectoryRun:
    run_id: str
    root_run_id: str
    parent_run_id: Optional[str] = None
    backend: str = "memory"
    session_id: str = ""
    segment_seq: int = 0
    controller: Optional[str] = None
    flow_ref: Optional[str] = None
    status: str = "running"
    policy: Optional[dict[str, Any]] = None
    started_ts: float = 0.0
    finished_ts: Optional[float] = None
    logical_seq: int = 0

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "runId": self.run_id,
            "rootRunId": self.root_run_id,
            "backend": self.backend,
            "sessionId": self.session_id,
            "segmentSeq": self.segment_seq,
            "status": self.status,
            "startedTs": self.started_ts,
            "logicalSeq": self.logical_seq,
        }
        for key, value in (
            ("parentRunId", self.parent_run_id),
            ("controller", self.controller),
            ("flowRef", self.flow_ref),
            ("policy", self.policy),
            ("finishedTs", self.finished_ts),
        ):
            if value is not None:
                out[key] = value
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "TrajectoryRun":
        return TrajectoryRun(
            run_id=d["runId"] if "runId" in d else d["run_id"],
            root_run_id=d["rootRunId"] if "rootRunId" in d else d["root_run_id"],
            parent_run_id=d.get("parentRunId", d.get("parent_run_id")),
            backend=d.get("backend", "memory"),
            session_id=d.get("sessionId", d.get("session_id", "")),
            segment_seq=int(d.get("segmentSeq", d.get("segment_seq", 0))),
            controller=d.get("controller"),
            flow_ref=d.get("flowRef", d.get("flow_ref")),
            status=d.get("status", "running"),
            policy=d.get("policy"),
            started_ts=float(d.get("startedTs", d.get("started_ts", 0.0))),
            finished_ts=d.get("finishedTs", d.get("finished_ts")),
            logical_seq=int(d.get("logicalSeq", d.get("logical_seq", 0))),
        )


@dataclass(frozen=True)
class TrajectoryStep:
    step_id: str
    run_id: str
    root_run_id: str
    cid: str
    node_id: str
    op: str
    kind: str
    causes: tuple[str, ...] = ()
    status: str = "did"
    input_ref: Optional[str] = None
    output_ref: Optional[str] = None
    error: Optional[str] = None
    cost: Optional[float] = None
    attrs: dict[str, Any] = field(default_factory=dict)
    logical_seq: int = 0

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "stepId": self.step_id,
            "runId": self.run_id,
            "rootRunId": self.root_run_id,
            "cid": self.cid,
            "nodeId": self.node_id,
            "op": self.op,
            "kind": self.kind,
            "causes": list(self.causes),
            "status": self.status,
            "attrs": self.attrs,
            "logicalSeq": self.logical_seq,
        }
        for key, value in (
            ("inputRef", self.input_ref),
            ("outputRef", self.output_ref),
            ("error", self.error),
            ("cost", self.cost),
        ):
            if value is not None:
                out[key] = value
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "TrajectoryStep":
        return TrajectoryStep(
            step_id=d["stepId"] if "stepId" in d else d["step_id"],
            run_id=d["runId"] if "runId" in d else d["run_id"],
            root_run_id=d["rootRunId"] if "rootRunId" in d else d["root_run_id"],
            cid=d["cid"],
            node_id=d["nodeId"] if "nodeId" in d else d["node_id"],
            op=d["op"],
            kind=d["kind"],
            causes=tuple(d.get("causes", ())),
            status=d.get("status", "did"),
            input_ref=d.get("inputRef", d.get("input_ref")),
            output_ref=d.get("outputRef", d.get("output_ref")),
            error=d.get("error"),
            cost=d.get("cost"),
            attrs=dict(d.get("attrs") or {}),
            logical_seq=int(d.get("logicalSeq", d.get("logical_seq", 0))),
        )


@dataclass(frozen=True)
class TrajectoryValue:
    ref: str
    root_run_id: str
    step_id: str
    kind: str
    size: Optional[int] = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "ref": self.ref,
            "rootRunId": self.root_run_id,
            "stepId": self.step_id,
            "kind": self.kind,
        }
        if self.size is not None:
            out["size"] = self.size
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "TrajectoryValue":
        return TrajectoryValue(
            ref=d["ref"],
            root_run_id=d["rootRunId"] if "rootRunId" in d else d["root_run_id"],
            step_id=d["stepId"] if "stepId" in d else d["step_id"],
            kind=d["kind"],
            size=d.get("size"),
        )


class TrajectorySink(Protocol):
    def start_run(self, run: TrajectoryRun) -> None: ...
    def append_steps(self, steps: list[TrajectoryStep]) -> None: ...
    def finish_run(self, run_id: str, status: str, finished_ts: float) -> None: ...
    def record_values(self, values: list[TrajectoryValue]) -> None: ...
    def get_trajectory_run(self, run_id: str) -> Optional[TrajectoryRun]: ...
    def list_trajectory_steps(
        self, run_id: str, include_children: bool = True
    ) -> list[TrajectoryStep]: ...
    def list_trajectory_values(
        self, run_id: str, refs: Optional[list[str]] = None
    ) -> list[TrajectoryValue]: ...
    def export_trajectory_jsonl(
        self, run_id: str, format: str = "supervised_turns"
    ) -> list[str]: ...
    async def export_trajectory_jsonl_hydrated(
        self, run_id: str, blob_store: Any, format: str = "supervised_turns"
    ) -> list[str]: ...


class ProjectionTrajectorySink:
    """Materialize structural trajectory steps from projection DID/FAILED events.

    This sink is fully best-effort because projection tee sinks propagate
    exceptions. Effect leaves are captured by the effect boundary, so ``prim``
    events are intentionally ignored here.
    """

    def __init__(
        self,
        sink: TrajectorySink,
        *,
        run_id: str,
        root_run_id: str,
        segment_seq: int,
        node_ops: dict[str, str],
    ) -> None:
        self._sink = sink
        self._run_id = run_id
        self._root_run_id = root_run_id
        self._segment_seq = segment_seq
        self._node_ops = node_ops

    def append(self, event: Any) -> None:
        def _append() -> None:
            from .projection import EventType

            if event.type not in (EventType.DID, EventType.FAILED):
                return
            op = self._node_ops.get(event.node)
            if op is None or op == "prim":
                return
            status = "did" if event.type == EventType.DID else "failed"
            step = TrajectoryStep(
                step_id=f"{self._run_id}:s{self._segment_seq}:{event.cid}",
                run_id=self._run_id,
                root_run_id=self._root_run_id,
                cid=event.cid,
                node_id=event.node,
                op=op,
                kind=op,
                causes=tuple(event.causes),
                status=status,
                cost=event.cost,
                error=event.error,
                attrs=dict(event.attrs or {}),
            )
            _best_effort(lambda: self._sink.append_steps([step]))

        _best_effort(_append)


class InMemoryTrajectoryStore:
    def __init__(self) -> None:
        self._runs: dict[str, TrajectoryRun] = {}
        self._steps: list[TrajectoryStep] = []
        self._values: list[TrajectoryValue] = []

    def start_run(self, run: TrajectoryRun) -> None:
        self._runs[run.run_id] = run

    def append_steps(self, steps: list[TrajectoryStep]) -> None:
        self._steps.extend(steps)

    def finish_run(self, run_id: str, status: str, finished_ts: float) -> None:
        run = self._runs.get(run_id)
        if run is not None:
            self._runs[run_id] = replace(run, status=status, finished_ts=finished_ts)

    def record_values(self, values: list[TrajectoryValue]) -> None:
        self._values.extend(values)

    def get_trajectory_run(self, run_id: str) -> Optional[TrajectoryRun]:
        return self._runs.get(run_id)

    def _descendant_run_ids(self, run_id: str) -> set[str]:
        seen = {run_id}
        frontier = [run_id]
        while frontier:
            current = frontier.pop()
            for child in self._runs.values():
                if child.parent_run_id == current and child.run_id not in seen:
                    seen.add(child.run_id)
                    frontier.append(child.run_id)
        return seen

    def list_trajectory_steps(
        self, run_id: str, include_children: bool = True
    ) -> list[TrajectoryStep]:
        target_runs = self._descendant_run_ids(run_id) if include_children else {run_id}
        return sorted(
            [step for step in self._steps if step.run_id in target_runs],
            key=lambda step: step.logical_seq,
        )

    def list_trajectory_values(
        self, run_id: str, refs: Optional[list[str]] = None
    ) -> list[TrajectoryValue]:
        step_ids = {
            step.step_id for step in self.list_trajectory_steps(run_id, include_children=True)
        }
        ref_filter = set(refs) if refs is not None else None
        values = [value for value in self._values if value.step_id in step_ids]
        if ref_filter is not None:
            values = [value for value in values if value.ref in ref_filter]
        return values

    def export_trajectory_jsonl(
        self, run_id: str, format: str = "supervised_turns"
    ) -> list[str]:
        if format != "supervised_turns":
            raise ValueError(f"unsupported trajectory export format: {format!r}")
        return [
            json.dumps(self._step_surface(step), sort_keys=True)
            for step in self.list_trajectory_steps(run_id, include_children=True)
        ]

    async def export_trajectory_jsonl_hydrated(
        self, run_id: str, blob_store: Any, format: str = "supervised_turns"
    ) -> list[str]:
        if format != "supervised_turns":
            raise ValueError(f"unsupported trajectory export format: {format!r}")

        from composable_agents.execution.blobstore import parse_ref

        steps = self.list_trajectory_steps(run_id, include_children=True)
        refs: set[str] = set()
        for step in steps:
            if step.input_ref is not None:
                refs.add(step.input_ref)
            if step.output_ref is not None:
                refs.add(step.output_ref)
        step_ids = {step.step_id for step in steps}
        for value in self._values:
            if value.step_id in step_ids:
                refs.add(value.ref)

        hydrated: dict[str, Any] = {}
        for ref in refs:
            tenant, _ = parse_ref(ref)
            hydrated[ref] = json.loads(await blob_store.get(tenant, ref))

        lines: list[str] = []
        for step in steps:
            surface = self._step_surface(step)
            if step.input_ref is not None:
                surface.pop("inputRef", None)
                surface["input"] = hydrated.get(step.input_ref)
            if step.output_ref is not None:
                surface.pop("outputRef", None)
                surface["output"] = hydrated.get(step.output_ref)
            lines.append(json.dumps(surface, sort_keys=True))
        return lines

    def _step_surface(self, step: TrajectoryStep) -> dict[str, Any]:
        out: dict[str, Any] = {
            "stepId": step.step_id,
            "runId": step.run_id,
            "rootRunId": step.root_run_id,
            "cid": step.cid,
            "nodeId": step.node_id,
            "op": step.op,
            "kind": step.kind,
            "causes": list(step.causes),
            "status": step.status,
            "attrs": step.attrs,
            "logicalSeq": step.logical_seq,
        }
        if step.input_ref is not None:
            out["inputRef"] = step.input_ref
        if step.output_ref is not None:
            out["outputRef"] = step.output_ref
        if step.error is not None:
            out["error"] = step.error
        if step.cost is not None:
            out["cost"] = step.cost
        return out


class PostgresTrajectoryStore:
    INSERT_RUN_SQL = (
        "INSERT INTO trajectory_runs "
        "(run_id, root_run_id, parent_run_id, backend, session_id, segment_seq, "
        "controller, flow_ref, status, policy, started_ts, finished_ts, logical_seq) "
        "VALUES (%(runId)s, %(rootRunId)s, %(parentRunId)s, %(backend)s, "
        "%(sessionId)s, %(segmentSeq)s, %(controller)s, %(flowRef)s, %(status)s, "
        "%(policy)s, %(startedTs)s, %(finishedTs)s, %(logicalSeq)s)"
    )
    INSERT_STEP_SQL = (
        "INSERT INTO trajectory_steps "
        "(step_id, run_id, root_run_id, cid, node_id, op, kind, causes, status, "
        "input_ref, output_ref, error, cost, attrs, logical_seq) "
        "VALUES (%(stepId)s, %(runId)s, %(rootRunId)s, %(cid)s, %(nodeId)s, "
        "%(op)s, %(kind)s, %(causes)s, %(status)s, %(inputRef)s, %(outputRef)s, "
        "%(error)s, %(cost)s, %(attrs)s, %(logicalSeq)s)"
    )
    INSERT_VALUE_SQL = (
        "INSERT INTO trajectory_values (ref, root_run_id, step_id, kind, size) "
        "VALUES (%(ref)s, %(rootRunId)s, %(stepId)s, %(kind)s, %(size)s)"
    )

    def __init__(
        self,
        execute: Optional[Callable[[str, dict[str, Any]], None]] = None,
        fetch: Optional[Callable[[str, dict[str, Any]], Iterable[dict[str, Any]]]] = None,
    ) -> None:
        self._execute = execute
        self._fetch = fetch
        self._buffer: list[Any] = []

    def _require_execute(self) -> None:
        if self._execute is None:
            raise RuntimeError(
                "PostgresTrajectoryStore needs an `execute` callable; inject a DB cursor from "
                "composable_agents.execution or use InMemoryTrajectoryStore in tests"
            )

    def _require_fetch(self) -> Callable[[str, dict[str, Any]], Iterable[dict[str, Any]]]:
        if self._fetch is None:
            raise RuntimeError(
                "PostgresTrajectoryStore needs a `fetch` callable; inject a DB cursor from "
                "composable_agents.execution or use InMemoryTrajectoryStore in tests"
            )
        return self._fetch

    def start_run(self, run: TrajectoryRun) -> None:
        self._require_execute()
        assert self._execute is not None
        row = run.to_json()
        row.setdefault("parentRunId", None)
        row.setdefault("controller", None)
        row.setdefault("flowRef", None)
        row.setdefault("policy", None)
        row.setdefault("finishedTs", None)
        self._execute(self.INSERT_RUN_SQL, row)
        self._buffer.append(run)

    def append_steps(self, steps: list[TrajectoryStep]) -> None:
        self._require_execute()
        assert self._execute is not None
        for step in steps:
            row = step.to_json()
            row.setdefault("inputRef", None)
            row.setdefault("outputRef", None)
            row.setdefault("error", None)
            row.setdefault("cost", None)
            self._execute(self.INSERT_STEP_SQL, row)
            self._buffer.append(step)

    def finish_run(self, run_id: str, status: str, finished_ts: float) -> None:
        self._require_execute()
        assert self._execute is not None
        self._execute(
            "UPDATE trajectory_runs SET status=%(status)s, finished_ts=%(finishedTs)s "
            "WHERE run_id=%(runId)s",
            {"runId": run_id, "status": status, "finishedTs": finished_ts},
        )

    def record_values(self, values: list[TrajectoryValue]) -> None:
        self._require_execute()
        assert self._execute is not None
        for value in values:
            row = value.to_json()
            row.setdefault("size", None)
            self._execute(self.INSERT_VALUE_SQL, row)
            self._buffer.append(value)

    def get_trajectory_run(self, run_id: str) -> Optional[TrajectoryRun]:
        rows = list(
            self._require_fetch()(
                "SELECT * FROM trajectory_runs WHERE run_id=%(runId)s",
                {"runId": run_id},
            )
        )
        if not rows:
            return None
        return TrajectoryRun.from_json(rows[0])

    def list_trajectory_steps(
        self, run_id: str, include_children: bool = True
    ) -> list[TrajectoryStep]:
        fetch = self._require_fetch()
        if not include_children:
            rows = fetch(
                "SELECT * FROM trajectory_steps WHERE run_id=%(runId)s ORDER BY logical_seq",
                {"runId": run_id},
            )
            return [TrajectoryStep.from_json(row) for row in rows]

        run = self.get_trajectory_run(run_id)
        if run is None:
            return []

        run_rows = fetch(
            "SELECT * FROM trajectory_runs WHERE root_run_id=%(rootRunId)s",
            {"rootRunId": run.root_run_id},
        )
        runs = [TrajectoryRun.from_json(row) for row in run_rows]
        seen = {run_id}
        frontier = [run_id]
        while frontier:
            current = frontier.pop()
            for child in runs:
                if child.parent_run_id == current and child.run_id not in seen:
                    seen.add(child.run_id)
                    frontier.append(child.run_id)

        rows = fetch(
            "SELECT * FROM trajectory_steps WHERE run_id = ANY(%(runIds)s) "
            "ORDER BY logical_seq",
            {"runIds": list(seen)},
        )
        return sorted(
            [TrajectoryStep.from_json(row) for row in rows],
            key=lambda step: step.logical_seq,
        )

    def list_trajectory_values(
        self, run_id: str, refs: Optional[list[str]] = None
    ) -> list[TrajectoryValue]:
        rows = self._require_fetch()(
            "SELECT * FROM trajectory_values WHERE root_run_id=%(runId)s",
            {"runId": run_id, "refs": refs or []},
        )
        return [TrajectoryValue.from_json(row) for row in rows]

    def export_trajectory_jsonl(
        self, run_id: str, format: str = "supervised_turns"
    ) -> list[str]:
        if format != "supervised_turns":
            raise ValueError(f"unsupported trajectory export format: {format!r}")
        return [json.dumps(step.to_json(), sort_keys=True) for step in self.list_trajectory_steps(run_id)]

    async def export_trajectory_jsonl_hydrated(
        self, run_id: str, blob_store: Any, format: str = "supervised_turns"
    ) -> list[str]:
        store = InMemoryTrajectoryStore()
        run = self.get_trajectory_run(run_id)
        if run is not None:
            store.start_run(run)
        store.append_steps(self.list_trajectory_steps(run_id))
        store.record_values(self.list_trajectory_values(run_id))
        return await store.export_trajectory_jsonl_hydrated(run_id, blob_store, format)

    def buffer(self) -> list[Any]:
        return list(self._buffer)
