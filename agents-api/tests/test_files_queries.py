# Tests for entry queries


from ward import test

from agents_api.autogen.openapi_model import CreateFileRequest
from agents_api.models.files.create_file import create_file
from agents_api.models.files.delete_file import delete_file
from agents_api.models.files.get_file import get_file
from tests.fixtures import (
    cozo_client,
    test_developer_id,
    test_file,
)


@test("model: create file")
def _(client=cozo_client, developer_id=test_developer_id):
    create_file(
        developer_id=developer_id,
        data=CreateFileRequest(
            name="Hello",
            description="World",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        client=client,
    )


@test("model: get file")
def _(client=cozo_client, file=test_file, developer_id=test_developer_id):
    get_file(
        developer_id=developer_id,
        file_id=file.id,
        client=client,
    )


@test("model: delete file")
def _(client=cozo_client, developer_id=test_developer_id):
    file = create_file(
        developer_id=developer_id,
        data=CreateFileRequest(
            name="Hello",
            description="World",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        client=client,
    )

    delete_file(
        developer_id=developer_id,
        file_id=file.id,
        client=client,
    )
