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
    await async_s3.setup()
    key = str(file_id)
    await async_s3.delete_object(key)


@router.delete("/files/{file_id}", status_code=HTTP_202_ACCEPTED, tags=["files"])
async def delete_file(
    file_id: UUID, x_developer_id: Annotated[UUID, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    resource_deleted = delete_file_query(developer_id=x_developer_id, file_id=file_id)

    # Delete the file content from blob storage
    await delete_file_content(file_id)

    return resource_deleted
