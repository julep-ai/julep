from typing import Literal
from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from ...autogen.openapi_model import (
    CreateTransitionRequest,
    Transition,
)
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, serialize_model_data, wrap_in_class

# Query to create a transition
create_execution_transition_query = """
INSERT INTO transitions
(
    execution_id,
    transition_id,
    type,
    step_label,
    current_step,
    next_step,
    output,
    task_token,
    metadata
)
VALUES
(
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8,
    $9
)
RETURNING *;
"""


# FIXME: Remove this function
def validate_transition_targets(data: CreateTransitionRequest) -> None:
    # Make sure the current/next targets are valid
    match data.type:
        case "finish_branch":
            pass  # TODO: Implement
        case "finish" | "error" | "cancelled":
            pass

            # FIXME: HACK: Fix this and uncomment

            # assert (
            # data.next is None
            # ), "Next target must be None for finish/finish_branch/error/cancelled"

        case "init_branch" | "init":
            assert data.next and data.current.step == data.next.step == 0, (
                "Next target must be same as current for init_branch/init and step 0"
            )

        case "wait":
            assert data.next is None, "Next target must be None for wait"

        case "resume" | "step":
            assert data.next is not None, "Next target must be provided for resume/step"

            if data.next.workflow == data.current.workflow:
                assert data.next.step > data.current.step, (
                    "Next step must be greater than current"
                )

        case _:
            msg = f"Invalid transition type: {data.type}"
            raise ValueError(msg)


@rewrap_exceptions(common_db_exceptions("transition", ["create"]))
@wrap_in_class(
    Transition,
    transform=lambda d: {
        **d,
        "id": d["transition_id"],
        "current": {"workflow": d["current_step"][0], "step": d["current_step"][1]},
        "next": d["next_step"] and {"workflow": d["next_step"][0], "step": d["next_step"][1]},
        "updated_at": utcnow(),
    },
    one=True,
)
@increase_counter("create_execution_transition")
@pg_query
@beartype
async def create_execution_transition(
    *,
    developer_id: UUID,
    execution_id: UUID,
    data: CreateTransitionRequest,
    # Only one of these needed
    transition_id: UUID | None = None,
    task_token: str | None = None,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Create a new execution transition.

    Parameters:
        developer_id (UUID): The ID of the developer.
        execution_id (UUID): The ID of the execution.
        data (CreateTransitionRequest): The data for the transition.
        transition_id (UUID | None): The ID of the transition.
        task_token (str | None): The task token.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query and parameters for creating the transition.
    """
    transition_id = transition_id or uuid7()
    data.metadata = data.metadata or {}
    data.execution_id = execution_id

    # Dump to json
    data.output = serialize_model_data(data.output)

    # Prepare the transition data
    transition_data = data.model_dump(exclude_unset=True, exclude={"id"})

    # Parse the current and next targets
    validate_transition_targets(data)
    current_target = transition_data.pop("current")
    next_target = transition_data.pop("next")

    transition_data["current"] = (current_target["workflow"], current_target["step"])
    transition_data["next"] = next_target and (
        next_target["workflow"],
        next_target["step"],
    )

    return (
        create_execution_transition_query,
        [
            execution_id,
            transition_id,
            data.type,
            transition_data.get("step_label"),
            transition_data["current"],
            transition_data["next"],
            data.output,
            task_token,
            data.metadata,
        ],
        "fetchrow",
    )
