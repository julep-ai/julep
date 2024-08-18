# Tests for task queries

from ward import test, raises

from agents_api.autogen.openapi_model import CreateExecutionRequest, CreateTaskRequest
from agents_api.models.task.create_task import create_task
from agents_api.routers.tasks.create_task_execution import start_execution

from .fixtures import cozo_client, test_agent, test_developer_id
from .utils import patch_testing_temporal


@test("workflow: evaluate step single")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "main": [{"evaluate": {"hello": '"world"'}}],
            }
        ),
        client=client,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            client=client,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == "world"


@test("workflow: evaluate step multiple")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "main": [
                    {"evaluate": {"hello": '"nope"'}},
                    {"evaluate": {"hello": '"world"'}},
                ],
            }
        ),
        client=client,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            client=client,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == "world"


@test("workflow: variable access in expressions")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "main": [
                    # Testing that we can access the input
                    {"evaluate": {"hello": '_["test"]'}},
                ],
            }
        ),
        client=client,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            client=client,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == data.input["test"]


@test("workflow: yield step")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "other_workflow": [
                    # Testing that we can access the input
                    {"evaluate": {"hello": '_["test"]'}},
                ],
                "main": [
                    # Testing that we can access the input
                    {
                        "workflow": "other_workflow",
                        "arguments": {"test": '_["test"]'},
                    },
                ],
            }
        ),
        client=client,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            client=client,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == data.input["test"]


@test("workflow: sleep step")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "other_workflow": [
                    # Testing that we can access the input
                    {"evaluate": {"hello": '_["test"]'}},
                    {"sleep": {"days": 5}},
                ],
                "main": [
                    # Testing that we can access the input
                    {
                        "workflow": "other_workflow",
                        "arguments": {"test": '_["test"]'},
                    },
                ],
            }
        ),
        client=client,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            client=client,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == data.input["test"]


@test("workflow: return step")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "other_workflow": [
                    # Testing that we can access the input
                    {"evaluate": {"hello": '_["test"]'}},
                    {"return": {"value": '_["hello"]'}},
                    {"return": {"value": '"banana"'}},
                ],
                "main": [
                    # Testing that we can access the input
                    {
                        "workflow": "other_workflow",
                        "arguments": {"test": '_["test"]'},
                    },
                ],
            }
        ),
        client=client,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            client=client,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["value"] == data.input["test"]


@test("workflow: log step")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "other_workflow": [
                    # Testing that we can access the input
                    {"evaluate": {"hello": '_["test"]'}},
                    {"log": '_["hello"]'},
                ],
                "main": [
                    # Testing that we can access the input
                    {
                        "workflow": "other_workflow",
                        "arguments": {"test": '_["test"]'},
                    },
                ],
            }
        ),
        client=client,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            client=client,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == data.input["test"]


@test("workflow: log step expression fail")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "other_workflow": [
                    # Testing that we can access the input
                    {"evaluate": {"hello": '_["test"]'}},
                    {"log": '_["hell"]'},  # <--- The "hell" key does not exist
                ],
                "main": [
                    # Testing that we can access the input
                    {
                        "workflow": "other_workflow",
                        "arguments": {"test": '_["test"]'},
                    },
                ],
            }
        ),
        client=client,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        with raises(BaseException):
            execution, handle = await start_execution(
                developer_id=developer_id,
                task_id=task.id,
                data=data,
                client=client,
            )

            assert handle is not None
            assert execution.task_id == task.id
            assert execution.input == data.input
            mock_run_task_execution_workflow.assert_called_once()

            result = await handle.result()
            assert result["hello"] == data.input["test"]
