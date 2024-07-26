"""This module contains functions for creating tools in the CozoDB database."""

from uuid import UUID, uuid4

from beartype import beartype

from ...autogen.openapi_model import CreateToolRequest, Tool

from ..utils import (
    cozo_query,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


@wrap_in_class(
    Tool,
    transform=lambda d: {
        "id": UUID(d.pop("tool_id")),
        d["type"]: d.pop("spec"),
        **d,
    },
)
@cozo_query
@beartype
def create_tools(
    *,
    developer_id: UUID,
    agent_id: UUID,
    data: list[CreateToolRequest],
) -> tuple[str, dict]:
    """
    Constructs a datalog query for inserting tool records into the 'agent_functions' relation in the CozoDB.

    Parameters:
    - agent_id (UUID): The unique identifier for the agent.
    - data (list[CreateToolRequest]): A list of function definitions to be inserted.

    Returns:
    list[Tool]
    """

    tools_data = [
        [
            str(agent_id),
            str(uuid4()),
            tool.type,
            tool.name,
            getattr(tool, tool.type).dict(),
        ]
        for tool in data
    ]

    # Datalog query for inserting new tool records into the 'agent_functions' relation
    create_query = """
        ?[agent_id, tool_id, type, name, spec] <- $records

        :insert tools {
            agent_id,
            tool_id,
            type,
            name,
            spec,
        }
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        create_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (query, {"records": tools_data})
