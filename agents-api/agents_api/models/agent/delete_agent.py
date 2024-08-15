"""
This module contains the implementation of the delete_agent_query function, which is responsible for deleting an agent and its related default settings from the CozoDB database.
"""

from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
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
        lambda e: isinstance(e, QueryException)
        and "asserted to return some results, but returned none"
        in str(e): lambda *_: HTTPException(
            detail="developer not found or doesnt own resource", status_code=404
        ),
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": UUID(d.pop("agent_id")),
        "deleted_at": utcnow(),
        "jobs": [],
    },
    _kind="deleted",
)
@cozo_query
@beartype
def delete_agent(*, developer_id: UUID, agent_id: UUID) -> tuple[list[str], dict]:
    """
    Constructs and returns a datalog query for deleting an agent and its default settings from the database.

    Parameters:
    - developer_id (UUID): The UUID of the developer owning the agent.
    - agent_id (UUID): The UUID of the agent to be deleted.
    - client (CozoClient, optional): An instance of the CozoClient to execute the query.

    Returns:
    - ResourceDeletedResponse: The response indicating the deletion of the agent.
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        """
        # Delete docs
        ?[owner_id, owner_type, doc_id] :=
            *docs{
                owner_type,
                owner_id,
                doc_id,
            },
            owner_id = to_uuid($agent_id),
            owner_type = "agent"

        :delete docs {
            owner_type,
            owner_id,
            doc_id
        }
        :returning
        """,
        """
        # Delete tools
        ?[agent_id, tool_id] :=
            *tools{
                agent_id,
                tool_id,
            }, agent_id = to_uuid($agent_id)

        :delete tools {
            agent_id,
            tool_id
        }
        :returning
        """,
        """
        # Delete default agent settings
        ?[agent_id] <- [[$agent_id]]

        :delete agent_default_settings {
            agent_id
        }
        :returning
        """,
        """
        # Delete the agent
        ?[agent_id, developer_id] <- [[$agent_id, $developer_id]]

        :delete agents {
            developer_id,
            agent_id
        }
        :returning
        """,
    ]

    return (queries, {"agent_id": str(agent_id), "developer_id": str(developer_id)})
