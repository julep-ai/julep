from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import File
from ...dependencies.developer_id import get_developer_id
from ...queries.files.list_files import list_files as list_files_query
from .get_file import fetch_file_content
from .router import router


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
