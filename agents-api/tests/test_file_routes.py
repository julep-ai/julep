# Tests for file routes

import base64
import hashlib

from ward import test

from tests.fixtures import make_request, s3_client, test_project


@test("route: create file")
async def _(make_request=make_request, s3_client=s3_client):
    data = {
        "name": "Test File",
        "description": "This is a test file.",
        "mime_type": "text/plain",
        "content": "eyJzYW1wbGUiOiAidGVzdCJ9",
    }

    response = make_request(
        method="POST",
        url="/files",
        json=data,
    )

    assert response.status_code == 201


@test("route: create file with project")
async def _(make_request=make_request, s3_client=s3_client, project=test_project):
    data = {
        "name": "Test File with Project",
        "description": "This is a test file with project.",
        "mime_type": "text/plain",
        "content": "eyJzYW1wbGUiOiAidGVzdCJ9",
        "project": project.canonical_name,
    }

    response = make_request(
        method="POST",
        url="/files",
        json=data,
    )

    assert response.status_code == 201
    assert response.json()["project"] == project.canonical_name


@test("route: delete file")
async def _(make_request=make_request, s3_client=s3_client):
    data = {
        "name": "Test File",
        "description": "This is a test file.",
        "mime_type": "text/plain",
        "content": "eyJzYW1wbGUiOiAidGVzdCJ9",
    }

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
    data = {
        "name": "Test File",
        "description": "This is a test file.",
        "mime_type": "text/plain",
        "content": "eyJzYW1wbGUiOiAidGVzdCJ9",
    }

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


@test("route: list files")
async def _(make_request=make_request, s3_client=s3_client):
    response = make_request(
        method="GET",
        url="/files",
    )

    assert response.status_code == 200


@test("route: list files with project filter")
async def _(make_request=make_request, s3_client=s3_client, project=test_project):
    # First create a file with the project
    data = {
        "name": "Test File for Project Filter",
        "description": "This is a test file for project filtering.",
        "mime_type": "text/plain",
        "content": "eyJzYW1wbGUiOiAidGVzdCJ9",
        "project": project.canonical_name,
    }

    make_request(
        method="POST",
        url="/files",
        json=data,
    )

    # Then list files with project filter
    response = make_request(
        method="GET",
        url="/files",
        params={
            "project": project.canonical_name,
        },
    )

    assert response.status_code == 200
    result = response.json()

    assert isinstance(result["items"], list)
    assert len(result["items"]) > 0
    assert all(file["project"] == project.canonical_name for file in result["items"])
