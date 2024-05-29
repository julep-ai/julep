from uuid import UUID

from ..utils import cozo_query
from typing import Literal, Dict, Any


@cozo_query
def create_execution_query(
    task_id: UUID,
    execution_id: UUID,
    status: Literal[
        "queued", "starting", "running", "waiting-for-input", "success", "failed"
    ] = "queued",
    arguments: Dict[str, Any] = {},
) -> tuple[str, dict]:
    query = """"""
    return (
        query,
        {
            "task_id": str(task_id),
            "execution_id": str(execution_id),
            "status": status,
            "arguments": arguments,
        },
    )
