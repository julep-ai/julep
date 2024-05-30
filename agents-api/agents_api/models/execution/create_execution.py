from uuid import UUID

from ..utils import cozo_query
from typing import Literal, Dict, Any


@cozo_query
def create_execution_query(
    agent_id: UUID,
    task_id: UUID,
    execution_id: UUID,
    developer_id: UUID,
    status: Literal[
        "queued", "starting", "running", "waiting-for-input", "success", "failed"
    ] = "queued",
    arguments: Dict[str, Any] = {},
) -> tuple[str, dict]:
    # TODO: Check for agent in developer ID; Assert whether dev can access agent and by relation the task

    query = """
{
    ?[task_id, execution_id, status, arguments] <- [[
        to_uuid($task_id),
        to_uuid($execution_id),
        $status,
        $arguments
    ]]

    :insert executions {
        task_id,
        execution_id,
        status,
        arguments
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
