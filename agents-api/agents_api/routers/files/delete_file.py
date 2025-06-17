from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_202_ACCEPTED

from ...autogen.openapi_model import ResourceDeletedResponse
from ...clients import async_s3
from ...dependencies.developer_id import get_developer_id
from ...queries.files.delete_file import delete_file as delete_file_query
from .router import router


async def delete_file_content(file_id: UUID) -> None:
    """Delete file content from blob storage using the file ID as the key"""
    client = await async_s3.setup()
    key = str(file_id)

    await client.delete_object(Bucket=async_s3.blob_store_bucket, Key=key)


@router.delete("/files/{file_id}", status_code=HTTP_202_ACCEPTED, tags=["files"])
async def delete_file(
    file_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceDeletedResponse:
    resource_deleted = await delete_file_query(developer_id=x_developer_id, file_id=file_id)

    # Delete the file content from blob storage
    await delete_file_content(file_id)

    return resource_deleted


@router.delete(
    "/users/{user_id}/files/{file_id}", status_code=HTTP_202_ACCEPTED, tags=["files"]
)
async def delete_user_file(
    file_id: UUID,
    user_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceDeletedResponse:
    """Delete a user-owned file."""
    # AIDEV-NOTE: added user-specific file deletion
    resource_deleted = await delete_file_query(
        developer_id=x_developer_id,
        file_id=file_id,
        owner_type="user",
        owner_id=user_id,
    )

    await delete_file_content(file_id)

    return resource_deleted


@router.delete(
    "/agents/{agent_id}/files/{file_id}", status_code=HTTP_202_ACCEPTED, tags=["files"]
)
async def delete_agent_file(
    file_id: UUID,
    agent_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceDeletedResponse:
    """Delete an agent-owned file."""
    # AIDEV-NOTE: added agent-specific file deletion
    resource_deleted = await delete_file_query(
        developer_id=x_developer_id,
        file_id=file_id,
        owner_type="agent",
        owner_id=agent_id,
    )

    await delete_file_content(file_id)

    return resource_deleted
