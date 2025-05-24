# Tests for task routes

import json
from unittest.mock import patch
from uuid import UUID

from agents_api.autogen.openapi_model import (
    ExecutionStatusEvent,
    Transition,
)
from agents_api.env import api_key, api_key_header_name, multi_tenant_mode
from agents_api.queries.executions.create_execution_transition import (
    create_execution_transition,
)
from fastapi.testclient import TestClient
from uuid_extensions import uuid7
from ward import skip, test

from .fixtures import (
    CreateTransitionRequest,
    client,
    create_db_pool,
    make_request,
    pg_dsn,
    test_agent,
    test_developer_id,
    test_execution,
    test_execution_started,
    test_task,
)
from .utils import patch_testing_temporal


@test("route: unauthorized should fail")
def _(client=client, agent=test_agent):
    data = {
        "name": "test user",
        "main": [
            {
                "kind_": "evaluate",
                "evaluate": {
                    "additionalProp1": "value1",
                },
            },
        ],
    }

    response = client.request(
        method="POST",
        url=f"/agents/{agent.id!s}/tasks",
        json=data,
    )

    assert response.status_code == 403


@test("route: create task")
def _(make_request=make_request, agent=test_agent):
    data = {
        "name": "test user",
        "main": [
            {
                "kind_": "evaluate",
                "evaluate": {
                    "additionalProp1": "value1",
                },
            },
        ],
    }

    response = make_request(
        method="POST",
        url=f"/agents/{agent.id!s}/tasks",
        json=data,
    )

    assert response.status_code == 201


@test("route: create task execution")
async def _(make_request=make_request, task=test_task):
    data = {
        "input": {},
        "metadata": {},
    }

    async with patch_testing_temporal():
        response = make_request(
            method="POST",
            url=f"/tasks/{task.id!s}/executions",
            json=data,
        )

    assert response.status_code == 201


@test("route: get execution not exists")
def _(make_request=make_request):
    execution_id = str(uuid7())

    response = make_request(
        method="GET",
        url=f"/executions/{execution_id}",
    )

    assert response.status_code == 404


@test("route: get execution exists")
def _(make_request=make_request, execution=test_execution):
    response = make_request(
        method="GET",
        url=f"/executions/{execution.id!s}",
    )

    assert response.status_code == 200


@test("route: get task not exists")
def _(make_request=make_request):
    task_id = str(uuid7())

    response = make_request(
        method="GET",
        url=f"/tasks/{task_id}",
    )

    assert response.status_code == 404


@test("route: get task exists")
def _(make_request=make_request, task=test_task):
    response = make_request(
        method="GET",
        url=f"/tasks/{task.id!s}",
    )

    assert response.status_code == 200


@test("route: list all execution transition")
async def _(make_request=make_request, execution=test_execution_started):
    response = make_request(
        method="GET",
        url=f"/executions/{execution.id!s}/transitions",
    )

    assert response.status_code == 200
    response = response.json()
    transitions = response["items"]

    assert isinstance(transitions, list)
    assert len(transitions) > 0


@test("route: list a single execution transition")
async def _(
    dsn=pg_dsn,
    make_request=make_request,
    execution=test_execution_started,
    developer_id=test_developer_id,
):
    pool = await create_db_pool(dsn=dsn)

    scope_id = uuid7()
    # Create a transition
    transition = await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="step",
            output={},
            current={"workflow": "main", "step": 0, "scope_id": scope_id},
            next={"workflow": "wf1", "step": 1, "scope_id": scope_id},
        ),
        connection_pool=pool,
    )

    response = make_request(
        method="GET",
        url=f"/executions/{execution.id!s}/transitions/{transition.id!s}",
    )

    assert response.status_code == 200
    response = response.json()

    assert isinstance(transition, Transition)
    assert str(transition.id) == response["id"]
    assert transition.type == response["type"]
    assert transition.output == response["output"]
    assert transition.current.workflow == response["current"]["workflow"]
    assert transition.current.step == response["current"]["step"]
    assert transition.next.workflow == response["next"]["workflow"]
    assert transition.next.step == response["next"]["step"]


@test("route: list task executions")
def _(make_request=make_request, execution=test_execution):
    response = make_request(
        method="GET",
        url=f"/tasks/{execution.task_id!s}/executions",
    )

    assert response.status_code == 200
    response = response.json()
    executions = response["items"]

    assert isinstance(executions, list)
    assert len(executions) > 0


@test("route: list tasks")
def _(make_request=make_request, agent=test_agent):
    response = make_request(
        method="GET",
        url=f"/agents/{agent.id!s}/tasks",
    )

    data = {
        "name": "test user",
        "main": [
            {
                "kind_": "evaluate",
                "evaluate": {
                    "additionalProp1": "value1",
                },
            },
        ],
    }

    response = make_request(
        method="POST",
        url=f"/agents/{agent.id!s}/tasks",
        json=data,
    )

    assert response.status_code == 201

    response = make_request(
        method="GET",
        url=f"/agents/{agent.id!s}/tasks",
    )

    assert response.status_code == 200
    response = response.json()
    tasks = response["items"]

    assert isinstance(tasks, list)
    assert len(tasks) > 0


# It's failing while getting the temporal client in
# the `update_execution.py` route, but it's correctly
# getting it in the `create_task_execution.py` route
@skip("Temporal connection issue")
@test("route: update execution")
async def _(make_request=make_request, task=test_task):
    data = {
        "input": {},
        "metadata": {},
    }

    async with patch_testing_temporal():
        response = make_request(
            method="POST",
            url=f"/tasks/{task.id!s}/executions",
            json=data,
        )

        execution = response.json()

        data = {
            "status": "running",
        }

        execution_id = execution["id"]

        response = make_request(
            method="PUT",
            url=f"/executions/{execution_id}",
            json=data,
        )

        assert response.status_code == 200

        execution_id = response.json()["id"]

        response = make_request(
            method="GET",
            url=f"/executions/{execution_id}",
        )

        assert response.status_code == 200
        execution = response.json()

        assert execution["status"] == "running"


@test("route: stream execution status SSE endpoint")
def _(
    client: TestClient = client,
    test_execution_started=test_execution_started,
    test_developer_id=test_developer_id,
):
    # Mock SSE response data that simulates a progressing execution
    mock_sse_responses = [
        ExecutionStatusEvent(
            execution_id=UUID("068306ff-e0f3-7fe9-8000-0013626a759a"),
            status="starting",
            updated_at="2025-05-23T12:54:24.565424Z",
            error=None,
            transition_count=1,
            metadata={},
        ),
        ExecutionStatusEvent(
            execution_id=UUID("068306ff-e0f3-7fe9-8000-0013626a759a"),
            status="running",
            updated_at="2025-05-23T12:54:30.903484Z",
            error=None,
            transition_count=2,
            metadata={},
        ),
        ExecutionStatusEvent(
            execution_id=UUID("068306ff-e0f3-7fe9-8000-0013626a759a"),
            status="succeeded",
            updated_at="2025-05-23T12:56:12.054067Z",
            error=None,
            transition_count=3,
            metadata={},
        ),
    ]

    # Simple mock SSE server that immediately returns all events
    async def mock_sse_publisher(send_chan, *args, **kwargs):
        """Mock publisher that sends all events at once and then exits"""
        async with send_chan:
            for response in mock_sse_responses:
                await send_chan.send({"data": response.model_dump_json()})

    execution = test_execution_started
    url = f"/executions/{execution.id}/status.stream"

    # Prepare authentication headers
    headers = {api_key_header_name: api_key}
    if multi_tenant_mode:
        headers["X-Developer-Id"] = str(test_developer_id)

    # Replace the execution_status_publisher with our simplified mock version
    with patch(
        "agents_api.routers.tasks.stream_execution_status.execution_status_publisher",
        mock_sse_publisher,
    ):
        # Make the request to the SSE endpoint using TestClient.stream
        with client.stream("GET", url, headers=headers) as response:
            # Verify response headers and status code
            content_type = response.headers.get("content-type", "")
            assert content_type.startswith("text/event-stream"), (
                f"Unexpected content type: {content_type}"
            )
            assert response.status_code == 200

            # Read and parse events from the stream
            received_events = []
            max_attempts = 10  # Limit the number of attempts to avoid infinite loops
            attempts = 0

            # Read the stream with a limit on attempts
            for line in response.iter_lines():
                if line:
                    event_line = line.decode() if isinstance(line, bytes | bytearray) else line
                    if event_line.startswith("data:"):
                        # Parse JSON payload
                        payload = event_line[len("data:") :].strip()
                        data = json.loads(payload)
                        received_events.append(data)

                # Check if we've received all events or reached max attempts
                attempts += 1
                if len(received_events) >= len(mock_sse_responses) or attempts >= max_attempts:
                    break

            # Ensure we close the connection
            response.close()

    # Verify we received the expected events
    assert len(received_events) == len(mock_sse_responses), (
        f"Expected {len(mock_sse_responses)} events, got {len(received_events)}"
    )

    # Verify the status progression
    assert received_events[0]["status"] == "starting"
    assert received_events[1]["status"] == "running"
    assert received_events[2]["status"] == "succeeded"

    # Verify other fields
    for i, event in enumerate(received_events):
        assert event["execution_id"] == "068306ff-e0f3-7fe9-8000-0013626a759a"
        assert isinstance(event["updated_at"], str)
        assert event["transition_count"] == i + 1


@test("route: stream execution status SSE endpoint - non-existing execution")
def _(client: TestClient = client, test_developer_id=test_developer_id):
    # Create a random UUID for a non-existing execution
    non_existing_execution_id = uuid7()
    url = f"/executions/{non_existing_execution_id}/status.stream"

    # Prepare authentication headers
    headers = {api_key_header_name: api_key}
    if multi_tenant_mode:
        headers["X-Developer-Id"] = str(test_developer_id)

    # Make the request to the SSE endpoint - should return a 404 error
    response = client.get(url, headers=headers)

    # Verify response status code is 404
    assert response.status_code == 404

    # Parse the error response
    error_data = response.json()

    # Verify error structure
    assert "error" in error_data
    assert "message" in error_data["error"]
    assert "code" in error_data["error"]
    assert "type" in error_data["error"]

    # Verify specific error details
    assert f"Execution {non_existing_execution_id} not found" in error_data["error"]["message"]
    assert error_data["error"]["code"] == "http_404"
    assert error_data["error"]["type"] == "http_error"
