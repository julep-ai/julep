"""
This module contains the functionality for creating agents in the CozoDB database.
It includes functions to construct and execute datalog queries for inserting new agent records.
"""

from typing import Any, TypeVar
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import Agent, CreateAgentRequest
from ...common.utils.cozo import cozo_process_mutate_data
from ...metrics.counters import increase_counter
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        lambda e: isinstance(e, QueryException)
        and "asserted to return some results, but returned none"
        in str(e): lambda *_: HTTPException(
            detail="Developer not found. Please ensure the provided auth token (which refers to your developer_id) is valid and the developer has the necessary permissions to create an agent.",
            status_code=403,
        ),
        QueryException: partialclass(
            HTTPException,
            status_code=400,
            detail="A database query failed to return the expected results. This might occur if the requested resource doesn't exist or your query parameters are incorrect.",
        ),
        ValidationError: partialclass(
            HTTPException,
            status_code=400,
            detail="Input validation failed. Please check the provided data for missing or incorrect fields, and ensure it matches the required format.",
        ),
        TypeError: partialclass(
            HTTPException,
            status_code=400,
            detail="A type mismatch occurred. This likely means the data provided is of an incorrect type (e.g., string instead of integer). Please review the input and try again.",
        ),
    }
)
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {"id": UUID(d.pop("agent_id")), **d},
    _kind="inserted",
)
@cozo_query
@increase_counter("create_agent")
@beartype
def create_agent(
    *,
    developer_id: UUID,
    agent_id: UUID | None = None,
    data: CreateAgentRequest,
) -> tuple[list[str], dict]:
    """
    Constructs and executes a datalog query to create a new agent in the database.

    Parameters:
        agent_id (UUID | None): The unique identifier for the agent.
        developer_id (UUID): The unique identifier for the developer creating the agent.
        data (CreateAgentRequest): The data for the new agent.

    Returns:
        Agent: The newly created agent record.
    """

    agent_id = agent_id or uuid4()

    # Extract the agent data from the payload
    data.metadata = data.metadata or {}
    data.default_settings = data.default_settings or {}

    data.instructions = (
        data.instructions
        if isinstance(data.instructions, list)
        else [data.instructions]
    )

    agent_data = data.model_dump(exclude_unset=True)
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

        :insert agent_default_settings {{
            {settings_cols}
        }}
    """
    # create the agent
    # Construct a query to insert the new agent record into the agents table
    agent_query = """
        ?[agent_id, developer_id, model, name, about, metadata, instructions, created_at, updated_at] <- [
            [$agent_id, $developer_id, $model, $name, $about, $metadata, $instructions, now(), now()]
        ]

        :insert agents {
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
        default_settings_query,
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
