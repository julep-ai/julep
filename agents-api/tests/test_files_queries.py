# # Tests for entry queries


from uuid_extensions import uuid7
from ward import raises, test
from fastapi import HTTPException
from agents_api.autogen.openapi_model import CreateFileRequest
from agents_api.queries.files.create_file import create_file
from agents_api.queries.files.delete_file import delete_file
from agents_api.queries.files.get_file import get_file
from tests.fixtures import pg_dsn, test_agent, test_developer_id
from agents_api.clients.pg import create_db_pool


@test("query: create file")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    pool = await create_db_pool(dsn=dsn)
    await create_file(
        developer_id=developer_id,
        data=CreateFileRequest(
            name="Hello",
            description="World",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        connection_pool=pool,
    )


# @test("query: get file")
# async def _(dsn=pg_dsn, developer_id=test_developer_id):
#     pool = await create_db_pool(dsn=dsn)
#     file = create_file(
#         developer_id=developer_id,
#         data=CreateFileRequest(
#             name="Hello",
#             description="World",
#             mime_type="text/plain",
#             content="eyJzYW1wbGUiOiAidGVzdCJ9",
#         ),
#         connection_pool=pool,
#     )

#     get_file_result = get_file(
#         developer_id=developer_id,
#         file_id=file.id,
#         connection_pool=pool,
#     )

#     assert file == get_file_result

# @test("query: delete file")
# async def _(dsn=pg_dsn, developer_id=test_developer_id):
#     pool = await create_db_pool(dsn=dsn)
#     file = create_file(
#         developer_id=developer_id,
#         data=CreateFileRequest(
#             name="Hello",
#             description="World",
#             mime_type="text/plain",
#             content="eyJzYW1wbGUiOiAidGVzdCJ9",
#         ),
#         connection_pool=pool,
#     )

#     delete_file(
#         developer_id=developer_id,
#         file_id=file.id,
#         connection_pool=pool,
#     )

#     with raises(HTTPException) as e:
#         get_file(
#             developer_id=developer_id,
#             file_id=file.id,
#             connection_pool=pool,
#         )

#     assert e.value.status_code == 404
#     assert e.value.detail == "The specified file does not exist"