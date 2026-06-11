from __future__ import annotations

import pytest

pytest.importorskip("temporalio")

from composable_agents import Ann
from composable_agents.contracts import ToolContract
from composable_agents.errors import (
    CapabilityDenied,
    ComposableAgentsError,
    FreezeError,
    PlanRejected,
    PrincipalRequired,
    ValidationError,
)
from composable_agents.execution import harness
from composable_agents.kinds import Effect, Idempotency


def test_policy_errors_are_framework_errors_and_temporal_non_retryable() -> None:
    policy_errors = [
        CapabilityDenied,
        PlanRejected,
        ValidationError,
        FreezeError,
        PrincipalRequired,
    ]
    expected_names = {cls.__name__ for cls in policy_errors}

    for cls in policy_errors:
        assert issubclass(cls, ComposableAgentsError)

    assert expected_names.issubset(set(harness._NON_RETRYABLE))

    retry_policy = harness._retry_policy_for(
        ToolContract(effect=Effect.READ, idempotency=Idempotency.NATIVE),
        harness.ExecutionPolicy(),
    )
    assert expected_names.issubset(set(retry_policy.non_retryable_error_types or []))


def test_temporal_retry_policy_clamps_ann_backoff_to_sdk_floor() -> None:
    retry_policy = harness._retry_policy_for(
        ToolContract(effect=Effect.READ, idempotency=Idempotency.NATIVE),
        harness.ExecutionPolicy(),
        Ann(backoff_rate=0.5),
    )

    assert retry_policy.maximum_attempts != 1
    assert retry_policy.backoff_coefficient >= 1.0
    retry_policy._validate()
