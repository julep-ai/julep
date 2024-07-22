"""
This module contains the functionality for creating agents in the CozoDB database.
It includes functions to construct and execute datalog queries for inserting new agent records.
"""

from uuid import UUID, uuid4

from beartype import beartype

from ...autogen.openapi_model import Agent, CreateAgentRequest
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import cozo_query, verify_developer_id_query, wrap_in_class


@wrap_in_class(Agent, one=True, transform=lambda d: {"id": UUID(d.pop("agent_id")), **d})
@cozo_query
@beartype
def create_agent_query(
    *,
    developer_id: UUID,
    agent_id: UUID | None = None,
    create_agent: CreateAgentRequest,
) -> tuple[str, dict]:
    """
    Constructs and executes a datalog query to create a new agent in the database.

    Parameters:
    - agent_id (UUID): The unique identifier for the agent.
    - developer_id (UUID): The unique identifier for the developer creating the agent.
    - name (str): The name of the agent.
    - about (str): A description of the agent.
    - instructions (list[str], optional): A list of instructions for using the agent. Defaults to an empty list.
    - model (str, optional): The model identifier for the agent. Defaults to "julep-ai/samantha-1-turbo".
    - metadata (dict, optional): A dictionary of metadata for the agent. Defaults to an empty dict.
    - default_settings (dict, optional): A dictionary of default settings for the agent. Defaults to an empty dict.
    - client (CozoClient, optional): The CozoDB client instance to use for the query. Defaults to a preconfigured client instance.

    Returns:
    Agent: The newly created agent record.
    """

    agent_id = agent_id or uuid4()

    # Extract the agent data from the payload
    create_agent.metadata = create_agent.metadata or {}
    create_agent.instructions = create_agent.instructions if isinstance(create_agent.instructions, list) else [create_agent.instructions]
    create_agent.default_settings = create_agent.default_settings or {}

    agent_data = create_agent.model_dump()
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

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (
        query,
        {
            "settings_vals": settings_vals,
            "agent_id": str(agent_id),
            "developer_id": str(developer_id),
            **agent_data,
        },
    )
