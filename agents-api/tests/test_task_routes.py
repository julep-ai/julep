# Tests for task routes

from agents_api.autogen.openapi_model import (
    Transition,
)
from agents_api.queries.executions.create_execution_transition import (
    create_execution_transition,
)
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


@test("route: get execution exists with transition count")
def _(make_request=make_request, execution=test_execution_started):
    response = make_request(
        method="GET",
        url=f"/executions/{execution.id!s}",
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["transition"]["count"] > 0


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
