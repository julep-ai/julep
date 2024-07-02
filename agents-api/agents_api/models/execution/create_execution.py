from typing import Literal, Dict, Any
from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def create_execution_query(
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID,
    execution_id: UUID,
    session_id: UUID | None = None,
    status: Literal[
        "pending",
        "queued",
        "starting",
        "running",
        "awaiting_input",
        "succeeded",
        "failed",
    ] = "pending",
    arguments: Dict[str, Any] = {},
) -> tuple[str, dict]:
    # TODO: Check for agent in developer ID; Assert whether dev can access agent and by relation the task

    query = """
{
    ?[task_id, execution_id, session_id, status, arguments] :=
        task_id = to_uuid($task_id),
        execution_id = to_uuid($execution_id),
        session_id = if(is_null($session_id), null, to_uuid($session_id)),
        status = $status,
        arguments = $arguments

    :insert executions {
        task_id,
        execution_id,
        session_id,
        status,
        arguments
    }

    :returning
}
"""
    return (
        query,
        {
            "task_id": str(task_id),
            "execution_id": str(execution_id),
            "session_id": str(session_id) if session_id is not None else None,
            "status": status,
            "arguments": arguments,
        },
    )
