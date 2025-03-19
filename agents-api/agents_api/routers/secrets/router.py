"""Router for secrets."""

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection

from ...autogen.Secrets import (
    CreateSecretRequest,
    ListResponse,
    PatchSecretRequest,
    ResourceDeletedResponse,
    Secret,
    SecretsSummary,
    UpdateSecretRequest,
)
from ...dependencies.auth import Developer
from ...dependencies.developer_id import get_developer_id
from ...queries import secrets as secret_queries

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Secrets"])


@router.post("/developers/{id}/secrets")
async def create_secret(
    id: UUID,
    secret: CreateSecretRequest,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> Secret:
    """Create a new secret for a developer.

    Args:
        id: The developer ID.
        secret: The secret to create.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The created secret.

    Raises:
        HTTPException: If the developer is not authorized or the secret creation fails.
    """
    try:
        # Verify ownership
        if id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create secrets for your developer account",
            )

        # Create the secret
        result = await secret_queries.create_secret(
            conn=conn,
            developer_id=id,
            input=secret_queries.SecretInput(
                name=secret.name,
                value=secret.value,
                description=secret.description,
                metadata=secret.metadata,
                agent_id=secret.agent_id,
            ),
        )

        return Secret(
            id=result.id,
            name=result.name,
            description=result.description,
            metadata=result.metadata,
            agent_id=result.agent_id,
            developer_id=result.developer_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    except Exception as e:
        logger.error(f"Error creating secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create secret",
        )


@router.get("/developers/{id}/secrets")
async def list_secrets(
    id: UUID,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> ListResponse[SecretsSummary]:
    """List all secrets for a developer.

    Args:
        id: The developer ID.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The list of secrets.

    Raises:
        HTTPException: If the developer is not authorized or the listing fails.
    """
    try:
        # Verify ownership
        if id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only list secrets for your developer account",
            )

        # List the secrets
        results = await secret_queries.list_secrets(
            conn=conn,
            developer_id=id,
        )

        # Convert to API model
        secrets = [
            SecretsSummary(
                id=secret.id,
                name=secret.name,
                description=secret.description,
                agent_id=secret.agent_id,
                created_at=secret.created_at,
                updated_at=secret.updated_at,
            )
            for secret in results
        ]

        return ListResponse[SecretsSummary](items=secrets)

    except Exception as e:
        logger.error(f"Error listing secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list secrets",
        )


@router.get(
    "/developers/{developer_id}/secrets/{id}"
)
async def get_secret_details(
    developer_id: UUID,
    id: UUID,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> SecretsSummary:
    """Get a secret's details by ID.

    Args:
        developer_id: The developer ID.
        id: The secret ID.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The secret details.

    Raises:
        HTTPException: If the developer is not authorized or the secret is not found.
    """
    try:
        # Verify ownership
        if developer_id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own secrets",
            )

        # Get the secret
        result = await secret_queries.get_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        # Convert to API model
        return SecretsSummary(
            id=result.id,
            name=result.name,
            description=result.description,
            agent_id=result.agent_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting secret details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get secret details",
        )


@router.put(
    "/developers/{developer_id}/secrets/{id}"
)
async def update_secret(
    developer_id: UUID,
    id: UUID,
    secret: UpdateSecretRequest,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> Secret:
    """Update a secret.

    Args:
        developer_id: The developer ID.
        id: The secret ID.
        secret: The updated secret data.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The updated secret.

    Raises:
        HTTPException: If the developer is not authorized or the secret is not found.
    """
    try:
        # Verify ownership
        if developer_id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own secrets",
            )

        # Update the secret
        result = await secret_queries.update_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer_id,
            input=secret_queries.UpdateSecretInput(
                name=secret.name,
                value=secret.value,
                description=secret.description,
                metadata=secret.metadata,
                agent_id=secret.agent_id,
            ),
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        # Convert to API model
        return Secret(
            id=result.id,
            name=result.name,
            description=result.description,
            metadata=result.metadata,
            agent_id=result.agent_id,
            developer_id=result.developer_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update secret",
        )


@router.patch(
    "/developers/{developer_id}/secrets/{id}"
)
async def patch_secret(
    developer_id: UUID,
    id: UUID,
    secret: PatchSecretRequest,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> Secret:
    """Patch a secret.

    Args:
        developer_id: The developer ID.
        id: The secret ID.
        secret: The partial secret data to update.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The patched secret.

    Raises:
        HTTPException: If the developer is not authorized or the secret is not found.
    """
    try:
        # Verify ownership
        if developer_id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only patch your own secrets",
            )

        # Patch the secret
        result = await secret_queries.patch_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer_id,
            input=secret_queries.PatchSecretInput(
                name=secret.name,
                value=secret.value,
                description=secret.description,
                metadata=secret.metadata,
                agent_id=secret.agent_id,
            ),
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        # Convert to API model
        return Secret(
            id=result.id,
            name=result.name,
            description=result.description,
            metadata=result.metadata,
            agent_id=result.agent_id,
            developer_id=result.developer_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to patch secret",
        )


@router.delete(
    "/developers/{developer_id}/secrets/{id}"
)
async def delete_secret(
    developer_id: UUID,
    id: UUID,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> ResourceDeletedResponse:
    """Delete a secret.

    Args:
        developer_id: The developer ID.
        id: The secret ID.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        Deletion success response.

    Raises:
        HTTPException: If the developer is not authorized or the secret is not found.
    """
    try:
        # Verify ownership
        if developer_id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own secrets",
            )

        # Delete the secret
        deleted = await secret_queries.delete_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        return ResourceDeletedResponse(id=str(id))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete secret",
        )


