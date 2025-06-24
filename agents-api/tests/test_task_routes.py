import json
from unittest.mock import patch
from uuid import UUID

import pytest
from agents_api.autogen.openapi_model import (
    CreateTransitionRequest,
    ExecutionStatusEvent,
    Transition,
)
from agents_api.clients.pg import create_db_pool
from agents_api.env import api_key, api_key_header_name, multi_tenant_mode
from agents_api.queries.executions.create_execution_transition import (
    create_execution_transition,
)
from fastapi.testclient import TestClient
from uuid_extensions import uuid7

from .utils import patch_testing_temporal


def test_route_unauthorized_should_fail(client, test_agent):
    """route: unauthorized should fail"""
    data = {
        "name": "test user",
        "main": [{"kind_": "evaluate", "evaluate": {"additionalProp1": "value1"}}],
    }
    response = client.request(method="POST", url=f"/agents/{test_agent.id!s}/tasks", json=data)
    assert response.status_code == 403


def test_route_create_task(make_request, test_agent):
    """route: create task"""
    data = {
        "name": "test user",
        "main": [{"kind_": "evaluate", "evaluate": {"additionalProp1": "value1"}}],
    }
    response = make_request(method="POST", url=f"/agents/{test_agent.id!s}/tasks", json=data)
    assert response.status_code == 201


async def test_route_create_task_execution(make_request, test_task):
    data = {"input": {}, "metadata": {}}
    async with patch_testing_temporal():
        response = make_request(
            method="POST", url=f"/tasks/{test_task.id!s}/executions", json=data
        )
    assert response.status_code == 201


def test_route_get_execution_not_exists(make_request):
    """route: get execution not exists"""
    execution_id = str(uuid7())
    response = make_request(method="GET", url=f"/executions/{execution_id}")
    assert response.status_code == 404


def test_route_get_execution_exists(make_request, test_execution):
    """route: get execution exists"""
    response = make_request(method="GET", url=f"/executions/{test_execution.id!s}")
    assert response.status_code == 200


def test_route_get_task_not_exists(make_request):
    """route: get task not exists"""
    task_id = str(uuid7())
    response = make_request(method="GET", url=f"/tasks/{task_id}")
    assert response.status_code == 404


def test_route_get_task_exists(make_request, test_task):
    """route: get task exists"""
    response = make_request(method="GET", url=f"/tasks/{test_task.id!s}")
    assert response.status_code == 200


async def test_route_list_all_execution_transition(make_request, test_execution_started):
    response = make_request(
        method="GET", url=f"/executions/{test_execution_started.id!s}/transitions"
    )
    assert response.status_code == 200
    response = response.json()
    transitions = response["items"]
    assert isinstance(transitions, list)
    assert len(transitions) > 0


async def test_route_list_a_single_execution_transition(
    pg_dsn, make_request, test_execution_started, test_developer_id
):
    pool = await create_db_pool(dsn=pg_dsn)
    scope_id = uuid7()
    transition = await create_execution_transition(
        developer_id=test_developer_id,
        execution_id=test_execution_started.id,
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
        url=f"/executions/{test_execution_started.id!s}/transitions/{transition.id!s}",
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


def test_route_list_task_executions(make_request, test_execution):
    """route: list task executions"""
    response = make_request(method="GET", url=f"/tasks/{test_execution.task_id!s}/executions")
    assert response.status_code == 200
    response = response.json()
    executions = response["items"]
    assert isinstance(executions, list)
    assert len(executions) > 0


def test_route_list_tasks(make_request, test_agent):
    """route: list tasks"""
    response = make_request(method="GET", url=f"/agents/{test_agent.id!s}/tasks")
    data = {
        "name": "test user",
        "main": [{"kind_": "evaluate", "evaluate": {"additionalProp1": "value1"}}],
    }
    response = make_request(method="POST", url=f"/agents/{test_agent.id!s}/tasks", json=data)
    assert response.status_code == 201
    response = make_request(method="GET", url=f"/agents/{test_agent.id!s}/tasks")
    assert response.status_code == 200
    response = response.json()
    tasks = response["items"]
    assert isinstance(tasks, list)
    assert len(tasks) > 0


@pytest.mark.skip(reason="Temporal connection issue")
async def test_route_update_execution(make_request, test_task):
    data = {"input": {}, "metadata": {}}
    async with patch_testing_temporal():
        response = make_request(
            method="POST", url=f"/tasks/{test_task.id!s}/executions", json=data
        )
        execution = response.json()
        data = {"status": "running"}
        execution_id = execution["id"]
        response = make_request(method="PUT", url=f"/executions/{execution_id}", json=data)
        assert response.status_code == 200
        execution_id = response.json()["id"]
        response = make_request(method="GET", url=f"/executions/{execution_id}")
        assert response.status_code == 200
        execution = response.json()
        assert execution["status"] == "running"


def test_route_stream_execution_status_sse_endpoint(
    client: TestClient, test_execution_started, test_developer_id
):
    """route: stream execution status SSE endpoint"""
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

    async def mock_sse_publisher(send_chan, *args, **kwargs):
        """Mock publisher that sends all events at once and then exits"""
        async with send_chan:
            for response in mock_sse_responses:
                await send_chan.send({"data": response.model_dump_json()})

    execution = test_execution_started
    url = f"/executions/{execution.id}/status.stream"
    headers = {api_key_header_name: api_key}
    if multi_tenant_mode:
        headers["X-Developer-Id"] = str(test_developer_id)
    with (
        patch(
            "agents_api.routers.tasks.stream_execution_status.execution_status_publisher",
            mock_sse_publisher,
        ),
        client.stream("GET", url, headers=headers) as response,
    ):
        content_type = response.headers.get("content-type", "")
        assert content_type.startswith("text/event-stream"), (
            f"Unexpected content type: {content_type}"
        )
        assert response.status_code == 200
        received_events = []
        max_attempts = 10
        for i, line in enumerate(response.iter_lines()):
            if line:
                event_line = line.decode() if isinstance(line, bytes | bytearray) else line
                if event_line.startswith("data:"):
                    payload = event_line[len("data:") :].strip()
                    data = json.loads(payload)
                    received_events.append(data)
            if len(received_events) >= len(mock_sse_responses) or i >= max_attempts:
                break
        response.close()
    assert len(received_events) == len(mock_sse_responses), (
        f"Expected {len(mock_sse_responses)} events, got {len(received_events)}"
    )
    assert received_events[0]["status"] == "starting"
    assert received_events[1]["status"] == "running"
    assert received_events[2]["status"] == "succeeded"
    for i, event in enumerate(received_events):
        assert event["execution_id"] == "068306ff-e0f3-7fe9-8000-0013626a759a"
        assert isinstance(event["updated_at"], str)
        assert event["transition_count"] == i + 1


def test_route_stream_execution_status_sse_endpoint_non_existing_execution(
    client: TestClient, test_developer_id
):
    """route: stream execution status SSE endpoint - non-existing execution"""
    non_existing_execution_id = uuid7()
    url = f"/executions/{non_existing_execution_id}/status.stream"
    headers = {api_key_header_name: api_key}
    if multi_tenant_mode:
        headers["X-Developer-Id"] = str(test_developer_id)
    response = client.get(url, headers=headers)
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert "message" in error_data["error"]
    assert "code" in error_data["error"]
    assert "type" in error_data["error"]
    assert f"Execution {non_existing_execution_id} not found" in error_data["error"]["message"]
    assert error_data["error"]["code"] == "http_404"
    assert error_data["error"]["type"] == "http_error"
