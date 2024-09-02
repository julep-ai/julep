from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import (
    CreateTransitionRequest,
    Transition,
    UpdateExecutionRequest,
)
from ...common.protocol.tasks import transition_to_execution_status, valid_transitions
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)
from .update_execution import update_execution


def validate_transition_targets(data: CreateTransitionRequest) -> None:
    # Make sure the current/next targets are valid
    match data.type:
        case "finish" | "finish_branch" | "error" | "cancelled":
            assert (
                data.next is None
            ), "Next target must be None for finish/finish_branch/error/cancelled"

        case "init_branch" | "init":
            assert (
                data.next and data.current.step == data.next.step == 0
            ), "Next target must be same as current for init_branch/init and step 0"

        case "wait":
            assert data.next is None, "Next target must be None for wait"

        case "resume" | "step":
            assert data.next is not None, "Next target must be provided for resume/step"

            if data.next.workflow == data.current.workflow:
                assert (
                    data.next.step > data.current.step
                ), "Next step must be greater than current"

        case _:
            raise ValueError(f"Invalid transition type: {data.type}")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    Transition,
    transform=lambda d: {
        **d,
        "id": d["transition_id"],
        "current": {"workflow": d["current"][0], "step": d["current"][1]},
        "next": d["next"] and {"workflow": d["next"][0], "step": d["next"][1]},
    },
    one=True,
    _kind="inserted",
)
@cozo_query
@beartype
def create_execution_transition(
    *,
    developer_id: UUID,
    execution_id: UUID,
    data: CreateTransitionRequest,
    # Only one of these needed
    transition_id: UUID | None = None,
    task_token: str | None = None,
    # Only required for updating the execution status as well
    update_execution_status: bool = False,
    task_id: UUID | None = None,
) -> tuple[list[str], dict]:
    transition_id = transition_id or uuid4()

    data.metadata = data.metadata or {}
    data.execution_id = execution_id

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

    columns, transition_values = cozo_process_mutate_data(
        {
            **transition_data,
            "task_token": task_token,
            "transition_id": str(transition_id),
            "execution_id": str(execution_id),
        }
    )

    # Make sure the transition is valid
    check_last_transition_query = f"""
    valid_transition[start, end] <- [
        {", ".join(f'["{start}", "{end}"]' for start, ends in valid_transitions.items() for end in ends)}
    ]

    last_transition_type[min_cost(type_created_at)] :=
        *transitions {{
            execution_id: to_uuid("{str(execution_id)}"),
            type,
            created_at,
        }},
        type_created_at = [type, -created_at]

    matched[collect(last_type)] :=
        last_transition_type[data],
        last_type_data = first(data),
        last_type = if(is_null(last_type_data), "init", last_type_data),
        valid_transition[last_type, $next_type]

    ?[valid] :=
        matched[prev_transitions],
        found = length(prev_transitions),
        valid = assert(found > 0, "Invalid transition"),
    """

    # Prepare the insert query
    insert_query = f"""
    ?[{columns}] <- $transition_values

    :insert transitions {{
        {columns}
    }}
    
    :returning
    """

    validate_status_query, update_execution_query, update_execution_params = (
        "",
        "",
        {},
    )

    if update_execution_status:
        assert (
            task_id is not None
        ), "task_id is required for updating the execution status"

        # Prepare the execution update query
        [*_, validate_status_query, update_execution_query], update_execution_params = (
            update_execution.__wrapped__(
                developer_id=developer_id,
                task_id=task_id,
                execution_id=execution_id,
                data=UpdateExecutionRequest(
                    status=transition_to_execution_status[data.type]
                ),
                output=data.output if data.type == "finish" else None,
                error=str(data.output)
                if data.type == "error" and data.output
                else None,
            )
        )

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id,
            "executions",
            execution_id=execution_id,
            parents=[("agents", "agent_id"), ("tasks", "task_id")],
        ),
        validate_status_query,
        update_execution_query,
        check_last_transition_query,
        insert_query,
    ]

    return (
        queries,
        {
            "transition_values": transition_values,
            "next_type": data.type,
            "valid_transitions": valid_transitions,
            **update_execution_params,
        },
    )
