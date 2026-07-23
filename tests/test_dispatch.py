from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from julep.dispatch import (
    BatchTrigger,
    BatchWindow,
    SignalWithStartRequest,
    build_debounce_request,
    dedup_workflow_id,
    signal_with_start,
)
from julep.execution import HAVE_TEMPORAL


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


def test_dedup_workflow_id_is_canonical_opaque_and_bounded() -> None:
    first = dedup_workflow_id(
        "episode summary / prod",
        {"store_id": 42, "nested": {"b": 2, "a": 1}},
        "generation-7",
        max_length=52,
    )
    reordered = dedup_workflow_id(
        "episode summary / prod",
        {"nested": {"a": 1, "b": 2}, "store_id": 42},
        "generation-7",
        max_length=52,
    )

    assert first == reordered
    assert len(first) <= 52
    assert re.fullmatch(r"[A-Za-z0-9_.-]+:[0-9a-f]{32}", first)
    assert "42" not in first
    assert "generation" not in first
    assert first != dedup_workflow_id(
        "episode summary / prod",
        {"store_id": 42, "nested": {"b": 2, "a": 1}},
        "generation-8",
        max_length=52,
    )


def test_dedup_workflow_id_rejects_ambiguous_inputs() -> None:
    with pytest.raises(ValueError, match="namespace"):
        dedup_workflow_id("", "x")
    with pytest.raises(ValueError, match="at least 34"):
        dedup_workflow_id("dispatch", "x", max_length=33)
    with pytest.raises(TypeError, match="finite JSON"):
        dedup_workflow_id("dispatch", {"not_json": object()})
    with pytest.raises(TypeError, match="finite JSON"):
        dedup_workflow_id("dispatch", float("nan"))


def test_batch_window_reports_empty_wait_quiet_and_cap() -> None:
    window = BatchWindow(quiet_s=10, max_items=3, max_wait_s=30)

    empty = window.evaluate(
        item_count=0,
        opened_at=None,
        last_arrival_at=None,
        now=NOW,
    )
    assert not empty.fire
    assert empty.trigger is None
    assert empty.deadline is None
    assert empty.wait_s is None

    waiting = window.evaluate(
        item_count=2,
        opened_at=NOW - timedelta(seconds=5),
        last_arrival_at=NOW - timedelta(seconds=4),
        now=NOW,
    )
    assert not waiting.fire
    assert waiting.trigger is BatchTrigger.QUIET
    assert waiting.deadline == NOW + timedelta(seconds=6)
    assert waiting.wait_s == 6

    quiet = window.evaluate(
        item_count=2,
        opened_at=NOW - timedelta(seconds=20),
        last_arrival_at=NOW - timedelta(seconds=10),
        now=NOW,
    )
    assert quiet.fire
    assert quiet.trigger is BatchTrigger.QUIET
    assert quiet.wait_s == 0

    capped = window.evaluate(
        item_count=3,
        opened_at=NOW,
        last_arrival_at=NOW,
        now=NOW,
    )
    assert capped.fire
    assert capped.trigger is BatchTrigger.MAX_ITEMS


def test_batch_window_uses_max_wait_when_it_is_earlier() -> None:
    decision = BatchWindow(quiet_s=60, max_wait_s=15).evaluate(
        item_count=1,
        opened_at=NOW - timedelta(seconds=15),
        last_arrival_at=NOW,
        now=NOW,
    )

    assert decision.fire
    assert decision.trigger is BatchTrigger.MAX_WAIT
    assert decision.deadline == NOW


@pytest.mark.parametrize(
    ("window", "message"),
    [
        (lambda: BatchWindow(quiet_s=-1), "quiet_s"),
        (lambda: BatchWindow(quiet_s=float("nan")), "quiet_s"),
        (lambda: BatchWindow(quiet_s=1, max_items=0), "max_items"),
        (lambda: BatchWindow(quiet_s=1, max_items=True), "max_items"),
        (lambda: BatchWindow(quiet_s=1, max_wait_s=-1), "max_wait_s"),
        (lambda: BatchWindow(quiet_s=1, max_wait_s=float("inf")), "max_wait_s"),
    ],
)
def test_batch_window_validates_configuration(window: Any, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        window()


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_build_debounce_request_keys_by_configuration_not_item() -> None:
    first = build_debounce_request(
        {"op": "id", "meta": {"b": 2, "a": 1}},
        {"tools": []},
        key="store-42",
        item={"event": 1},
        window=BatchWindow(quiet_s=5, max_items=10, max_wait_s=60),
        scope={"pipeline": "record", "release": "abc"},
        principal={"store_id": 42},
    )
    second = build_debounce_request(
        {"meta": {"a": 1, "b": 2}, "op": "id"},
        {"tools": []},
        key="store-42",
        item={"event": 2},
        window=BatchWindow(quiet_s=5, max_items=10, max_wait_s=60),
        scope={"release": "abc", "pipeline": "record"},
        principal={"store_id": 42},
    )
    changed = build_debounce_request(
        {"op": "id", "meta": {"a": 1, "b": 2}},
        {"tools": []},
        key="store-42",
        item={"event": 3},
        window=BatchWindow(quiet_s=6, max_items=10, max_wait_s=60),
        scope={"pipeline": "record", "release": "abc"},
        principal={"store_id": 42},
    )

    assert first.workflow_id == second.workflow_id
    assert changed.workflow_id != first.workflow_id
    assert first.workflow == "DebounceCollector"
    assert first.signal == "submit"
    assert first.signal_args == ({"event": 1},)
    assert first.input.key == "store-42"
    assert first.input.quiet_s == 5
    assert "store-42" not in first.workflow_id


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_signal_with_start_executes_managed_dedup_policies() -> None:
    captured: dict[str, Any] = {}

    class FakeClient:
        async def start_workflow(
            self,
            workflow: Any,
            arg: Any,
            **kwargs: Any,
        ) -> str:
            captured.update(workflow=workflow, arg=arg, kwargs=kwargs)
            return "handle"

    request = SignalWithStartRequest(
        workflow="Collector",
        input={"configuration": True},
        workflow_id="collector:abc",
        task_queue="background",
        signal="submit",
        signal_args=({"event": 1},),
        start_options={"memo": {"owner": "test"}},
    )
    result = asyncio.run(signal_with_start(FakeClient(), request))

    assert result == "handle"
    assert captured["workflow"] == "Collector"
    assert captured["arg"] == {"configuration": True}
    kwargs = captured["kwargs"]
    assert kwargs["id"] == "collector:abc"
    assert kwargs["task_queue"] == "background"
    assert kwargs["start_signal"] == "submit"
    assert kwargs["start_signal_args"] == [{"event": 1}]
    assert kwargs["id_reuse_policy"].name == "ALLOW_DUPLICATE"
    assert kwargs["id_conflict_policy"].name == "USE_EXISTING"
    assert kwargs["memo"] == {"owner": "test"}


def test_signal_with_start_rejects_managed_option_override() -> None:
    with pytest.raises(ValueError, match="cannot override.*id"):
        SignalWithStartRequest(
            workflow="Collector",
            input=None,
            workflow_id="collector:abc",
            task_queue="background",
            signal="submit",
            start_options={"id": "other"},
        )
