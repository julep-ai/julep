# Tests for entry queries

import pytest
from agents_api.autogen.openapi_model import CreateFileRequest, File
from agents_api.clients.pg import create_db_pool
from agents_api.queries.files.create_file import create_file
from agents_api.queries.files.delete_file import delete_file
from agents_api.queries.files.get_file import get_file
from agents_api.queries.files.list_files import list_files
from fastapi import HTTPException


async def test_query_create_file(pg_dsn, test_developer):
    pool = await create_db_pool(dsn=pg_dsn)
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="Hello",
            description="World",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        connection_pool=pool,
    )
    assert isinstance(file, File)
    assert file.id is not None
    assert file.name == "Hello"
    assert file.description == "World"
    assert file.mime_type == "text/plain"


async def test_query_create_file_with_project(pg_dsn, test_developer, test_project):
    pool = await create_db_pool(dsn=pg_dsn)
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="Hello with Project",
            description="World",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=test_project.canonical_name,
        ),
        connection_pool=pool,
    )
    assert isinstance(file, File)
    assert file.id is not None
    assert file.name == "Hello with Project"
    assert file.project == test_project.canonical_name


async def test_query_create_file_with_invalid_project(pg_dsn, test_developer):
    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc:
        await create_file(
            developer_id=test_developer.id,
            data=CreateFileRequest(
                name="Hello with Invalid Project",
                description="World",
                mime_type="text/plain",
                content="eyJzYW1wbGUiOiAidGVzdCJ9",
                project="invalid_project",
            ),
            connection_pool=pool,
        )

    assert exc.value.status_code == 404
    assert "Project 'invalid_project' not found" in exc.value.detail


async def test_query_create_user_file(pg_dsn, test_developer, test_user):
    pool = await create_db_pool(dsn=pg_dsn)
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="User File",
            description="Test user file",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )
    assert isinstance(file, File)
    assert file.id is not None
    assert file.name == "User File"

    # Verify file appears in user's files
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )
    assert any(f.id == file.id for f in files)


async def test_query_create_user_file_with_project(
    pg_dsn, test_developer, test_user, test_project
):
    pool = await create_db_pool(dsn=pg_dsn)
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="User File with Project",
            description="Test user file",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=test_project.canonical_name,
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )
    assert isinstance(file, File)
    assert file.id is not None
    assert file.name == "User File with Project"
    assert file.project == test_project.canonical_name

    # Verify file appears in user's files with the right project
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        project=test_project.canonical_name,
        connection_pool=pool,
    )
    assert any(f.id == file.id for f in files)
    assert all(f.project == test_project.canonical_name for f in files)


async def test_query_create_agent_file(pg_dsn, test_developer, test_agent):
    pool = await create_db_pool(dsn=pg_dsn)

    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="Agent File",
            description="Test agent file",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )
    assert file.name == "Agent File"

    # Verify file appears in agent's files
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )
    assert any(f.id == file.id for f in files)


async def test_query_create_agent_file_with_project(
    pg_dsn, test_developer, test_agent, test_project
):
    pool = await create_db_pool(dsn=pg_dsn)

    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="Agent File with Project",
            description="Test agent file",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=test_project.canonical_name,
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )
    assert file.name == "Agent File with Project"
    assert file.project == test_project.canonical_name

    # Verify file appears in agent's files with the right project
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        project=test_project.canonical_name,
        connection_pool=pool,
    )
    assert any(f.id == file.id for f in files)
    assert all(f.project == test_project.canonical_name for f in files)


async def test_query_get_file(pg_dsn, test_file, test_developer):
    pool = await create_db_pool(dsn=pg_dsn)
    file_test = await get_file(
        developer_id=test_developer.id,
        file_id=test_file.id,
        connection_pool=pool,
    )
    assert file_test.id == test_file.id
    assert file_test.name == "Hello"
    assert file_test.description == "World"
    assert file_test.mime_type == "text/plain"
    assert file_test.hash == test_file.hash


