# Tests for entry queries

from agents_api.autogen.openapi_model import CreateFileRequest, File
from agents_api.clients.pg import create_db_pool
from agents_api.queries.files.create_file import create_file
from agents_api.queries.files.delete_file import delete_file
from agents_api.queries.files.get_file import get_file
from agents_api.queries.files.list_files import list_files
from fastapi import HTTPException
from ward import raises, test

from tests.fixtures import pg_dsn, test_agent, test_developer, test_file, test_project, test_user


@test("query: create file")
async def _(dsn=pg_dsn, developer=test_developer):
    pool = await create_db_pool(dsn=dsn)
    file = await create_file(
        developer_id=developer.id,
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


@test("query: create file with project")
async def _(dsn=pg_dsn, developer=test_developer, project=test_project):
    pool = await create_db_pool(dsn=dsn)
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="Hello with Project",
            description="World",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )
    assert isinstance(file, File)
    assert file.id is not None
    assert file.name == "Hello with Project"
    assert file.project == project.canonical_name


@test("query: create file with invalid project")
async def _(dsn=pg_dsn, developer=test_developer):
    pool = await create_db_pool(dsn=dsn)
    
    with raises(HTTPException) as exc:
        await create_file(
            developer_id=developer.id,
            data=CreateFileRequest(
                name="Hello with Invalid Project",
                description="World",
                mime_type="text/plain",
                content="eyJzYW1wbGUiOiAidGVzdCJ9",
                project="invalid_project",
            ),
            connection_pool=pool,
        )
    
    assert exc.raised.status_code == 404
    assert "Project 'invalid_project' not found" in exc.raised.detail


@test("query: create user file")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    pool = await create_db_pool(dsn=dsn)
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="User File",
            description="Test user file",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )
    assert isinstance(file, File)
    assert file.id is not None
    assert file.name == "User File"

    # Verify file appears in user's files
    files = await list_files(
        developer_id=developer.id,
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )
    assert any(f.id == file.id for f in files)


@test("query: create user file with project")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user, project=test_project):
    pool = await create_db_pool(dsn=dsn)
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="User File with Project",
            description="Test user file",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=project.canonical_name,
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )
    assert isinstance(file, File)
    assert file.id is not None
    assert file.name == "User File with Project"
    assert file.project == project.canonical_name

    # Verify file appears in user's files with the right project
    files = await list_files(
        developer_id=developer.id,
        owner_type="user",
        owner_id=user.id,
        project=project.canonical_name,
        connection_pool=pool,
    )
    assert any(f.id == file.id for f in files)
    assert all(f.project == project.canonical_name for f in files)


@test("query: create agent file")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="Agent File",
            description="Test agent file",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert file.name == "Agent File"

    # Verify file appears in agent's files
    files = await list_files(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert any(f.id == file.id for f in files)


@test("query: create agent file with project")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent, project=test_project):
    pool = await create_db_pool(dsn=dsn)

    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="Agent File with Project",
            description="Test agent file",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=project.canonical_name,
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert file.name == "Agent File with Project"
    assert file.project == project.canonical_name

    # Verify file appears in agent's files with the right project
    files = await list_files(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        project=project.canonical_name,
        connection_pool=pool,
    )
    assert any(f.id == file.id for f in files)
    assert all(f.project == project.canonical_name for f in files)


@test("query: get file")
async def _(dsn=pg_dsn, file=test_file, developer=test_developer):
    pool = await create_db_pool(dsn=dsn)
    file_test = await get_file(
        developer_id=developer.id,
        file_id=file.id,
        connection_pool=pool,
    )
    assert file_test.id == file.id
    assert file_test.name == "Hello"
    assert file_test.description == "World"
    assert file_test.mime_type == "text/plain"
    assert file_test.hash == file.hash


@test("query: list files")
async def _(dsn=pg_dsn, developer=test_developer, file=test_file):
    pool = await create_db_pool(dsn=dsn)
    files = await list_files(
        developer_id=developer.id,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)


@test("query: list files with project filter")
async def _(dsn=pg_dsn, developer=test_developer, project=test_project):
    pool = await create_db_pool(dsn=dsn)
    
    # Create a file with the project
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="Project File for Filtering",
            description="Test project file filtering",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )
    
    # List files with project filter
    files = await list_files(
        developer_id=developer.id,
        project=project.canonical_name,
        connection_pool=pool,
    )
    
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)
    assert all(f.project == project.canonical_name for f in files)


@test("query: list files, invalid limit")
async def _(dsn=pg_dsn, developer=test_developer, file=test_file):
    """Test that listing files with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_files(
            developer_id=developer.id,
            connection_pool=pool,
            limit=101,
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"

    with raises(HTTPException) as exc:
        await list_files(
            developer_id=developer.id,
            connection_pool=pool,
            limit=0,
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"


@test("query: list files, invalid offset")
async def _(dsn=pg_dsn, developer=test_developer, file=test_file):
    """Test that listing files with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_files(
            developer_id=developer.id,
            connection_pool=pool,
            offset=-1,
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Offset must be >= 0"


@test("query: list files, invalid sort by")
async def _(dsn=pg_dsn, developer=test_developer, file=test_file):
    """Test that listing files with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_files(
            developer_id=developer.id,
            connection_pool=pool,
            sort_by="invalid",
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort field"


@test("query: list files, invalid sort direction")
async def _(dsn=pg_dsn, developer=test_developer, file=test_file):
    """Test that listing files with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_files(
            developer_id=developer.id,
            connection_pool=pool,
            direction="invalid",
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort direction"


@test("query: list user files")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    pool = await create_db_pool(dsn=dsn)

    # Create a file owned by the user
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="User List Test",
            description="Test file for user listing",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    # List user's files
    files = await list_files(
        developer_id=developer.id,
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)


@test("query: list user files with project")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user, project=test_project):
    pool = await create_db_pool(dsn=dsn)

    # Create a file owned by the user with a project
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="User Project List Test",
            description="Test file for user project listing",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=project.canonical_name,
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    # List user's files with project filter
    files = await list_files(
        developer_id=developer.id,
        owner_type="user",
        owner_id=user.id,
        project=project.canonical_name,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)
    assert all(f.project == project.canonical_name for f in files)


@test("query: list agent files")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    # Create a file owned by the agent
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="Agent List Test",
            description="Test file for agent listing",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )

    # List agent's files
    files = await list_files(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)


@test("query: list agent files with project")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent, project=test_project):
    pool = await create_db_pool(dsn=dsn)

    # Create a file owned by the agent with a project
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="Agent Project List Test",
            description="Test file for agent project listing",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
            project=project.canonical_name,
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )

    # List agent's files with project filter
    files = await list_files(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        project=project.canonical_name,
        connection_pool=pool,
    )
    assert len(files) >= 1
    assert any(f.id == file.id for f in files)
    assert all(f.project == project.canonical_name for f in files)


@test("query: delete user file")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    pool = await create_db_pool(dsn=dsn)

    # Create a file owned by the user
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="User Delete Test",
            description="Test file for user deletion",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    # Delete the file
    await delete_file(
        developer_id=developer.id,
        file_id=file.id,
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    # Verify file is no longer in user's files
    files = await list_files(
        developer_id=developer.id,
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )
    assert not any(f.id == file.id for f in files)


@test("query: delete agent file")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    # Create a file owned by the agent
    file = await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="Agent Delete Test",
            description="Test file for agent deletion",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )

    # Delete the file
    await delete_file(
        developer_id=developer.id,
        file_id=file.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )

    # Verify file is no longer in agent's files
    files = await list_files(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert not any(f.id == file.id for f in files)


@test("query: delete file")
async def _(dsn=pg_dsn, developer=test_developer, file=test_file):
    pool = await create_db_pool(dsn=dsn)

    await delete_file(
        developer_id=developer.id,
        file_id=file.id,
        connection_pool=pool,
    )
