import json
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateTransitionRequest, Transition
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)

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


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(Transition, transform=lambda d: {"id": d["transition_id"], **d})
@cozo_query
@beartype
def create_execution_transition(
    *,
    developer_id: UUID,
    execution_id: UUID,
    transition_id: UUID | None = None,
    data: CreateTransitionRequest,
    task_token: str | None = None,
) -> tuple[str, dict]:
    transition_id = transition_id or uuid4()

    data.metadata = data.metadata or {}
    data.execution_id = execution_id

    transition_data = data.model_dump(exclude_unset=True)
    columns, values = cozo_process_mutate_data(
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

    insert_query = f"""
    ?[{columns}] <- $values

    :insert transitions {{
        {columns}
    }}
    
    :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id,
            "executions",
            execution_id=execution_id,
            parents=[("agents", "agent_id"), ("tasks", "task_id")],
        ),
        check_last_transition_query,
        insert_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (
        query,
        {
            "values": values,
            "next_type": data.type,
            "valid_transitions": valid_transitions,
        },
    )
