"""
This module contains the functionality for creating agents in the CozoDB database.
It includes functions to construct and execute datalog queries for inserting new agent records.
"""

from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import Agent, CreateOrUpdateAgentRequest
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
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
    Agent, one=True, transform=lambda d: {"id": UUID(d.pop("agent_id")), **d}
)
@cozo_query
@beartype
def create_or_update_agent(
    *,
    developer_id: UUID,
    agent_id: UUID,
    data: CreateOrUpdateAgentRequest,
) -> tuple[list[str | None], dict]:
    """
    Constructs and executes a datalog query to create a new agent in the database.

    Parameters:
    - agent_id (UUID): The unique identifier for the agent.
    - developer_id (UUID): The unique identifier for the developer creating the agent.
    - name (str): The name of the agent.
    - about (str): A description of the agent.
    - instructions (list[str], optional): A list of instructions for using the agent. Defaults to an empty list.
    - model (str, optional): The model identifier for the agent. Defaults to "gpt-4o".
    - metadata (dict, optional): A dictionary of metadata for the agent. Defaults to an empty dict.
    - default_settings (dict, optional): A dictionary of default settings for the agent. Defaults to an empty dict.
    - client (CozoClient, optional): The CozoDB client instance to use for the query. Defaults to a preconfigured client instance.

    Returns:
    Agent: The newly created agent record.
    """

    # Extract the agent data from the payload
    data.metadata = data.metadata or {}
    data.instructions = (
        data.instructions
        if isinstance(data.instructions, list)
        else [data.instructions]
    )
    data.default_settings = data.default_settings or {}

    agent_data = data.model_dump()
    default_settings = agent_data.pop("default_settings")

    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": str(agent_id),
        }
    )

    # Create default agent settings
    # Construct a query to insert default settings for the new agent
    default_settings_query = f"""
        ?[{settings_cols}] <- $settings_vals

        :put agent_default_settings {{
            {settings_cols}
        }}
    """
    # create the agent
    # Construct a query to insert the new agent record into the agents table
    agent_query = """
        input[agent_id, developer_id, model, name, about, metadata, instructions, updated_at] <- [
            [$agent_id, $developer_id, $model, $name, $about, $metadata, $instructions, now()]
        ]

        ?[agent_id, developer_id, model, name, about, metadata, instructions, created_at, updated_at] :=
            input[_agent_id, developer_id, model, name, about, metadata, instructions, updated_at],
            *agents{
                agent_id,
                created_at,
            },
            agent_id = to_uuid(_agent_id),

        ?[agent_id, developer_id, model, name, about, metadata, instructions, created_at, updated_at] :=
            input[_agent_id, developer_id, model, name, about, metadata, instructions, updated_at],
            not *agents{
                agent_id,
            }, created_at = now(),
            agent_id = to_uuid(_agent_id),

        :put agents {
            developer_id,
            agent_id =>
            model,
            name,
            about,
            metadata,
            instructions,
            created_at,
            updated_at,
        }
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        default_settings_query if default_settings else None,
        agent_query,
    ]

    return (
        queries,
        {
            "settings_vals": settings_vals,
            "agent_id": str(agent_id),
            "developer_id": str(developer_id),
            **agent_data,
        },
    )
