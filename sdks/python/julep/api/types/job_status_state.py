# This file was auto-generated by Fern from our API Definition.

import enum
import typing

T_Result = typing.TypeVar("T_Result")


class JobStatusState(str, enum.Enum):
    """
    Current state (one of: pending, in_progress, retrying, succeeded, aborted, failed)
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    ABORTED = "aborted"
    FAILED = "failed"
    UNKNOWN = "unknown"

    def visit(
        self,
        pending: typing.Callable[[], T_Result],
        in_progress: typing.Callable[[], T_Result],
        retrying: typing.Callable[[], T_Result],
        succeeded: typing.Callable[[], T_Result],
        aborted: typing.Callable[[], T_Result],
        failed: typing.Callable[[], T_Result],
        unknown: typing.Callable[[], T_Result],
    ) -> T_Result:
        if self is JobStatusState.PENDING:
            return pending()
        if self is JobStatusState.IN_PROGRESS:
            return in_progress()
        if self is JobStatusState.RETRYING:
            return retrying()
        if self is JobStatusState.SUCCEEDED:
            return succeeded()
        if self is JobStatusState.ABORTED:
            return aborted()
        if self is JobStatusState.FAILED:
            return failed()
        if self is JobStatusState.UNKNOWN:
            return unknown()
