from __future__ import annotations

from composable_agents.contracts import ToolContract
from composable_agents.errors import (
    CapabilityDenied,
    ComposableAgentsError,
    FreezeError,
    PlanRejected,
    ValidationError,
)
from composable_agents.execution import harness
from composable_agents.kinds import Effect, Idempotency


def test_policy_errors_are_framework_errors_and_temporal_non_retryable() -> None:
    policy_errors = [CapabilityDenied, PlanRejected, ValidationError, FreezeError]
    expected_names = {cls.__name__ for cls in policy_errors}

    for cls in policy_errors:
        assert issubclass(cls, ComposableAgentsError)

    assert expected_names.issubset(set(harness._NON_RETRYABLE))

    retry_policy = harness._retry_policy_for(
        ToolContract(effect=Effect.READ, idempotency=Idempotency.NATIVE),
        harness.ExecutionPolicy(),
    )
    assert expected_names.issubset(set(retry_policy.non_retryable_error_types or []))
