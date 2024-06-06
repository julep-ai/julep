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
def update_task_query(
    task_id: UUID,
    developer_id: UUID,
    agent_id: UUID,
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    tools_available: List[UUID] = [],
    workflows: List[Dict[str, Any]] = [],
) -> tuple[str, dict]:
    # NOT TO IMPLEMENT FOR NOW
    raise NotImplementedError("Not implemented yet")
