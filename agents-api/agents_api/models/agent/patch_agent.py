from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import PatchAgentRequest, ResourceUpdatedResponse
from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow
from ...metrics.counters import increase_counter
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["agent_id"], "jobs": [], **d},
    _kind="inserted",
)
@cozo_query
@increase_counter("patch_agent")
@beartype
def patch_agent(
    *,
    agent_id: UUID,
    developer_id: UUID,
    data: PatchAgentRequest,
) -> tuple[list[str], dict]:
    """Patches agent data based on provided updates.

    Parameters:
        agent_id (UUID): The unique identifier for the agent.
        developer_id (UUID): The unique identifier for the developer.
        default_settings (dict, optional): Default settings to apply to the agent.
        **update_data: Arbitrary keyword arguments representing data to update.

    Returns:
        ResourceUpdatedResponse: The updated agent data.
    """
    update_data = data.model_dump(exclude_unset=True)

    # Construct the query for updating agent information in the database.
    # Agent update query
    metadata = update_data.pop("metadata", {}) or {}
    default_settings = update_data.pop("default_settings", {}) or {}
    agent_update_cols, agent_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "agent_id": str(agent_id),
            "developer_id": str(developer_id),
            "updated_at": utcnow().timestamp(),
        }
    )

    update_query = f"""
        # update the agent
        input[{agent_update_cols}] <- $agent_update_vals

        ?[{agent_update_cols}, metadata] := 
            input[{agent_update_cols}],
            *agents {{
                agent_id: to_uuid($agent_id),
                metadata: md,
            }},
            metadata = concat(md, $metadata)

        :update agents {{
            {agent_update_cols},
            metadata,
        }}
        :returning
    """

    # Construct the query for updating agent's default settings in the database.
    # Settings update query
    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": str(agent_id),
        }
    )

    settings_update_query = f"""
        # update the agent settings
        ?[{settings_cols}] <- $settings_vals

        :update agent_default_settings {{
            {settings_cols}
        }}
    """

    # Combine agent and settings update queries if default settings are provided.
    # Combine the queries
    queries = [update_query]

    if len(default_settings) != 0:
        queries.insert(0, settings_update_query)

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        *queries,
    ]

    return (
        queries,
        {
            "agent_update_vals": agent_update_vals,
            "settings_vals": settings_vals,
            "metadata": metadata,
            "agent_id": str(agent_id),
        },
    )
