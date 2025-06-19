import base64
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import File
from ...clients import async_s3
from ...dependencies.developer_id import get_developer_id
from ...queries.files.get_file import get_file as get_file_query
from .router import router


# TODO: Use streaming for large payloads and file ID formatting
async def fetch_file_content(file_id: UUID) -> str:
    """Fetch file content from blob storage using the file ID as the key"""
    client = await async_s3.setup()

    key = str(file_id)
    result = await client.get_object(Bucket=async_s3.blob_store_bucket, Key=key)
    content = await result["Body"].read()

    return base64.b64encode(content).decode("utf-8")


# TODO: Use streaming for large payloads
@router.get("/files/{file_id}", tags=["files"])
async def get_file(
    file_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> File:
    file = await get_file_query(developer_id=x_developer_id, file_id=file_id)

    # Fetch the file content from blob storage
    file.content = await fetch_file_content(file.id)

    return file
