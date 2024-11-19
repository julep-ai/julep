import base64
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateFileRequest,
    File,
    ResourceCreatedResponse,
)
from ...clients import s3
from ...dependencies.developer_id import get_developer_id
from ...models.files.create_file import create_file as create_file_query
from .router import router


async def upload_file_content(file_id: UUID, content: str) -> None:
    """Upload file content to blob storage using the file ID as the key"""
    s3.setup()
    key = str(file_id)
    content_bytes = base64.b64decode(content)
    s3.add_object(key, content_bytes)


@router.post("/files", status_code=HTTP_201_CREATED, tags=["files"])
async def create_file(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: CreateFileRequest,
) -> ResourceCreatedResponse:
    file: File = create_file_query(
        developer_id=x_developer_id,
        data=data,
    )

    # Upload the file content to blob storage using the file ID as the key
    await upload_file_content(file.id, data.content)

    return ResourceCreatedResponse(
        id=file.id,
        created_at=file.created_at,
        jobs=[],
    )
