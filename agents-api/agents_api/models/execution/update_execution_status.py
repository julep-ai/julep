from uuid import UUID

from ..utils import cozo_query
from typing import Literal, Dict, Any


@cozo_query
def update_execution_status_query(
    task_id: UUID,
    execution_id: UUID,
    status: Literal[
        "queued", "starting", "running", "waiting-for-input", "success", "failed"
    ],
    arguments: Dict[str, Any] = {},
) -> tuple[str, dict]:
    query = """
{
    ?[execution_id, task_id, status, updated_at] <- [[
        to_uuid($execution_id),
        to_uuid($task_id),
        $status,
        now()
    ]]

    :update executions {
        execution_id,
        task_id,
        status,
        updated_at
    }
}

"""
    return (
        query,
        {
            "task_id": str(task_id),
            "execution_id": str(execution_id),
            "status": status,
            "arguments": arguments,
        },
    )
