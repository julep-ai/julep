from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_202_ACCEPTED

from ...autogen.openapi_model import ResourceDeletedResponse
from ...dependencies.developer_id import get_developer_id
from ...queries.projects.delete_project import delete_project as delete_project_query
from .router import router


@router.delete("/projects/{project_id}", status_code=HTTP_202_ACCEPTED, tags=["projects"])
async def delete_project(
    project_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceDeletedResponse:
    """Delete a project.
    
    Args:
        project_id: ID of the project to delete
        x_developer_id: Developer ID from header
        
    Returns:
        ResourceDeletedResponse: The deleted project information
    """
    return await delete_project_query(
        developer_id=x_developer_id,
        project_id=project_id,
    ) 