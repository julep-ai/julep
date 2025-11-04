"""
Test cases for project deletion functionality.
"""

import pytest
from uuid import uuid4

from agents_api.queries.projects.delete_project import delete_project
from tests.fixtures import pg_dsn, test_developer, test_project


@pytest.mark.asyncio
async def test_delete_project_success(dsn=pg_dsn, developer=test_developer, project=test_project):
    """Test that a project can be successfully deleted."""
    # Create a new project to delete (not the default one)
    from agents_api.queries.projects.create_project import create_project
    from agents_api.autogen.openapi_model import CreateProjectRequest
    
    create_data = CreateProjectRequest(
        name="Test Project to Delete",
        canonical_name="test-delete-project",
        metadata={"test": True}
    )
    
    created_project = await create_project(
        developer_id=developer.developer_id,
        data=create_data
    )
    
    # Delete the project
    result = await delete_project(
        developer_id=developer.developer_id,
        project_id=created_project.id
    )
    
    # Verify the result
    assert result.id == created_project.id
    assert result.deleted_at is not None
    assert result.jobs == []


@pytest.mark.asyncio
async def test_delete_project_not_found(dsn=pg_dsn, developer=test_developer):
    """Test that deleting a non-existent project raises an appropriate error."""
    non_existent_project_id = uuid4()
    
    with pytest.raises(Exception) as exc_info:
        await delete_project(
            developer_id=developer.developer_id,
            project_id=non_existent_project_id
        )
    
    # The exact exception type and message may vary based on the database layer
    assert exc_info.value is not None


@pytest.mark.asyncio
async def test_delete_project_wrong_developer(dsn=pg_dsn, developer=test_developer, project=test_project):
    """Test that deleting a project with wrong developer ID raises an error."""
    wrong_developer_id = uuid4()
    
    with pytest.raises(Exception) as exc_info:
        await delete_project(
            developer_id=wrong_developer_id,
            project_id=project.id
        )
    
    # The exact exception type and message may vary based on the database layer
    assert exc_info.value is not None 