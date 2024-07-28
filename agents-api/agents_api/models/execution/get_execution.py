from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Execution
from ..utils import (
    cozo_query,
    wrap_in_class,
)


@wrap_in_class(Execution, one=True)
@cozo_query
@beartype
def get_execution(
    *,
    execution_id: UUID,
) -> tuple[str, dict]:
    # Executions are allowed direct GET access if they have execution_id

    query = """
    input[execution_id] <- [[to_uuid($execution_id)]]

    ?[id, task_id, status, input, session_id, metadata, created_at, updated_at] := 
        input[execution_id],
        *executions {
            task_id,
            execution_id,
            status,
            input,
            session_id,
            metadata,
            created_at,
            updated_at,
        },
        id = execution_id

    :limit 1
    """

    return (
        query,
        {
            "execution_id": str(execution_id),
        },
    )
