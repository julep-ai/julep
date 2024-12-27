# Tests for task routes

from uuid_extensions import uuid7
from ward import test

from .fixtures import (
    client,
    make_request,
    test_agent,
    test_execution,
    test_task,
    test_transition,
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
            }
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
            }
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


@test("route: list execution transitions")
def _(make_request=make_request, execution=test_execution, transition=test_transition):
    response = make_request(
        method="GET",
        url=f"/executions/{execution.id!s}/transitions",
    )

    assert response.status_code == 200
    response = response.json()
    transitions = response["items"]

    assert isinstance(transitions, list)
    assert len(transitions) > 0


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
            }
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


# FIXME: This test is failing


@test("route: patch execution")
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

    response = make_request(
        method="PATCH",
        url=f"/tasks/{task.id!s}/executions/{execution['id']!s}",
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
