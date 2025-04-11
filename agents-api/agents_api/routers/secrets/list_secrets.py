"""List secrets endpoint."""

from uuid import UUID

from ...autogen.openapi_model import Secret
from ...queries.secrets import list_secrets as list_secrets_query
from .router import router


@router.get("/developers/{developer_id}/secrets", response_model=list[Secret])
async def list_developer_secrets(
    developer_id: UUID,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[Secret]:
    """List all secrets for a developer.

    Args:
        developer_id: ID of the developer whose secrets to list
        limit: Maximum number of secrets to return
        offset: Number of secrets to skip

    Returns:
        List of secrets
    """
    return await list_secrets_query(
        developer_id=developer_id,
        limit=limit,
        offset=offset,
    )


@router.get("/agents/{agent_id}/secrets", response_model=list[Secret])
async def list_agent_secrets(
    agent_id: UUID,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[Secret]:
    """List all secrets for an agent.

    Args:
        agent_id: ID of the agent whose secrets to list
        limit: Maximum number of secrets to return
        offset: Number of secrets to skip

    Returns:
        List of secrets
    """
    return await list_secrets_query(
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )
