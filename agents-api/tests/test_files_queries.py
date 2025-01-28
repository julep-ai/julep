# Tests for entry queries

from agents_api.autogen.openapi_model import CreateFileRequest, File
from agents_api.clients.pg import create_db_pool
from agents_api.queries.files.create_file import create_file
from agents_api.queries.files.delete_file import delete_file
from agents_api.queries.files.get_file import get_file
from agents_api.queries.files.list_files import list_files
from ward import test

from tests.fixtures import pg_dsn, test_agent, test_developer, test_file, test_user


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
