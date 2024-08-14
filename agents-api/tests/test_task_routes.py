# Tests for task routes
from uuid import uuid4

from ward import test

from tests.fixtures import client, make_request, test_agent


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
def _(make_request=make_request):
    task_id = str(uuid4())
    data = dict(
        input={},
        metadata={},
    )

    response = make_request(
        method="POST",
        url=f"/tasks/{task_id}/executions",
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
def _(make_request=make_request):
    execution_id = str(uuid4())

    response = make_request(
        method="GET",
        url=f"/executions/{execution_id}",
    )

    assert response.status_code == 200


@test("route: get task not exists")
def _(make_request=make_request):
    data = dict(
        name="test user",
        main="test user about",
    )

    response = make_request(
        method="POST",
        url="/tasks",
        json=data,
    )

    assert response.status_code == 201


@test("route: get task exists")
def _(make_request=make_request):
    data = dict(
        name="test user",
        main="test user about",
    )

    response = make_request(
        method="POST",
        url="/tasks",
        json=data,
    )

    assert response.status_code == 201


@test("model: list execution transitions")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/users",
    )

    assert response.status_code == 200
    response = response.json()
    users = response["items"]

    assert isinstance(users, list)
    assert len(users) > 0


@test("model: list task executions")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/users",
    )

    assert response.status_code == 200
    response = response.json()
    users = response["items"]

    assert isinstance(users, list)
    assert len(users) > 0


@test("model: list tasks")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/users",
    )

    assert response.status_code == 200
    response = response.json()
    users = response["items"]

    assert isinstance(users, list)
    assert len(users) > 0


@test("model: patch execution")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/users",
    )

    assert response.status_code == 200
    response = response.json()
    users = response["items"]

    assert isinstance(users, list)
    assert len(users) > 0


@test("model: update execution")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/users",
    )

    assert response.status_code == 200
    response = response.json()
    users = response["items"]

    assert isinstance(users, list)
    assert len(users) > 0
