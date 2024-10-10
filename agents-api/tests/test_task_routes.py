# Tests for task routes

from uuid import uuid4

from ward import test

from tests.fixtures import (
    client,
    make_request,
    test_agent,
    test_execution,
    test_task,
)
from tests.utils import patch_testing_temporal


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
async def _(make_request=make_request, task=test_task):
    data = dict(
        input={},
        metadata={},
    )

    async with patch_testing_temporal():
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


# FIXME: This test is failing
# @test("route: list execution transitions")
# def _(make_request=make_request, execution=test_execution, transition=test_transition):
#     response = make_request(
#         method="GET",
#         url=f"/executions/{str(execution.id)}/transitions",
#     )

#     assert response.status_code == 200
#     response = response.json()
#     transitions = response["items"]

#     assert isinstance(transitions, list)
#     assert len(transitions) > 0


@test("route: list task executions")
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


@test("route: list tasks")
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


# FIXME: This test is failing

# @test("route: patch execution")
# async def _(make_request=make_request, task=test_task):
#     data = dict(
#         input={},
#         metadata={},
#     )

#     async with patch_testing_temporal():
#         response = make_request(
#             method="POST",
#             url=f"/tasks/{str(task.id)}/executions",
#             json=data,
#         )

#         execution = response.json()

#     data = dict(
#         status="running",
#     )

#     response = make_request(
#         method="PATCH",
#         url=f"/tasks/{str(task.id)}/executions/{str(execution['id'])}",
#         json=data,
#     )

#     assert response.status_code == 200

#     execution_id = response.json()["id"]

#     response = make_request(
#         method="GET",
#         url=f"/executions/{execution_id}",
#     )

#     assert response.status_code == 200
#     execution = response.json()

#     assert execution["status"] == "running"
