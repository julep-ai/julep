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

# AIDEV-NOTE: Decode and stream base64 file content directly to S3 to avoid
# buffering entire payloads in memory.


async def _iter_decoded(content: str, chunk_size: int = 65536):
    """Yield decoded bytes from a base64 string in chunks."""
    buffer = ""
    for i in range(0, len(content), chunk_size):
        buffer += content[i : i + chunk_size]
        to_decode_len = len(buffer) - (len(buffer) % 4)
        if to_decode_len:
            chunk = buffer[:to_decode_len]
            buffer = buffer[to_decode_len:]
            yield base64.b64decode(chunk)
    if buffer:
        yield base64.b64decode(buffer)


async def upload_file_content(file_id: UUID, content: str) -> None:
    """Upload file content to blob storage using the file ID as the key."""
    key = str(file_id)
    client = await async_s3.setup()

    await client.put_object(
        Bucket=async_s3.blob_store_bucket,
        Key=key,
        Body=_iter_decoded(content),
    )


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
