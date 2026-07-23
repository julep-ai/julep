from __future__ import annotations

import pytest

pytest.importorskip("temporalio")

from julep import Ann
from julep.contracts import ToolContract
from julep.errors import (
    CapabilityDenied,
    JulepError,
    FreezeError,
    PlanRejected,
    PrincipalRequired,
    ToolInputValidation,
    ToolSurfaceDrift,
    ValidationError,
)
from julep.execution import harness
from julep.kinds import Effect, Idempotency


def test_policy_errors_are_framework_errors_and_temporal_non_retryable() -> None:
    policy_errors = [
        CapabilityDenied,
        PlanRejected,
        ValidationError,
        FreezeError,
        PrincipalRequired,
        ToolSurfaceDrift,
        ToolInputValidation,
    ]
    expected_names = {cls.__name__ for cls in policy_errors}

    for cls in policy_errors:
        assert issubclass(cls, JulepError)

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
        asserted=True,
    )

    assert retry_policy.maximum_attempts != 1
    assert retry_policy.backoff_coefficient >= 1.0
    retry_policy._validate()


def test_temporal_retry_policy_denies_unasserted_hint_even_with_annotation_override() -> None:
    retry_policy = harness._retry_policy_for(
        ToolContract(effect=Effect.READ, idempotency=Idempotency.NATIVE),
        harness.ExecutionPolicy(),
        Ann(max_attempts=9),
        asserted=False,
    )

    assert retry_policy.maximum_attempts == 1
