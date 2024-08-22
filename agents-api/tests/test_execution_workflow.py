# Tests for task queries

import asyncio
from unittest.mock import patch

from google.protobuf.json_format import MessageToDict
from litellm.types.utils import Choices, ModelResponse
from ward import raises, test

from agents_api.autogen.openapi_model import (
    CreateExecutionRequest,
    CreateTaskRequest,
    MainModel,
    MapOverEvaluate,
)
from agents_api.models.task.create_task import create_task
from agents_api.routers.tasks.create_task_execution import start_execution

from .fixtures import cozo_client, test_agent, test_developer_id
from .utils import patch_testing_temporal

EMBEDDING_SIZE: int = 1024


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


@test("workflow: wait for input step start")
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
                    {"wait_for_input": {"hi": '"bye"'}},
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

        # Let it run for a bit
        await asyncio.sleep(1)

        # Get the history
        history = await handle.fetch_history()
        events = [MessageToDict(e) for e in history.events]
        assert len(events) > 0

        activities_scheduled = [
            event.get("activityTaskScheduledEventAttributes", {})
            .get("activityType", {})
            .get("name")
            for event in events
            if "ACTIVITY_TASK_SCHEDULED" in event["eventType"]
        ]
        activities_scheduled = [
            activity for activity in activities_scheduled if activity
        ]

        assert activities_scheduled == [
            "wait_for_input_step",
            "transition_step",
            "raise_complete_async",
        ]


@test("workflow: if-else step")
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
                    {
                        "if": "True",
                        "then": {"evaluate": {"hello": '"world"'}},
                        "else": {"evaluate": {"hello": '"nope"'}},
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
        assert result["hello"] == "world"


@test("workflow: switch step")
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
                    {
                        "switch": [
                            {
                                "case": "False",
                                "then": {"evaluate": {"hello": '"bubbles"'}},
                            },
                            {
                                "case": "True",
                                "then": {"evaluate": {"hello": '"world"'}},
                            },
                            {
                                "case": "True",
                                "then": {"evaluate": {"hello": '"bye"'}},
                            },
                        ]
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
        assert result["hello"] == "world"


@test("workflow: for each step")
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
                    {
                        "foreach": {
                            "in": "'a b c'.split()",
                            "do": {"evaluate": {"hello": '"world"'}},
                        },
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
        assert result["hello"] == "world"


@test("workflow: map reduce step")
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
                    {
                        "over": "'a b c'.split()",
                        "evaluate": {"res": "_"},
                    },
                ],
            },
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
        assert result["res"] == {"test": "input"}


@test("workflow: prompt step")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    mock_model_response = ModelResponse(
        id="fake_id",
        choices=[Choices(message={"role": "assistant", "content": "Hello, world!"})],
        created=0,
        object="text_completion",
    )

    with patch("agents_api.clients.litellm.acompletion") as acompletion:
        acompletion.return_value = mock_model_response
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
                        {
                            "prompt": [
                                {
                                    "role": "user",
                                    "content": "message",
                                },
                            ],
                            "settings": {},
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
            assert result["content"] == "Hello, world!"
            assert result["role"] == "assistant"
