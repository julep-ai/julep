"""The pomset projection (blueprint, observability plane).

This is a *derived*, append-only view of a run — emphatically **not** the
durability mechanism (Temporal history is). A Temporal interceptor (or a
history-export tail) feeds three event kinds into a :class:`ProjectionStore` as
the workflow walks the IR:

* ``PLANNED`` — a node activation is about to run. Its ``causes`` are the event
  ids that produced this activation's inputs (the IR input edges), which is what
  makes the projection a partial order (a *pomset*) rather than a flat log.
* ``DID`` — the activation succeeded, carrying a content-addressed ``value_ref``
  into the :class:`ValueStore` (big payloads live once, keyed by hash; events
  stay small).
* ``FAILED`` — the activation raised; carries the error.

A single node id can activate many times (a loop body, a retried call), so an
*activation* is identified by ``cid``, and the materialized views key off that.
The store is pluggable: :class:`InMemoryProjection` backs the golden tests, and
:class:`PostgresProjection` is the production append-only sink (its SQL lives in
:mod:`composable_agents.execution`; the class here is the seam). Everything in
this module is pure Python so the projection can be exercised without a database
or the OTel SDK; :func:`to_otel_spans` produces the span data the real exporter
in :mod:`composable_agents.execution.otel` consumes.
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Optional, Protocol

from .ir import canonical_json


class EventType(str, Enum):
    PLANNED = "Planned"
    DID = "Did"
    FAILED = "Failed"


@dataclass(frozen=True)
class ProjectionEvent:
    """One immutable fact about one node activation."""

    event_id: str
    type: EventType
    node: str                       # IR node id
    cid: str                        # activation id (unique per node firing)
    ts: float                       # logical or wall timestamp
    causes: tuple[str, ...] = ()    # upstream event ids (IR input edges)
    value_ref: Optional[str] = None  # DID: content hash into the value store
    shape: Optional[str] = None     # surface shape, for the cost roll-up
    cost: Optional[float] = None     # DID: cost charged to this activation
    error: Optional[str] = None     # FAILED: error message
    attrs: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "eventId": self.event_id,
            "type": self.type.value,
            "node": self.node,
            "cid": self.cid,
            "ts": self.ts,
            "causes": list(self.causes),
        }
        for k, src in (
            ("valueRef", self.value_ref),
            ("shape", self.shape),
            ("cost", self.cost),
            ("error", self.error),
        ):
            if src is not None:
                out[k] = src
        if self.attrs:
            out["attrs"] = self.attrs
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "ProjectionEvent":
        return ProjectionEvent(
            event_id=d["eventId"],
            type=EventType(d["type"]),
            node=d["node"],
            cid=d["cid"],
            ts=d["ts"],
            causes=tuple(d.get("causes", [])),
            value_ref=d.get("valueRef"),
            shape=d.get("shape"),
            cost=d.get("cost"),
            error=d.get("error"),
            attrs=dict(d.get("attrs", {})),
        )


# --------------------------------------------------------------------------- #
# Content-addressed value store.
# --------------------------------------------------------------------------- #
def value_ref(value: Any) -> str:
    """Stable content hash for a value (canonical JSON -> sha256)."""
    payload = canonical_json(value)
    return "val:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


class ValueStore:
    """Deduplicating value store: identical values collapse to one entry."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}

    def put(self, value: Any) -> str:
        ref = value_ref(value)
        self._values.setdefault(ref, value)
        return ref

    def get(self, ref: str) -> Any:
        return self._values[ref]

    def has(self, ref: str) -> bool:
        return ref in self._values


# --------------------------------------------------------------------------- #
# Store protocol + in-memory + Postgres seam.
# --------------------------------------------------------------------------- #
class ProjectionStore(Protocol):
    def append(self, event: ProjectionEvent) -> None: ...
    def events(self) -> list[ProjectionEvent]: ...


class ProjectionSink(Protocol):
    """A write-only consumer of projection events (observability adapters)."""

    def append(self, event: ProjectionEvent) -> None: ...


