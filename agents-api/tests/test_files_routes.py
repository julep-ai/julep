import base64
import hashlib

from ward import test

from tests.fixtures import make_request, s3_client


@test("route: create file")
async def _(make_request=make_request, s3_client=s3_client):
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
async def _(make_request=make_request, s3_client=s3_client):
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
async def _(make_request=make_request, s3_client=s3_client):
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
    content_bytes = base64.b64decode(data["content"])
    expected_hash = hashlib.sha256(content_bytes).hexdigest()

    response = make_request(
        method="GET",
        url=f"/files/{file_id}",
    )

    assert response.status_code == 200

    result = response.json()

    # Decode base64 content and compute its SHA-256 hash
    assert result["hash"] == expected_hash
