# Tests for task routes

from agents_api.autogen.openapi_model import (
    Transition,
)
from agents_api.queries.executions.create_execution_transition import (
    create_execution_transition,
)
from uuid_extensions import uuid7
import pytest

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


def test_route_unauthorized_should_fail(client=client, agent=test_agent):
    """route: unauthorized should fail"""
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


def test_route_create_task(make_request=make_request, agent=test_agent):
    """route: create task"""
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


@pytest.mark.asyncio
async def test_route_create_task_execution(make_request=make_request, task=test_task):
    """route: create task execution"""
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


def test_route_get_execution_not_exists(make_request=make_request):
    """route: get execution not exists"""
    execution_id = str(uuid7())

    response = make_request(
        method="GET",
        url=f"/executions/{execution_id}",
    )

    assert response.status_code == 404


def test_route_get_execution_exists(make_request=make_request, execution=test_execution):
    """route: get execution exists"""
    response = make_request(
        method="GET",
        url=f"/executions/{execution.id!s}",
    )

    assert response.status_code == 200


def test_route_get_task_not_exists(make_request=make_request):
    """route: get task not exists"""
    task_id = str(uuid7())

    response = make_request(
        method="GET",
        url=f"/tasks/{task_id}",
    )

    assert response.status_code == 404


def test_route_get_task_exists(make_request=make_request, task=test_task):
    """route: get task exists"""
    response = make_request(
        method="GET",
        url=f"/tasks/{task.id!s}",
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_route_list_all_execution_transition(make_request=make_request, execution=test_execution_started):
    """route: list all execution transition"""
    response = make_request(
        method="GET",
        url=f"/executions/{execution.id!s}/transitions",
    )

    assert response.status_code == 200
    response = response.json()
    transitions = response["items"]

    assert isinstance(transitions, list)
    assert len(transitions) > 0


@pytest.mark.asyncio
async def test_route_list_a_single_execution_transition(
    """route: list a single execution transition"""
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


def test_route_list_task_executions(make_request=make_request, execution=test_execution):
    """route: list task executions"""
    response = make_request(
        method="GET",
        url=f"/tasks/{execution.task_id!s}/executions",
    )

    assert response.status_code == 200
    response = response.json()
    executions = response["items"]

    assert isinstance(executions, list)
    assert len(executions) > 0


def test_route_list_tasks(make_request=make_request, agent=test_agent):
    """route: list tasks"""
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
@pytest.mark.skip(reason="Temporal connection issue")
@pytest.mark.asyncio
async def test_route_update_execution(make_request=make_request, task=test_task):
    """route: update execution"""
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
