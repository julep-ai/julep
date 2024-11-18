import base64
import hashlib

from ward import skip, test

from tests.fixtures import make_request, test_file


@test("route: create file")
async def _(make_request=make_request):
    data = dict(
        name="Test File",
        description="This is a test file.",
        mime_type="text/plain",
        content="eyJzYW1wbGUiOiAidGVzdCJ9",
    )

    response = make_request(
        method="POST",
        url="/files",
        json=data,
    )

    assert response.status_code == 201


@test("route: delete file")
async def _(make_request=make_request):
    data = dict(
        name="Test File",
        description="This is a test file.",
        mime_type="text/plain",
        content="eyJzYW1wbGUiOiAidGVzdCJ9",
    )

    response = make_request(
        method="POST",
        url="/files",
        json=data,
    )

    file_id = response.json()["id"]

    response = make_request(
        method="DELETE",
        url=f"/files/{file_id}",
    )

    assert response.status_code == 202

    response = make_request(
        method="GET",
        url=f"/files/{file_id}",
    )

    assert response.status_code == 404


@test("route: get file")
async def _(make_request=make_request, file=test_file):
    response = make_request(
        method="GET",
        url=f"/files/{file.id}",
    )

    assert response.status_code == 200

    result = response.json()

    assert result["hash"] == file.hash

    # Decode base64 content and compute its SHA-256 hash
    content_bytes = base64.b64decode(file.content)
    expected_hash = hashlib.sha256(content_bytes).hexdigest()

    assert result["hash"] == expected_hash
