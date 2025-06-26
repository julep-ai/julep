from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateProjectRequest,
    Project,
)
from ...dependencies.developer_id import get_developer_id
from ...queries.projects.create_project import create_project as create_project_query
from .router import router


@router.post("/projects", status_code=HTTP_201_CREATED, tags=["projects"])
async def create_project(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: CreateProjectRequest,
) -> Project:
    return await create_project_query(
        developer_id=x_developer_id,
        data=data,
    )
