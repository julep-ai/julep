import base64
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import File
from ...clients import async_s3
from ...dependencies.developer_id import get_developer_id
from ...queries.files.list_files import list_files as list_files_query
from .router import router


async def fetch_file_content(file_id: UUID) -> str:
    """Fetch file content from blob storage using the file ID as the key"""
    async with async_s3.setup() as client:
        key = str(file_id)
        content = await client.get_object(Bucket=async_s3.blob_store_bucket, Key=key)
        return base64.b64encode(content).decode("utf-8")


# TODO: Use streaming for large payloads
@router.get("/files", tags=["files"])
async def list_files(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> list[File]:
    files = await list_files_query(developer_id=x_developer_id)

    # Fetch the file content from blob storage
    for file in files:
        file.content = await fetch_file_content(file.id)

    return files
