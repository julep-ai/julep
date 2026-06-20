"""Guard: every @activity.defn the harness defines must be registered on the
Temporal worker.

Regression for a real bug the EKS acceptance run surfaced: ``startTrajectory``
and ``flushStructural`` were defined and dispatched by the workflow but missing
from ``worker.ACTIVITIES``. Because trajectory capture is best-effort (the
workflow swallows the dispatch failure), the flow still returned the right
result and the unit suite stayed green — the worker just logged a
``NotFoundError`` and silently captured nothing. An unregistered activity must
fail loudly here instead.
"""

from __future__ import annotations

import pytest

pytest.importorskip("temporalio")

from composable_agents.execution import harness, worker  # noqa: E402


def _activity_callables(module: object) -> list[object]:
    return [
        obj
        for obj in vars(module).values()
        if callable(obj) and hasattr(obj, "__temporal_activity_definition")
    ]


def test_every_harness_activity_is_registered_on_the_worker() -> None:
    defined = _activity_callables(harness)
    assert defined, "expected harness to define @activity.defn activities"
    registered = {id(act) for act in worker.ACTIVITIES}
    missing = [getattr(a, "__name__", repr(a)) for a in defined if id(a) not in registered]
    assert not missing, f"harness activities missing from worker.ACTIVITIES: {missing}"


def test_trajectory_activities_are_registered() -> None:
    for act in (
        harness.startTrajectory,
        harness.finishTrajectory,
        harness.flushStructural,
        harness.runSubCapture,
    ):
        assert act in worker.ACTIVITIES, f"{act.__name__} not registered on the worker"
