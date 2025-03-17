"""
Utilities for working with transitions output stored in large objects (LO).

This module provides functions to work with transition output data after migration
from JSONB to LO (large object) storage using PostgreSQL's lo extension.
"""

from typing import Any, Dict, List, Optional, cast

import json
import asyncpg
from uuid import UUID


async def get_transition_output(
    conn: asyncpg.Connection, transition_id: UUID
) -> Dict[str, Any]:
    """
    Fetch transition output data from a large object.

    This function handles retrieving the output data for a transition after
    the migration from JSONB to large objects.

    Args:
        conn: The database connection
        transition_id: The ID of the transition to fetch output for

    Returns:
        The output data as a dictionary, or an empty dict if none exists
    """
    query = """
    SELECT
        output_oid,
        get_transition_output(output_oid) as parsed_output
    FROM transitions
    WHERE transition_id = $1
    """
    
    row = await conn.fetchrow(query, transition_id)
    if not row or not row["parsed_output"]:
        return {}
        
    data = json.loads(row["parsed_output"])
    return cast(Dict[str, Any], data)


async def store_transition_output(
    conn: asyncpg.Connection, data: Dict[str, Any]
) -> Optional[int]:
    """
    Store transition output data in a large object.

    This function handles storing output data for a transition after
    the migration from JSONB to large objects.

    Args:
        conn: The database connection
        data: The output data to store

    Returns:
        The OID of the created large object, or None if no data was provided
    """
    if not data:
        return None
        
    # Use the PostgreSQL function to create and store the large object
    oid = await conn.fetchval("SELECT set_transition_output($1)", json.dumps(data))
    return oid


async def update_transition_output(
    conn: asyncpg.Connection, transition_id: UUID, new_data: Dict[str, Any]
) -> None:
    """
    Update transition output data.

    This function handles updating output data for a transition after
    the migration from JSONB to large objects.

    Args:
        conn: The database connection
        transition_id: The ID of the transition to update
        new_data: The new output data to store
    """
    # Create a new large object with the data
    oid = await store_transition_output(conn, new_data)
    
    # Update the transition record to point to the new large object
    # The old one will be cleaned up by the lo_manage trigger
    await conn.execute(
        "UPDATE transitions SET output_oid = $1 WHERE transition_id = $2",
        oid, transition_id
    )


async def bulk_get_transition_outputs(
    conn: asyncpg.Connection, transition_ids: List[UUID]
) -> Dict[UUID, Dict[str, Any]]:
    """
    Fetch multiple transition outputs in bulk.

    Args:
        conn: The database connection
        transition_ids: List of transition IDs to fetch outputs for

    Returns:
        Dictionary mapping transition IDs to their output data
    """
    if not transition_ids:
        return {}
        
    query = """
    SELECT
        transition_id,
        get_transition_output(output_oid) as output
    FROM transitions
    WHERE transition_id = ANY($1)
    """
    
    rows = await conn.fetch(query, transition_ids)
    result = {}
    
    for row in rows:
        if row["output"]:
            result[row["transition_id"]] = cast(Dict[str, Any], json.loads(row["output"]))
        else:
            result[row["transition_id"]] = {}
            
    return result