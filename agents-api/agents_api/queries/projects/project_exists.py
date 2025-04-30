"""
This module contains the functionality for creating agents in the PostgreSQL database.
It includes functions to construct and execute SQL queries for inserting new agent records.
"""

from uuid import UUID

from beartype import beartype

from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions


# Define the raw SQL query for checking project existence
check_project_query = """
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM projects 
            WHERE developer_id = $1 AND canonical_name = $2
        ) THEN
            TRUE
        ELSE
            FALSE
    END as project_exists;
"""


@rewrap_exceptions(common_db_exceptions("project", ["exists"]))
@pg_query
@beartype
async def project_exists(developer_id: UUID, canonical_name: str) -> tuple[str, list]:
    return (
        check_project_query,
        [developer_id, canonical_name]
    )
