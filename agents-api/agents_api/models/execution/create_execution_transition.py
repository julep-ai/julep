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

valid_transitions = {
    # Start state
    "init": ["wait", "error", "step", "cancelled"],
    # End states
    "finish": [],
    "error": [],
    "cancelled": [],
    # Intermediate states
    "wait": ["resume", "error", "cancelled"],
    "resume": ["wait", "error", "step", "finish", "cancelled"],
    "step": ["wait", "error", "step", "finish", "cancelled"],
}

transition_to_execution_status = {
    "init": "queued",
    "wait": "awaiting_input",
    "resume": "running",
    "step": "running",
    "finish": "succeeded",
    "error": "failed",
    "cancelled": "cancelled",
}


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    Transition,
    transform=lambda d: {"id": d["transition_id"], **d},
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
    transition_data = data.model_dump(exclude_unset=True)
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
            type,
            created_at,
        }},
        type_created_at = [type, -created_at]

    ?[last_type] :=
        last_transition_type[data],
        last_type_data = first(data),
        last_type = if(is_null(last_type_data), "init", last_type_data),
        valid_transition[last_type, $next_type]

    :assert some
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
