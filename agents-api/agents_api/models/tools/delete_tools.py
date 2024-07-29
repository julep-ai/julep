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
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {"id": d["tool_id"], "deleted_at": utcnow(), "jobs": [], **d},
)
@cozo_query
@beartype
def delete_tool(
    *,
    developer_id: UUID,
    agent_id: UUID,
    tool_id: UUID,
) -> tuple[str, dict]:
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    delete_query = """
        # Delete function
        ?[tool_id, agent_id] <- [[
            to_uuid($tool_id),
            to_uuid($agent_id),
        ]]

        :delete tools {
            tool_id,
            agent_id,
        }
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        delete_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (query, {"tool_id": tool_id, "agent_id": agent_id})
