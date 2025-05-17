import base64
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import File
from ...clients import async_s3
from ...dependencies.developer_id import get_developer_id
from ...queries.files.get_file import get_file as get_file_query
from .router import router

# AIDEV-NOTE: Stream file bytes from S3 and encode to base64 to avoid loading
# entire files into memory.


async def fetch_file_content(file_id: UUID) -> str:
    """Fetch file content from blob storage using the file ID as the key."""
    client = await async_s3.setup()

    key = str(file_id)
    result = await client.get_object(Bucket=async_s3.blob_store_bucket, Key=key)

    encoded = bytearray()
    async for chunk in result["Body"].iter_chunks():
        encoded.extend(base64.b64encode(chunk))

    return encoded.decode("utf-8")


@router.get("/files/{file_id}", tags=["files"])
async def get_file(
    file_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> File:
    file = await get_file_query(developer_id=x_developer_id, file_id=file_id)

    # Fetch the file content from blob storage
    file.content = await fetch_file_content(file.id)

    return file
