from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateFileRequest,
    File,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.files.create_file import create_file as create_file_query
from .router import router


@router.post("/files", status_code=HTTP_201_CREATED, tags=["files"])
async def create_file(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: CreateFileRequest,
) -> ResourceCreatedResponse:
    file: File = create_file_query(
        developer_id=x_developer_id,
        data=data,
    )

    # TODO: Upload the file content to blob storage
    # await upload_file_content(resource_created.id, data.content)

    return ResourceCreatedResponse(
        id=file.id,
        created_at=file.created_at,
        jobs=[],
    )
