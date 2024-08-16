# Tests for task routes

from uuid import uuid4

from ward import test

from tests.fixtures import (
    client,
    make_request,
    test_agent,
    test_execution,
    test_task,
    test_transition,
)


@test("route: unauthorized should fail")
def _(client=client, agent=test_agent):
    data = dict(
        name="test user",
        main=[
            {
                "kind_": "evaluate",
                "evaluate": {
                    "additionalProp1": "value1",
                },
            }
        ],
    )

    response = client.request(
        method="POST",
        url=f"/agents/{str(agent.id)}/tasks",
        data=data,
    )

    assert response.status_code == 403


@test("route: create task")
def _(make_request=make_request, agent=test_agent):
    data = dict(
        name="test user",
        main=[
            {
                "kind_": "evaluate",
                "evaluate": {
                    "additionalProp1": "value1",
                },
            }
        ],
    )

    response = make_request(
        method="POST",
        url=f"/agents/{str(agent.id)}/tasks",
        json=data,
    )

    assert response.status_code == 201


@test("route: create task execution")
def _(make_request=make_request, task=test_task):
    data = dict(
        input={},
        metadata={},
    )

    response = make_request(
        method="POST",
        url=f"/tasks/{str(task.id)}/executions",
        json=data,
    )

    assert response.status_code == 201


@test("route: get execution not exists")
def _(make_request=make_request):
    execution_id = str(uuid4())

    response = make_request(
        method="GET",
        url=f"/executions/{execution_id}",
    )

    assert response.status_code == 404


@test("route: get execution exists")
def _(make_request=make_request, execution=test_execution):
    response = make_request(
        method="GET",
        url=f"/executions/{str(execution.id)}",
    )

    assert response.status_code == 200


@test("route: get task not exists")
def _(make_request=make_request):
    task_id = str(uuid4())

    response = make_request(
        method="GET",
        url=f"/tasks/{task_id}",
    )

    assert response.status_code == 400


@test("route: get task exists")
def _(make_request=make_request, task=test_task):
    response = make_request(
        method="GET",
        url=f"/tasks/{str(task.id)}",
    )

    assert response.status_code == 200


@test("model: list execution transitions")
def _(make_request=make_request, transition=test_transition):
    response = make_request(
        method="GET",
        url=f"/executions/{str(transition.execution_id)}/transitions",
    )

    assert response.status_code == 200
    response = response.json()
    transitions = response["items"]

    assert isinstance(transitions, list)
    assert len(transitions) > 0


@test("model: list task executions")
def _(make_request=make_request, execution=test_execution):
    response = make_request(
        method="GET",
        url=f"/tasks/{str(execution.task_id)}/executions",
    )

    assert response.status_code == 200
    response = response.json()
    executions = response["items"]

    assert isinstance(executions, list)
    assert len(executions) > 0


@test("model: list tasks")
def _(make_request=make_request, agent=test_agent):
    response = make_request(
        method="GET",
        url=f"/agents/{str(agent.id)}/tasks",
    )

    assert response.status_code == 200
    response = response.json()
    tasks = response["items"]

    assert isinstance(tasks, list)
    assert len(tasks) > 0


@test("model: patch execution")
def _(make_request=make_request, execution=test_execution):
    data = dict(
        status="running",
    )

    response = make_request(
        method="PATCH",
        url=f"/tasks/{str(execution.task_id)}/executions/{str(execution.id)}",
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
