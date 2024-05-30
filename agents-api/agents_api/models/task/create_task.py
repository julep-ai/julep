"""
This module contains the functionality for creating a new Task in the 'cozodb` database.
It constructs and executes a datalog query to insert Task data.
"""

from uuid import UUID
from typing import List, Optional, Dict, Any


from ..utils import cozo_query


@cozo_query
def create_task_query(
    task_id: UUID,
    developer_id: UUID,
    agent_id: UUID,
    name: str,
    description: str,
    input_schema: Dict[str, any],
    tools_available: List[UUID] = [],
    workflows: List[Dict[str, Any]] = [],
) -> tuple[str, dict]:
    pass
