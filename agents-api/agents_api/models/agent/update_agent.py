from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import ResourceUpdatedResponse, UpdateAgentRequest
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


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
    _kind="replaced",
)
@cozo_query
@beartype
def update_agent(
    *,
    agent_id: UUID,
    developer_id: UUID,
    data: UpdateAgentRequest,
) -> tuple[list[str], dict]:
    """
    Constructs and executes a datalog query to update an agent and its default settings in the 'cozodb' database.

    Parameters:
    - agent_id (UUID): The unique identifier of the agent to be updated.
    - developer_id (UUID): The unique identifier of the developer associated with the agent.
    - data (UpdateAgentRequest): The request payload containing the updated agent data.
    - client (CozoClient, optional): The database client used to execute the query. Defaults to a pre-configured client instance.

    Returns:
    ResourceUpdatedResponse: The updated agent data.
    """
    default_settings = (
        data.default_settings.model_dump(exclude_none=True)
        if data.default_settings
        else {}
    )
    update_data = data.model_dump()

    # Remove default settings from the agent update data
    update_data.pop("default_settings", None)

    agent_id = str(agent_id)
    developer_id = str(developer_id)
    update_data["instructions"] = update_data.get("instructions", [])
    update_data["instructions"] = (
        update_data["instructions"]
        if isinstance(update_data["instructions"], list)
        else [update_data["instructions"]]
    )

    # Construct the agent update part of the query with dynamic columns and values based on `update_data`.
    # Agent update query
    agent_update_cols, agent_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "agent_id": agent_id,
            "developer_id": developer_id,
        }
    )

    update_query = f"""
        # update the agent
        input[{agent_update_cols}] <- $agent_update_vals
        original[created_at] := *agents{{
            developer_id: to_uuid($developer_id),
            agent_id: to_uuid($agent_id),
            created_at,
        }},

        ?[created_at, updated_at, {agent_update_cols}] :=
            input[{agent_update_cols}],
            original[created_at],
            updated_at = now(),

        :put agents {{
            created_at,
            updated_at,
            {agent_update_cols}
        }}
        :returning
    """

    # Construct the settings update part of the query if `default_settings` are provided.
    # Settings update query
    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": agent_id,
        }
    )

    settings_update_query = f"""
        # update the agent settings
        ?[{settings_cols}] <- $settings_vals

        :put agent_default_settings {{
            {settings_cols}
        }}
    """

    # Combine agent and settings update queries into a single query string.
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
            "agent_id": agent_id,
            "developer_id": developer_id,
        },
    )
