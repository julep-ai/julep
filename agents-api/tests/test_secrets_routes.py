"""Tests for secrets routes."""

from uuid import uuid4

import pytest

from tests.fixtures import client, make_request, test_developer_id


def test_route_unauthorized_secrets_route_should_fail(client=client):
    """route: unauthorized secrets route should fail"""
    data = {
        "name": f"test_secret_{uuid4().hex[:8]}",
        "description": "Test secret for listing",
        "value": "sk_list_test_123456789",
    }
    # Try to access secrets without auth
    response = client.request(
        method="GET",
        url="/secrets",
        json=data,
    )

    assert response.status_code == 403


def test_route_create_secret(make_request=make_request, developer_id=test_developer_id):
    """route: create secret"""
    data = {
        "developer_id": str(developer_id),
        "name": f"test_secret_{uuid4().hex[:8]}",
        "description": "Test secret for API integration",
        "value": "sk_test_123456789",
        "metadata": {"service": "test-service", "environment": "test"},
    }

    response = make_request(
        method="POST",
        url="/secrets",
        json=data,
    )

    assert response.status_code == 201
    result = response.json()
    assert result["name"] == data["name"]
    assert result["description"] == data["description"]
    # Value should be encrypted in response
    assert result["value"] == "ENCRYPTED"
    assert result["metadata"] == data["metadata"]


def test_route_list_secrets(make_request=make_request, developer_id=test_developer_id):
    """route: list secrets"""
    # First create a secret to ensure we have something to list
    secret_name = f"list_test_secret_{uuid4().hex[:8]}"
    data = {
        "developer_id": str(developer_id),
        "name": secret_name,
        "description": "Test secret for listing",
        "value": "sk_list_test_123456789",
        "metadata": {"service": "test-service", "environment": "test"},
    }

    make_request(
        method="POST",
        url="/secrets",
        json=data,
    )

    # Now list secrets
    response = make_request(
        method="GET",
        url="/secrets",
    )

    assert response.status_code == 200
    secrets = response.json()

    assert isinstance(secrets, list)
    assert len(secrets) > 0
    # Find our test secret
    assert any(secret["name"] == secret_name for secret in secrets)
    assert all(secret["value"] == "ENCRYPTED" for secret in secrets)


def test_route_update_secret(make_request=make_request, developer_id=test_developer_id):
    """route: update secret"""
    # First create a secret
    original_name = f"update_test_secret_{uuid4().hex[:8]}"
    create_data = {
        "developer_id": str(developer_id),
        "name": original_name,
        "description": "Original description",
        "value": "sk_original_value",
        "metadata": {"original": True},
    }

    create_response = make_request(
        method="POST",
        url="/secrets",
        json=create_data,
    )

    secret_id = create_response.json()["id"]

    # Now update it
    updated_name = f"updated_secret_{uuid4().hex[:8]}"
    update_data = {
        "developer_id": str(developer_id),
        "name": updated_name,
        "description": "Updated description",
        "value": "sk_updated_value",
        "metadata": {"updated": True, "timestamp": "now"},
    }

    update_response = make_request(
        method="PUT",
        url=f"/secrets/{secret_id}",
        json=update_data,
    )

    assert update_response.status_code == 200
    updated_secret = update_response.json()

    assert updated_secret["name"] == updated_name
    assert updated_secret["description"] == "Updated description"
    assert updated_secret["value"] == "ENCRYPTED"
    assert updated_secret["metadata"] == update_data["metadata"]


def test_route_delete_secret(make_request=make_request, developer_id=test_developer_id):
    """route: delete secret"""
    # First create a secret
    delete_test_name = f"delete_test_secret_{uuid4().hex[:8]}"
    create_data = {
        "developer_id": str(developer_id),
        "name": delete_test_name,
        "description": "Secret to be deleted",
        "value": "sk_delete_me",
        "metadata": {"service": "test-service", "environment": "test"},
    }

    create_response = make_request(
        method="POST",
        url="/secrets",
        json=create_data,
    )

    secret_id = create_response.json()["id"]

    # Now delete it
    delete_response = make_request(
        method="DELETE",
        url=f"/secrets/{secret_id}",
    )

    assert delete_response.status_code == 202
    # Verify the secret is gone by listing all secrets
    list_response = make_request(
        method="GET",
        url="/secrets",
    )

    assert list_response.status_code == 200
    secrets = list_response.json()

    # Check that the deleted secret is not in the list
    deleted_secret_ids = [secret["id"] for secret in secrets]
    assert secret_id not in deleted_secret_ids


def test_route_create_duplicate_secret_name_fails(make_request=make_request, developer_id=test_developer_id):
    """route: create duplicate secret name fails"""
    # Create a secret with a specific name
    unique_name = f"unique_secret_{uuid4().hex[:8]}"
    data = {
        "developer_id": str(developer_id),
        "name": unique_name,
        "description": "First secret with this name",
        "value": "sk_first_value",
        "metadata": {"service": "test-service", "environment": "test"},
    }

    first_response = make_request(
        method="POST",
        url="/secrets",
        json=data,
    )

    assert first_response.status_code == 201

    # Try to create another with the same name
    duplicate_data = {
        "developer_id": str(developer_id),
        "name": unique_name,  # Same name
        "description": "Second secret with same name",
        "value": "sk_second_value",
        "metadata": {"service": "test-service", "environment": "test"},
    }

    second_response = make_request(
        method="POST",
        url="/secrets",
        json=duplicate_data,
    )

    # Should fail with a conflict error
    assert second_response.status_code == 409