class TeeStore:
    """A :class:`ProjectionStore` that fans every append out to extra sinks.

    Queries (``events``) are served by the primary store; sinks are
    fire-and-forget appenders (a Logfire exporter, a metrics counter). A sink
    exception propagates — a broken observability pipe should fail loudly in
    dev; production adapters are expected to catch their own transport errors.
    """

    def __init__(self, primary: "InMemoryProjection", *sinks: ProjectionSink) -> None:
        self._primary = primary
        self._sinks = tuple(sinks)
        # ProjectionEmitter discovers a value store via getattr(store, "values").
        self.values = primary.values

    def append(self, event: ProjectionEvent) -> None:
        self._primary.append(event)
        for sink in self._sinks:
            sink.append(event)

    def events(self) -> list[ProjectionEvent]:
        return self._primary.events()


class InMemoryProjection:
    """A complete, queryable projection backed by a Python list (tests/dev)."""

    def __init__(self) -> None:
        self._events: list[ProjectionEvent] = []
        self.values = ValueStore()

    # ProjectionStore
    def append(self, event: ProjectionEvent) -> None:
        self._events.append(event)

    def events(self) -> list[ProjectionEvent]:
        return list(self._events)

    # ----- materialized views ---------------------------------------------- #
    def status_by_activation(self) -> dict[str, EventType]:
        """Latest state per activation (cid). PLANNED then DID -> DID."""
        latest: dict[str, EventType] = {}
        for e in self._events:
            latest[e.cid] = e.type
        return latest

    def pending(self) -> list[str]:
        """Activations that were PLANNED but never reached DID/FAILED."""
        return [cid for cid, st in self.status_by_activation().items()
                if st == EventType.PLANNED]

    def latest_value(self, node: str) -> Any:
        """Most recent successful value produced by ``node`` (resolved), or None."""
        ref = None
        for e in self._events:
            if e.node == node and e.type == EventType.DID and e.value_ref is not None:
                ref = e.value_ref
        return self.values.get(ref) if ref is not None else None

    def cost_by_shape(self) -> dict[str, float]:
        """Total charged cost grouped by the activation's surface shape."""
        roll: dict[str, float] = {}
        for e in self._events:
            if e.type == EventType.DID and e.cost is not None:
                key = e.shape or "unknown"
                roll[key] = roll.get(key, 0.0) + e.cost
        return roll

    def failures(self) -> list[ProjectionEvent]:
        return [e for e in self._events if e.type == EventType.FAILED]


class PostgresProjection:
    """Production append-only sink (seam).

    The schema is a single ``projection_events`` table plus a ``values`` table,
    with the materialized views above expressed as SQL. The concrete cursor
    wiring lives in :mod:`composable_agents.execution` so this module stays
    importable without a database driver. Calling :meth:`append` without an
    injected ``execute`` callable is a deliberate, loud error.
    """

    INSERT_SQL = (
        "INSERT INTO projection_events "
        "(event_id, type, node, cid, ts, causes, value_ref, shape, cost, error, attrs) "
        "VALUES (%(eventId)s, %(type)s, %(node)s, %(cid)s, %(ts)s, %(causes)s, "
        "%(valueRef)s, %(shape)s, %(cost)s, %(error)s, %(attrs)s)"
    )

    def __init__(self, execute: Optional[Any] = None) -> None:
        # execute: callable(sql: str, params: dict) -> None (e.g. a psycopg cursor)
        self._execute = execute
        self._buffer: list[ProjectionEvent] = []

    def append(self, event: ProjectionEvent) -> None:
        if self._execute is None:
            raise RuntimeError(
                "PostgresProjection needs an `execute` callable; inject a DB cursor "
                "from composable_agents.execution or use InMemoryProjection in tests"
            )
        row = event.to_json()
        row.setdefault("valueRef", None)
        row.setdefault("shape", None)
        row.setdefault("cost", None)
        row.setdefault("error", None)
        row["causes"] = list(event.causes)
        row["attrs"] = event.attrs or {}
        self._execute(self.INSERT_SQL, row)
        self._buffer.append(event)

    def events(self) -> list[ProjectionEvent]:
        # Buffered view of what this process appended; full history lives in PG.
        return list(self._buffer)