# Agent-specific routes

@router.post("/agents/{id}/secrets")
async def create_agent_secret(
    id: UUID,
    secret: CreateSecretRequest,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> Secret:
    """Create a new secret for a specific agent.

    Args:
        id: The agent ID.
        secret: The secret to create.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The created secret.

    Raises:
        HTTPException: If the developer is not authorized or the secret creation fails.
    """
    try:
        # Override agent_id to ensure it matches the path parameter
        secret_input = secret_queries.SecretInput(
            name=secret.name,
            value=secret.value,
            description=secret.description,
            metadata=secret.metadata,
            agent_id=id,  # Force the agent_id to match the path
        )

        # Create the secret
        result = await secret_queries.create_secret(
            conn=conn,
            developer_id=developer.id,
            input=secret_input,
        )

        return Secret(
            id=result.id,
            name=result.name,
            description=result.description,
            metadata=result.metadata,
            agent_id=result.agent_id,
            developer_id=result.developer_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    except Exception as e:
        logger.error(f"Error creating agent secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent secret",
        )


@router.get("/agents/{id}/secrets")
async def list_agent_secrets(
    id: UUID,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> ListResponse[SecretsSummary]:
    """List all secrets available to a specific agent.

    Args:
        id: The agent ID.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The list of secrets.

    Raises:
        HTTPException: If the developer is not authorized or the listing fails.
    """
    try:
        # List the secrets for this agent (including developer-wide ones)
        results = await secret_queries.list_secrets(
            conn=conn,
            developer_id=developer.id,
            agent_id=id,
        )

        # Convert to API model
        secrets = [
            SecretsSummary(
                id=secret.id,
                name=secret.name,
                description=secret.description,
                agent_id=secret.agent_id,
                created_at=secret.created_at,
                updated_at=secret.updated_at,
            )
            for secret in results
        ]

        return ListResponse[SecretsSummary](items=secrets)

    except Exception as e:
        logger.error(f"Error listing agent secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agent secrets",
        )


@router.get(
    "/agents/{agent_id}/secrets/{id}"
)
async def get_agent_secret_details(
    agent_id: UUID,
    id: UUID,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> SecretsSummary:
    """Get an agent-specific secret's details by ID.

    Args:
        agent_id: The agent ID.
        id: The secret ID.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The secret details.

    Raises:
        HTTPException: If the developer is not authorized or the secret is not found.
    """
    try:
        # Get the secret
        result = await secret_queries.get_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer.id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        # Verify it's for the specified agent
        if result.agent_id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found for this agent",
            )

        # Convert to API model
        return SecretsSummary(
            id=result.id,
            name=result.name,
            description=result.description,
            agent_id=result.agent_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent secret details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent secret details",
        )


@router.put(
    "/agents/{agent_id}/secrets/{id}"
)
async def update_agent_secret(
    agent_id: UUID,
    id: UUID,
    secret: UpdateSecretRequest,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> Secret:
    """Update an agent-specific secret.

    Args:
        agent_id: The agent ID.
        id: The secret ID.
        secret: The updated secret data.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The updated secret.

    Raises:
        HTTPException: If the developer is not authorized or the secret is not found.
    """
    try:
        # Override agent_id to ensure it matches the path parameter
        secret_input = secret_queries.UpdateSecretInput(
            name=secret.name,
            value=secret.value,
            description=secret.description,
            metadata=secret.metadata,
            agent_id=agent_id,  # Force the agent_id to match the path
        )

        # Update the secret
        result = await secret_queries.update_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer.id,
            input=secret_input,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        # Convert to API model
        return Secret(
            id=result.id,
            name=result.name,
            description=result.description,
            metadata=result.metadata,
            agent_id=result.agent_id,
            developer_id=result.developer_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent secret",
        )


@router.patch(
    "/agents/{agent_id}/secrets/{id}"
)
async def patch_agent_secret(
    agent_id: UUID,
    id: UUID,
    secret: PatchSecretRequest,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> Secret:
    """Patch an agent-specific secret.

    Args:
        agent_id: The agent ID.
        id: The secret ID.
        secret: The partial secret data to update.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        The patched secret.

    Raises:
        HTTPException: If the developer is not authorized or the secret is not found.
    """
    try:
        # First check if the secret exists and belongs to this agent
        current_secret = await secret_queries.get_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer.id,
        )

        if not current_secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        if current_secret.agent_id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found for this agent",
            )

        # Create patch input, ensuring agent_id is preserved
        patch_input = secret_queries.PatchSecretInput(
            name=secret.name,
            value=secret.value,
            description=secret.description,
            metadata=secret.metadata,
            agent_id=agent_id,  # Force agent_id to match the path
        )

        # Patch the secret
        result = await secret_queries.patch_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer.id,
            input=patch_input,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        # Convert to API model
        return Secret(
            id=result.id,
            name=result.name,
            description=result.description,
            metadata=result.metadata,
            agent_id=result.agent_id,
            developer_id=result.developer_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching agent secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to patch agent secret",
        )


@router.delete(
    "/agents/{agent_id}/secrets/{id}"
)
async def delete_agent_secret(
    agent_id: UUID,
    id: UUID,
    developer: Annotated[Developer, Depends(get_developer_id)],
    conn: Annotated[AsyncConnection[dict[str, Any]], Depends()],
) -> ResourceDeletedResponse:
    """Delete an agent-specific secret.

    Args:
        agent_id: The agent ID.
        id: The secret ID.
        developer: The authenticated developer.
        conn: Database connection.

    Returns:
        Deletion success response.

    Raises:
        HTTPException: If the developer is not authorized or the secret is not found.
    """
    try:
        # First check if the secret exists and belongs to this agent
        current_secret = await secret_queries.get_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer.id,
        )

        if not current_secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        if current_secret.agent_id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found for this agent",
            )

        # Delete the secret
        deleted = await secret_queries.delete_secret(
            conn=conn,
            secret_id=id,
            developer_id=developer.id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        return ResourceDeletedResponse(id=str(id))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent secret",
        )
