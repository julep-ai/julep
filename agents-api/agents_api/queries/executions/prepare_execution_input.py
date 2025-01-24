from uuid import UUID

from beartype import beartype

from ...common.protocol.models import ExecutionInput
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query to prepare execution input
prepare_execution_input_query = """
SELECT * FROM
(
    SELECT to_jsonb(a) AS agent FROM (
        SELECT * FROM agents
        WHERE
            developer_id = $1  AND
            agent_id = (
                SELECT agent_id FROM tasks
                WHERE developer_id = $1 AND task_id = $2
                LIMIT 1
            )
        LIMIT 1
    ) a
) AS agent,
(
    SELECT COALESCE(jsonb_agg(r), '[]'::jsonb) AS tools FROM (
        SELECT * FROM tools
        WHERE
            developer_id = $1 AND
            task_id = $2
    ) r
) AS tools,
(
    SELECT to_jsonb(e) AS execution FROM (
        SELECT * FROM latest_executions
        WHERE
            developer_id = $1 AND
            task_id = $2 AND
            execution_id = $3
        LIMIT 1
    ) e
) AS execution;
"""


@rewrap_exceptions(common_db_exceptions("execution_data", ["get"]))
@wrap_in_class(
    ExecutionInput,
    one=True,
    transform=lambda d: {
        **d,
        # "task": {
        #     "tools": d["tools"],
        #     **d["task"],
        # },
        "developer_id": d["agent"]["developer_id"],
        "agent": {
            "id": d["agent"]["agent_id"],
            **d["agent"],
        },
        "agent_tools": [
            {tool["type"]: tool.pop("spec"), **tool} for tool in d["tools"] if tool is not None
        ],
        "arguments": d["execution"]["input"],
        "execution": {
            "id": d["execution"]["execution_id"],
            **d["execution"],
        },
    },
)
@pg_query
@beartype
async def prepare_execution_input(
    *,
    developer_id: UUID,
    task_id: UUID,
    execution_id: UUID,
) -> tuple[str, list]:
    """
    Prepare the execution input for a given task.

    Parameters:
        developer_id (UUID): The ID of the developer.
        task_id (UUID): The ID of the task.
        execution_id (UUID): The ID of the execution.

    Returns:
        tuple[str, list]: SQL query and parameters for preparing the execution input.
    """
    return (
        prepare_execution_input_query,
        [
            str(developer_id),
            str(task_id),
            str(execution_id),
        ],
    )
