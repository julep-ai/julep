# Tests for task queries

import asyncio
import json
from unittest.mock import patch

import yaml
from google.protobuf.json_format import MessageToDict
from litellm.types.utils import Choices, ModelResponse
from ward import raises, skip, test

from agents_api.autogen.openapi_model import (
    CreateExecutionRequest,
    CreateTaskRequest,
)
from agents_api.models.task.create_task import create_task
from agents_api.routers.tasks.create_task_execution import start_execution
from tests.fixtures import cozo_client, test_agent, test_developer_id
from tests.utils import patch_integration_service, patch_testing_temporal

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


@test("workflow: return step direct")
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
                    {"return": {"value": '_["hello"]'}},
                    {"return": {"value": '"banana"'}},
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


@test("workflow: return step nested")
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
                    {"log": "{{_.hello}}"},
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
                    {
                        "log": '{{_["hell"].strip()}}'
                    },  # <--- The "hell" key does not exist
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


@test("workflow: system call - list agents")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={})

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "Test system tool task",
                "description": "List agents using system call",
                "input_schema": {"type": "object"},
                "tools": [
                    {
                        "name": "list_agents",
                        "description": "List all agents",
                        "type": "system",
                        "system": {"resource": "agent", "operation": "list"},
                    },
                ],
                "main": [
                    {
                        "tool": "list_agents",
                        "arguments": {
                            "limit": "10",
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
        assert isinstance(result, list)
        # Result's length should be less than or equal to the limit
        assert len(result) <= 10
        # Check if all items are agent dictionaries
        assert all(isinstance(agent, dict) for agent in result)
        # Check if each agent has an 'id' field
        assert all("id" in agent for agent in result)


@test("workflow: tool call api_call")
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
                "tools": [
                    {
                        "type": "api_call",
                        "name": "hello",
                        "api_call": {
                            "method": "GET",
                            "url": "https://httpbin.org/get",
                        },
                    }
                ],
                "main": [
                    {
                        "tool": "hello",
                        "arguments": {
                            "params": {"test": "_.test"},
                        },
                    },
                    {
                        "evaluate": {"hello": "_.json.args.test"},
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


@test("workflow: tool call api_call test retry")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})
    status_codes_to_retry = ",".join(str(code) for code in (408, 429, 503, 504))

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "tools": [
                    {
                        "type": "api_call",
                        "name": "hello",
                        "api_call": {
                            "method": "GET",
                            "url": f"https://httpbin.org/status/{status_codes_to_retry}",
                        },
                    }
                ],
                "main": [
                    {
                        "tool": "hello",
                        "arguments": {
                            "params": {"test": "_.test"},
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
        mock_run_task_execution_workflow.assert_called_once()

        # Let it run for a bit
        result_coroutine = handle.result()
        task = asyncio.create_task(result_coroutine)
        try:
            await asyncio.wait_for(task, timeout=3)
        except BaseException:
            task.cancel()

        # Get the history
        history = await handle.fetch_history()
        events = [MessageToDict(e) for e in history.events]
        assert len(events) > 0

        # NOTE: super janky but works
        events_strings = [json.dumps(event) for event in events]
        num_retries = len(
            [event for event in events_strings if "execute_api_call" in event]
        )

        assert num_retries >= 2


@test("workflow: tool call integration dummy")
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
                "tools": [
                    {
                        "type": "integration",
                        "name": "hello",
                        "integration": {
                            "provider": "dummy",
                        },
                    }
                ],
                "main": [
                    {
                        "tool": "hello",
                        "arguments": {"test": "_.test"},
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
        assert result["test"] == data.input["test"]


@skip("integration service patch not working")
@test("workflow: tool call integration mocked weather")
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
                "tools": [
                    {
                        "type": "integration",
                        "name": "get_weather",
                        "integration": {
                            "provider": "weather",
                            "setup": {"openweathermap_api_key": "test"},
                            "arguments": {"test": "fake"},
                        },
                    }
                ],
                "main": [
                    {
                        "tool": "get_weather",
                        "arguments": {"location": "_.test"},
                    },
                ],
            }
        ),
        client=client,
    )

    expected_output = {"temperature": 20, "humidity": 60}

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        with patch_integration_service(expected_output) as mock_integration_service:
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
            mock_integration_service.assert_called_once()

            result = await handle.result()
            assert result == expected_output


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
                    {"wait_for_input": {"info": {"hi": '"bye"'}}},
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
        result_coroutine = handle.result()
        task = asyncio.create_task(result_coroutine)
        try:
            await asyncio.wait_for(task, timeout=3)
        except asyncio.TimeoutError:
            task.cancel()

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

        assert "wait_for_input_step" in activities_scheduled


@test("workflow: foreach wait for input step start")
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
                            "do": {"wait_for_input": {"info": {"hi": '"bye"'}}},
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

        # Let it run for a bit
        result_coroutine = handle.result()
        task = asyncio.create_task(result_coroutine)
        try:
            await asyncio.wait_for(task, timeout=3)
        except asyncio.TimeoutError:
            task.cancel()

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

        assert "for_each_step" in activities_scheduled


@test("workflow: if-else step")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    task_def = CreateTaskRequest(
        **{
            "name": "test task",
            "description": "test task about",
            "input_schema": {"type": "object", "additionalProperties": True},
            "main": [
                {
                    "if": "False",
                    "then": {"evaluate": {"hello": '"world"'}},
                    "else": {"evaluate": {"hello": "random.randint(0, 10)"}},
                },
            ],
        }
    )

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=task_def,
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
        assert result["hello"] in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


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
        assert result[0]["hello"] == "world"


@test("workflow: map reduce step")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    data = CreateExecutionRequest(input={"test": "input"})

    map_step = {
        "over": "'a b c'.split()",
        "map": {
            "evaluate": {"res": "_"},
        },
    }

    task_def = {
        "name": "test task",
        "description": "test task about",
        "input_schema": {"type": "object", "additionalProperties": True},
        "main": [map_step],
    }

    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(**task_def),
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
        assert [r["res"] for r in result] == ["a", "b", "c"]


for p in [1, 3, 5]:

    @test(f"workflow: map reduce step parallel (parallelism={p})")
    async def _(
        client=cozo_client,
        developer_id=test_developer_id,
        agent=test_agent,
    ):
        data = CreateExecutionRequest(input={"test": "input"})

        map_step = {
            "over": "'a b c d'.split()",
            "map": {
                "evaluate": {"res": "_ + '!'"},
            },
            "parallelism": p,
        }

        task_def = {
            "name": "test task",
            "description": "test task about",
            "input_schema": {"type": "object", "additionalProperties": True},
            "main": [map_step],
        }

        task = create_task(
            developer_id=developer_id,
            agent_id=agent.id,
            data=CreateTaskRequest(**task_def),
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
            assert [r["res"] for r in result] == [
                "a!",
                "b!",
                "c!",
                "d!",
            ]


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
            result = result["choices"][0]["message"]
            assert result["content"] == "Hello, world!"
            assert result["role"] == "assistant"


@test("workflow: prompt step unwrap")
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
                            "unwrap": True,
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
            assert result == "Hello, world!"


@test("workflow: set and get steps")
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
                    {"set": {"test_key": '"test_value"'}},
                    {"get": "test_key"},
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
        assert result == "test_value"


@test("workflow: execute yaml task")
async def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    mock_model_response = ModelResponse(
        id="fake_id",
        choices=[
            Choices(
                message={"role": "assistant", "content": "found: true\nvalue: 'Gaga'"}
            )
        ],
        created=0,
        object="text_completion",
    )

    with patch("agents_api.clients.litellm.acompletion") as acompletion, open(
        "./tests/sample_tasks/find_selector.yaml", "r"
    ) as task_file:
        input = dict(
            screenshot_base64="iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA",
            network_requests=[{"request": {}, "response": {"body": "Lady Gaga"}}],
            parameters=["name"],
        )
        task_definition = yaml.safe_load(task_file)
        acompletion.return_value = mock_model_response
        data = CreateExecutionRequest(input=input)

        task = create_task(
            developer_id=developer_id,
            agent_id=agent.id,
            data=CreateTaskRequest(**task_definition),
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

            await handle.result()
