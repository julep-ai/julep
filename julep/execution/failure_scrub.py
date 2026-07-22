"""Run-secret-safe exception conversion at durable execution boundaries."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from functools import wraps
from typing import Any, Optional, TypeVar

from temporalio.exceptions import ApplicationError

from ..errors import POLICY_ERRORS, tool_surface_drift_from_cause
from ..secrets import REDACTED, operator_secret_redactor, scrubber_for_values


_T = TypeVar("_T")


def redact_failure_value(
    value: Any,
    secrets: Optional[Mapping[str, str]],
    *,
    redactor: Optional[Callable[[Any], Any]] = None,
) -> Any:
    """Remove raw and encoded run-secret echoes, failing closed.

    This helper is deterministic when called from workflow code: it uses only
    values carried in that workflow's encrypted input and no process-global
    registry.
    """

    if redactor is None:
        if not secrets:
            return value
        redactor = scrubber_for_values(secrets.values())
    try:
        return redactor(value)
    except Exception:
        return REDACTED


def redacted_failure_text(
    error: BaseException | str,
    secrets: Optional[Mapping[str, str]],
    *,
    use_repr: bool = False,
    redactor: Optional[Callable[[Any], Any]] = None,
) -> str:
    """Return a secret-safe exception message or representation."""

    if isinstance(error, BaseException):
        raw = repr(error) if use_repr else str(error)
    else:
        raw = error
    redacted = redact_failure_value(raw, secrets, redactor=redactor)
    return redacted if isinstance(redacted, str) else REDACTED


def application_error_from_failure(
    error: BaseException,
    secrets: Optional[Mapping[str, str]],
    *,
    use_repr: bool = False,
    non_retryable: Optional[bool] = None,
    redactor: Optional[Callable[[Any], Any]] = None,
) -> ApplicationError:
    """Rebuild ``error`` without retaining its potentially unsafe cause.

    Callers must raise the returned error ``from None``. Typed MCP drift and
    existing ``ApplicationError`` metadata survive the conversion, while the
    message and user details are scrubbed before Temporal sees them.
    """

    drift = tool_surface_drift_from_cause(error)
    if drift is not None:
        details = redact_failure_value(
            drift.to_json(), secrets, redactor=redactor
        )
        return ApplicationError(
            redacted_failure_text(drift, secrets, redactor=redactor),
            details,
            type="ToolSurfaceDrift",
            non_retryable=True,
        )

    application_failure = _application_error_from_cause(error)
    if application_failure is not None:
        redacted_details = redact_failure_value(
            list(application_failure.details), secrets, redactor=redactor
        )
        details = (
            tuple(redacted_details)
            if isinstance(redacted_details, list)
            else (redacted_details,)
        )
        return ApplicationError(
            redacted_failure_text(
                application_failure.message, secrets, redactor=redactor
            ),
            *details,
            type=application_failure.type,
            non_retryable=(
                application_failure.non_retryable
                if non_retryable is None
                else non_retryable
            ),
            next_retry_delay=application_failure.next_retry_delay,
            category=application_failure.category,
        )

    return ApplicationError(
        redacted_failure_text(
            error,
            secrets,
            use_repr=use_repr,
            redactor=redactor,
        ),
        type=type(error).__name__,
        non_retryable=(
            isinstance(error, POLICY_ERRORS)
            if non_retryable is None
            else non_retryable
        ),
    )


def _application_error_from_cause(error: BaseException) -> ApplicationError | None:
    """Find Temporal application metadata through workflow/activity wrappers."""

    pending: list[BaseException] = [error]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if isinstance(current, ApplicationError):
            return current
        for nested in (
            getattr(current, "__cause__", None),
            getattr(current, "__context__", None),
            getattr(current, "cause", None),
        ):
            if isinstance(nested, BaseException):
                pending.append(nested)
    return None


def activity_application_error_from_failure(
    error: BaseException,
    secrets: Optional[Mapping[str, str]],
) -> ApplicationError:
    """Scrub activity failures with live operator and per-run values.

    Activities are outside workflow replay, so they may safely consult the
    process-wide operator-secret registry. Operator values are scrubbed first;
    the immutable run-scoped scrubber is then composed over that result.
    """

    redactor = operator_secret_redactor()
    if secrets:
        redactor = scrubber_for_values(secrets.values(), base=redactor)
    return application_error_from_failure(
        error,
        secrets,
        redactor=redactor,
    )


def activity_redacted_failure_text(
    error: BaseException | str,
    secrets: Optional[Mapping[str, str]] = None,
    *,
    use_repr: bool = False,
) -> str:
    """Scrub a caught activity-side diagnostic that will be returned as data."""

    redactor = operator_secret_redactor()
    if secrets:
        redactor = scrubber_for_values(secrets.values(), base=redactor)
    return redacted_failure_text(
        error,
        secrets,
        use_repr=use_repr,
        redactor=redactor,
    )


def secret_safe_activity(
    body: Callable[[Any], Awaitable[_T]],
) -> Callable[[Any], Awaitable[_T]]:
    """Scrub a one-payload activity's exception before Temporal serializes it."""

    @wraps(body)
    async def wrapped(inp: Any) -> _T:
        try:
            return await body(inp)
        except Exception as exc:
            secrets = (
                inp.get("secrets")
                if isinstance(inp, Mapping)
                else getattr(inp, "secrets", None)
            )
            raise activity_application_error_from_failure(exc, secrets) from None

    return wrapped


__all__ = [
    "activity_application_error_from_failure",
    "activity_redacted_failure_text",
    "application_error_from_failure",
    "redact_failure_value",
    "redacted_failure_text",
    "secret_safe_activity",
]
