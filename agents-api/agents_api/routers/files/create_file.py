import base64
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import CreateFileRequest, File
from ...clients import async_s3
from ...dependencies.developer_id import get_developer_id
from ...queries.files.create_file import create_file as create_file_query
from .router import router


async def upload_file_content(file_id: UUID, content: str) -> None:
    """Upload file content to blob storage using the file ID as the key"""
    key = str(file_id)
    content_bytes = base64.b64decode(content)

    client = await async_s3.setup()

    await client.put_object(
        Bucket=async_s3.blob_store_bucket, Key=key, Body=content_bytes
    )


# TODO: Use streaming for large payloads
@router.post("/files", status_code=HTTP_201_CREATED, tags=["files"])
async def create_file(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: CreateFileRequest,
) -> File:
    file: File = await create_file_query(
        developer_id=x_developer_id,
        data=data,
    )

    # Upload the file content to blob storage using the file ID as the key
    await upload_file_content(file.id, data.content)

    return file
