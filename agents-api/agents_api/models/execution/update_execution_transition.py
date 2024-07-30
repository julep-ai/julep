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
        insert_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (query, {"values": values})
