import base64
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import File
from ...clients import s3
from ...dependencies.developer_id import get_developer_id
from ...models.files.get_file import get_file as get_file_query
from .router import router


async def fetch_file_content(file_id: UUID) -> str:
    """Fetch file content from blob storage using the file ID as the key"""
    s3.setup()
    key = str(file_id)
    content = s3.get_object(key)
    return base64.b64encode(content).decode("utf-8")


@router.get("/files/{file_id}", tags=["files"])
async def get_file(
    file_id: UUID, x_developer_id: Annotated[UUID, Depends(get_developer_id)]
) -> File:
    file = get_file_query(developer_id=x_developer_id, file_id=file_id)

    # Fetch the file content from blob storage
    file.content = await fetch_file_content(file.id)

    return file
