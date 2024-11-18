from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import File
from ...dependencies.developer_id import get_developer_id
from ...models.files.get_file import get_file as get_file_query
from .router import router


@router.get("/files/{file_id}", tags=["files"])
async def get_file(
    file_id: UUID, x_developer_id: Annotated[UUID, Depends(get_developer_id)]
) -> File:
    file = get_file_query(developer_id=x_developer_id, file_id=file_id)

    # TODO: Fetch the file content from blob storage
    # file.content = await fetch_file_content(file.id)

    return file
