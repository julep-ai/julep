"""
This module contains the functionality for creating a new Task in the 'cozodb` database.
It constructs and executes a datalog query to insert Task data.
"""

from uuid import UUID
from typing import List, Dict, Any
from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def create_task_query(
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID,
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    tools_available: List[UUID] = [],
    workflows: List[Dict[str, Any]] = [],
) -> tuple[str, dict]:
    # TODO: Check for agent in developer ID; Assert whether dev can access agent and by relation the task
    query = """
{
    ?[agent_id, task_id, name, description, input_schema, tools_available, workflows] <- [[
        to_uuid($agent_id), to_uuid($task_id), $name, $description, $input_schema, $tools_available, $workflows
    ]]

    :insert tasks {
        agent_id,
        task_id,
        name,
        description,
        input_schema,
        tools_available,
        workflows
    }

    :returning
}
"""

    return (
        query,
        {
            "agent_id": str(agent_id),
            "task_id": str(task_id),
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "tools_available": tools_available,
            "workflows": workflows,
        },
    )
