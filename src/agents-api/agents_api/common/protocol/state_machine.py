from collections.abc import Generator
from contextlib import contextmanager
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from ...autogen.openapi_model import TransitionTarget


class TransitionType(StrEnum):
    """Enum for transition types in the workflow."""

    INIT = "init"
    INIT_BRANCH = "init_branch"
    WAIT = "wait"
    RESUME = "resume"
    STEP = "step"
    FINISH = "finish"
    FINISH_BRANCH = "finish_branch"
    ERROR = "error"
    CANCELLED = "cancelled"


class ExecutionStatus(StrEnum):
    """Enum for execution statuses."""

    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    AWAITING_INPUT = "awaiting_input"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


class ExecutionState(BaseModel):
    """Model representing the current state of an execution."""

    status: ExecutionStatus
    transition_type: TransitionType | None = None
    current_target: TransitionTarget | None = None
    next_target: TransitionTarget | None = None
    execution_id: UUID
    metadata: dict = Field(default_factory=dict)


# Valid transitions from each state
_valid_transitions: dict[TransitionType | None, list[TransitionType]] = {
    None: [
        TransitionType.INIT,
        TransitionType.WAIT,
        TransitionType.ERROR,
        TransitionType.STEP,
        TransitionType.CANCELLED,
        TransitionType.INIT_BRANCH,
        TransitionType.FINISH,
    ],
    TransitionType.INIT: [
        TransitionType.WAIT,
        TransitionType.ERROR,
        TransitionType.STEP,
        TransitionType.CANCELLED,
        TransitionType.INIT_BRANCH,
        TransitionType.FINISH,
    ],
    TransitionType.INIT_BRANCH: [
        TransitionType.WAIT,
        TransitionType.ERROR,
        TransitionType.STEP,
        TransitionType.CANCELLED,
        TransitionType.INIT_BRANCH,
        TransitionType.FINISH_BRANCH,
        TransitionType.FINISH,
    ],
    TransitionType.WAIT: [
        TransitionType.RESUME,
        TransitionType.STEP,
        TransitionType.CANCELLED,
        TransitionType.FINISH,
        TransitionType.FINISH_BRANCH,
    ],
    TransitionType.RESUME: [
        TransitionType.WAIT,
        TransitionType.ERROR,
        TransitionType.CANCELLED,
        TransitionType.STEP,
        TransitionType.FINISH,
        TransitionType.FINISH_BRANCH,
        TransitionType.INIT_BRANCH,
    ],
    TransitionType.STEP: [
        TransitionType.WAIT,
        TransitionType.ERROR,
        TransitionType.CANCELLED,
        TransitionType.STEP,
        TransitionType.FINISH,
        TransitionType.FINISH_BRANCH,
        TransitionType.INIT_BRANCH,
    ],
    TransitionType.FINISH_BRANCH: [
        TransitionType.WAIT,
        TransitionType.ERROR,
        TransitionType.CANCELLED,
        TransitionType.STEP,
        TransitionType.FINISH,
        TransitionType.INIT_BRANCH,
    ],
    # Terminal states
    TransitionType.FINISH: [],
    TransitionType.ERROR: [],
    TransitionType.CANCELLED: [],
}

# Mapping from transition types to execution statuses
_transition_to_status: dict[TransitionType | None, ExecutionStatus] = {
    None: ExecutionStatus.QUEUED,
    TransitionType.INIT: ExecutionStatus.STARTING,
    TransitionType.INIT_BRANCH: ExecutionStatus.RUNNING,
    TransitionType.WAIT: ExecutionStatus.AWAITING_INPUT,
    TransitionType.RESUME: ExecutionStatus.RUNNING,
    TransitionType.STEP: ExecutionStatus.RUNNING,
    TransitionType.FINISH: ExecutionStatus.SUCCEEDED,
    TransitionType.FINISH_BRANCH: ExecutionStatus.RUNNING,
    TransitionType.ERROR: ExecutionStatus.FAILED,
    TransitionType.CANCELLED: ExecutionStatus.CANCELLED,
}


class ExecutionStateMachine:
    """
    A state machine for managing execution state transitions with validation.
    Uses context managers for safe state transitions.
    """

    def __init__(self, execution_id: UUID) -> None:
        """Initialize the state machine with QUEUED status."""
        self.state = ExecutionState(
            status=ExecutionStatus.QUEUED,
            execution_id=execution_id,
        )

    def _validate_transition(self, new_type: TransitionType) -> bool:
        """Validate if a transition is allowed from the current state."""
        return new_type in _valid_transitions[self.state.transition_type]

    @contextmanager
    def transition_to(
        self,
        transition_type: TransitionType,
        current_target: TransitionTarget | None = None,
        next_target: TransitionTarget | None = None,
        metadata: dict | None = None,
    ) -> Generator[ExecutionState, None, None]:
        """
        Context manager for safely transitioning to a new state.

        Args:
            transition_type: The type of transition to perform
            current_target: The current workflow target
            next_target: The next workflow target
            metadata: Optional metadata for the transition

        Raises:
            StateTransitionError: If the transition is invalid
        """
        if not self._validate_transition(transition_type):
            msg = f"Invalid transition from {self.state.transition_type} to {transition_type}"
            raise StateTransitionError(msg)

        # Store previous state for rollback
        previous_state = self.state.model_copy(deep=True)

        try:
            # Update the state
            self.state.transition_type = transition_type
            self.state.status = _transition_to_status[transition_type]
            self.state.current_target = current_target
            self.state.next_target = next_target
            if metadata:
                self.state.metadata.update(metadata)

            yield self.state

        except Exception as e:
            # Rollback on error
            self.state = previous_state
            msg = f"Transition failed: {e!s}"
            raise StateTransitionError(msg) from e

    @property
    def is_terminal(self) -> bool:
        """Check if the current state is terminal."""
        return (
            self.state.transition_type is not None
            and not _valid_transitions[self.state.transition_type]
        )

    @property
    def current_status(self) -> ExecutionStatus:
        """Get the current execution status."""
        return self.state.status
