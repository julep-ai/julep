"""
Tests for middleware components.
"""

from uuid import uuid4

from agents_api.app import app
from agents_api.clients.pg import create_db_pool
from agents_api.queries.developers.create_developer import create_developer
from fastapi.testclient import TestClient
from ward import test

from tests.fixtures import pg_dsn


@test("middleware: access denied for inactive developer")
async def _(dsn=pg_dsn):
    developer_id = uuid4()
    # Add a test endpoint that requires authentication

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    # Create a test client
    client = TestClient(app)

    # Create an inactive developer
    pool = await create_db_pool(dsn=dsn)
    await create_developer(
        email="inactive@test.com",
        active=False,
        developer_id=developer_id,
        connection_pool=pool,
    )

    # Make a request with the inactive developer's ID
    response = client.get(
        "/test",
        headers={"X-Developer-Id": str(developer_id)},
    )

    # Verify we get a 403 response
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Invalid developer account"