async def test_query_list_files(pg_dsn, test_developer, test_file):
    pool = await create_db_pool(dsn=pg_dsn)
    files = await list_files(
        developer_id=test_developer.id,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == test_file.id for f in files)


async def test_query_list_files_with_project_filter(
    pg_dsn, test_developer, test_project
):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a file with the project
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="Project File for Filtering",
            description="Test project file filtering",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=test_project.canonical_name,
        ),
        connection_pool=pool,
    )

    # List files with project filter
    files = await list_files(
        developer_id=test_developer.id,
        project=test_project.canonical_name,
        connection_pool=pool,
    )

    assert len(files) >= 1
    assert any(f.id == file.id for f in files)
    assert all(f.project == test_project.canonical_name for f in files)


async def test_query_list_files_invalid_limit(pg_dsn, test_developer, test_file):
    """Test that listing files with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_files(
            developer_id=test_developer.id,
            connection_pool=pool,
            limit=101,
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"

    with pytest.raises(HTTPException) as exc:
        await list_files(
            developer_id=test_developer.id,
            connection_pool=pool,
            limit=0,
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"


async def test_query_list_files_invalid_offset(pg_dsn, test_developer, test_file):
    """Test that listing files with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_files(
            developer_id=test_developer.id,
            connection_pool=pool,
            offset=-1,
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Offset must be >= 0"


async def test_query_list_files_invalid_sort_by(pg_dsn, test_developer, test_file):
    """Test that listing files with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_files(
            developer_id=test_developer.id,
            connection_pool=pool,
            sort_by="invalid",
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort field"


async def test_query_list_files_invalid_sort_direction(
    pg_dsn, test_developer, test_file
):
    """Test that listing files with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_files(
            developer_id=test_developer.id,
            connection_pool=pool,
            direction="invalid",
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort direction"


async def test_query_list_user_files(pg_dsn, test_developer, test_user):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a file owned by the user
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="User List Test",
            description="Test file for user listing",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    # List user's files
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)


async def test_query_list_user_files_with_project(
    pg_dsn, test_developer, test_user, test_project
):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a file owned by the user with a project
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="User Project List Test",
            description="Test file for user project listing",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=test_project.canonical_name,
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    # List user's files with project filter
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        project=test_project.canonical_name,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)
    assert all(f.project == test_project.canonical_name for f in files)


async def test_query_list_agent_files(pg_dsn, test_developer, test_agent):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a file owned by the agent
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="Agent List Test",
            description="Test file for agent listing",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # List agent's files
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)


async def test_query_list_agent_files_with_project(
    pg_dsn, test_developer, test_agent, test_project
):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a file owned by the agent with a project
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="Agent Project List Test",
            description="Test file for agent project listing",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=test_project.canonical_name,
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # List agent's files with project filter
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        project=test_project.canonical_name,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)
    assert all(f.project == test_project.canonical_name for f in files)


async def test_query_delete_user_file(pg_dsn, test_developer, test_user):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a file owned by the user
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="User Delete Test",
            description="Test file for user deletion",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    # Delete the file
    await delete_file(
        developer_id=test_developer.id,
        file_id=file.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    # Verify file is no longer in user's files
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )
    assert not any(f.id == file.id for f in files)


async def test_query_delete_agent_file(pg_dsn, test_developer, test_agent):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a file owned by the agent
    file = await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="Agent Delete Test",
            description="Test file for agent deletion",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # Delete the file
    await delete_file(
        developer_id=test_developer.id,
        file_id=file.id,
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # Verify file is no longer in agent's files
    files = await list_files(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )
    assert not any(f.id == file.id for f in files)


async def test_query_delete_file(pg_dsn, test_developer, test_file):
    pool = await create_db_pool(dsn=pg_dsn)

    await delete_file(
        developer_id=test_developer.id,
        file_id=test_file.id,
        connection_pool=pool,
    )
