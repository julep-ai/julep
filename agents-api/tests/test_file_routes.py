import base64
import hashlib


async def test_route_create_file(make_request, s3_client):
    """route: create file"""
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


async def test_route_create_file_with_project(make_request, s3_client, test_project):
    """route: create file with project"""
    data = {
        "name": "Test File with Project",
        "description": "This is a test file with project.",
        "mime_type": "text/plain",
        "content": "eyJzYW1wbGUiOiAidGVzdCJ9",
        "project": test_project.canonical_name,
    }

    response = make_request(
        method="POST",
        url="/files",
        json=data,
    )

    assert response.status_code == 201
    assert response.json()["project"] == test_project.canonical_name


async def test_route_delete_file(make_request, s3_client):
    """route: delete file"""
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


async def test_route_get_file(make_request, s3_client):
    """route: get file"""
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


async def test_route_list_files(make_request, s3_client):
    """route: list files"""
    response = make_request(
        method="GET",
        url="/files",
    )

    assert response.status_code == 200


async def test_route_list_files_with_project_filter(
    make_request, s3_client, test_project
):
    """route: list files with project filter"""
    # First create a file with the project
    data = {
        "name": "Test File for Project Filter",
        "description": "This is a test file for project filtering.",
        "mime_type": "text/plain",
        "content": "eyJzYW1wbGUiOiAidGVzdCJ9",
        "project": test_project.canonical_name,
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
            "project": test_project.canonical_name,
        },
    )

    assert response.status_code == 200
    files = response.json()

    assert isinstance(files, list)
    assert len(files) > 0
    assert any(file["project"] == test_project.canonical_name for file in files)