# --------------------------------------------------------------------------- #
# Emitter: the thin API the interceptor / harness calls.
# --------------------------------------------------------------------------- #
class ProjectionEmitter:
    """Records Planned/Did/Failed against a store, minting ids and value refs.

    The harness (or a Temporal interceptor) holds one of these per run. ``plan``
    returns the new event id so the caller can thread it into the ``causes`` of
    downstream activations, which is what knits the pomset together.
    """

    def __init__(
        self,
        store: ProjectionStore,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._store = store
        self._ids = itertools.count()
        # clock() -> float; defaults to a monotonic logical counter so the
        # projection is deterministic in tests (no wall-clock in replay anyway).
        self._tick = itertools.count()
        self._clock = clock or (lambda: float(next(self._tick)))
        # only InMemoryProjection exposes a value store; tolerate stores without.
        self._values: Optional[ValueStore] = getattr(store, "values", None)

    def _next_id(self) -> str:
        return f"e{next(self._ids)}"

    def plan(self, node: str, cid: str, causes: Iterable[str] = (),
             shape: Optional[str] = None, attrs: Optional[dict[str, Any]] = None) -> str:
        eid = self._next_id()
        self._store.append(ProjectionEvent(
            event_id=eid, type=EventType.PLANNED, node=node, cid=cid,
            ts=self._clock(), causes=tuple(causes), shape=shape,
            attrs=dict(attrs or {}),
        ))
        return eid

    def did(self, node: str, cid: str, value: Any = None,
            cost: Optional[float] = None, shape: Optional[str] = None,
            causes: Iterable[str] = (), attrs: Optional[dict[str, Any]] = None) -> str:
        eid = self._next_id()
        ref = self._values.put(value) if (self._values is not None and value is not None) else None
        self._store.append(ProjectionEvent(
            event_id=eid, type=EventType.DID, node=node, cid=cid,
            ts=self._clock(), causes=tuple(causes), value_ref=ref, cost=cost, shape=shape,
            attrs=dict(attrs or {}),
        ))
        return eid

    def fail(self, node: str, cid: str, error: str,
             causes: Iterable[str] = ()) -> str:
        eid = self._next_id()
        self._store.append(ProjectionEvent(
            event_id=eid, type=EventType.FAILED, node=node, cid=cid,
            ts=self._clock(), causes=tuple(causes), error=error,
        ))
        return eid


# --------------------------------------------------------------------------- #
# OTel mapping (pure data; the SDK export lives in execution.otel).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SpanData:
    name: str
    cid: str
    node: str
    start_ts: float
    end_ts: Optional[float]
    status: str                 # "ok" | "error" | "unfinished"
    parents: tuple[str, ...]    # causing cids
    error: Optional[str] = None


def to_otel_spans(events: list[ProjectionEvent]) -> list[SpanData]:
    """Pair PLANNED with its terminal DID/FAILED (by cid) into span data.

    A causal edge (event id in ``causes``) is resolved back to the producing
    activation's cid so spans link parent->child the way OTel expects.
    """
    by_event_cid: dict[str, str] = {e.event_id: e.cid for e in events}
    starts: dict[str, ProjectionEvent] = {}
    ends: dict[str, ProjectionEvent] = {}
    for e in events:
        if e.type == EventType.PLANNED:
            starts[e.cid] = e
        else:
            ends[e.cid] = e

    spans: list[SpanData] = []
    for cid, start in starts.items():
        end = ends.get(cid)
        parents = tuple(
            by_event_cid[c] for c in start.causes if c in by_event_cid
        )
        if end is None:
            spans.append(SpanData(
                name=start.node, cid=cid, node=start.node,
                start_ts=start.ts, end_ts=None, status="unfinished",
                parents=parents,
            ))
        else:
            status = "ok" if end.type == EventType.DID else "error"
            spans.append(SpanData(
                name=start.node, cid=cid, node=start.node,
                start_ts=start.ts, end_ts=end.ts, status=status,
                parents=parents, error=end.error,
            ))
    return spans
