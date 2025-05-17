# Tests for task queries

import asyncio
import json
from unittest.mock import patch

import yaml
from agents_api.autogen.openapi_model import (
    CreateExecutionRequest,
    CreateTaskRequest,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.tasks.create_task import create_task
from agents_api.routers.tasks.create_task_execution import start_execution
from google.protobuf.json_format import MessageToDict
from litellm import Choices, ModelResponse
import pytest

from .fixtures import (
    pg_dsn,
    s3_client,
    test_agent,
    test_developer_id,
)
from .utils import patch_integration_service, patch_testing_temporal


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_evaluate_step_single(
    """workflow: evaluate step single"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"hello": '"world"'}}],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == "world"


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_evaluate_step_multiple(
    """workflow: evaluate step multiple"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[
                {"evaluate": {"hello": '"nope"'}},
                {"evaluate": {"hello": '"world"'}},
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == "world"


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_variable_access_in_expressions(
    """workflow: variable access in expressions"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[
                # Testing that we can access the input
                {"evaluate": {"hello": '_["test"]'}},
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == data.input["test"]


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_yield_step(
    """workflow: yield step"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            other_workflow=[
                # Testing that we can access the input
                {"evaluate": {"hello": '_["test"]'}},
            ],
            main=[
                # Testing that we can access the input
                {
                    "workflow": "other_workflow",
                    "arguments": {"test": '_["test"]'},
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == data.input["test"]


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_sleep_step(
    """workflow: sleep step"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            other_workflow=[
                # Testing that we can access the input
                {"evaluate": {"hello": '_["test"]'}},
                {"sleep": {"days": 5}},
            ],
            main=[
                # Testing that we can access the input
                {
                    "workflow": "other_workflow",
                    "arguments": {"test": '_["test"]'},
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == data.input["test"]


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_return_step_direct(
    """workflow: return step direct"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[
                # Testing that we can access the input
                {"evaluate": {"hello": '_["test"]'}},
                {"return": {"value": '_["hello"]'}},
                {"return": {"value": '"banana"'}},
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["value"] == data.input["test"]


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_return_step_nested(
    """workflow: return step nested"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            other_workflow=[
                # Testing that we can access the input
                {"evaluate": {"hello": '_["test"]'}},
                {"return": {"value": '_["hello"]'}},
                {"return": {"value": '"banana"'}},
            ],
            main=[
                # Testing that we can access the input
                {
                    "workflow": "other_workflow",
                    "arguments": {"test": '_["test"]'},
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["value"] == data.input["test"]


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_log_step(
    """workflow: log step"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            other_workflow=[
                # Testing that we can access the input
                {"evaluate": {"hello": '_["test"]'}},
                {"log": "{{_.hello}}"},
            ],
            main=[
                # Testing that we can access the input
                {
                    "workflow": "other_workflow",
                    "arguments": {"test": '_["test"]'},
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == data.input["test"]


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_log_step_expression_fail(
    """workflow: log step expression fail"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            other_workflow=[
                # Testing that we can access the input
                {"evaluate": {"hello": '_["test"]'}},
                {"log": '{{_["hell"].strip()}}'},  # <--- The "hell" key does not exist
            ],
            main=[
                # Testing that we can access the input
                {
                    "workflow": "other_workflow",
                    "arguments": {"test": '_["test"]'},
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        with pytest.pytest.raises(BaseException):
            execution, handle = await start_execution(
                developer_id=developer_id,
                task_id=task.id,
                data=data,
                connection_pool=pool,
            )

            assert handle is not None
            assert execution.task_id == task.id
            assert execution.input == data.input
            mock_run_task_execution_workflow.assert_called_once()

            result = await handle.result()
            assert result["hello"] == data.input["test"]


@pytest.mark.skip(reason="workflow: thread race condition")
@pytest.mark.asyncio
async def test_workflow_system_call_list_agents(
    """workflow: system call - list agents"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="Test system tool task",
            description="List agents using system call",
            input_schema={"type": "object"},
            tools=[
                {
                    "name": "list_agents",
                    "description": "List all agents",
                    "type": "system",
                    "system": {"resource": "agent", "operation": "list"},
                },
            ],
            main=[
                {
                    "tool": "list_agents",
                    "arguments": {
                        "limit": "10",
                    },
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        pool = await create_db_pool(dsn=dsn)
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
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


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_tool_call_api_call(
    """workflow: tool call api_call"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            inherit_tools=True,
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            tools=[
                {
                    "type": "api_call",
                    "name": "hello",
                    "api_call": {
                        "method": "GET",
                        "url": "https://httpbin.org/get",
                    },
                },
            ],
            main=[
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
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == data.input["test"]


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_tool_call_api_call_test_retry(
    """workflow: tool call api_call test retry"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})
    status_codes_to_retry = ",".join(str(code) for code in (408, 429, 503, 504))

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            inherit_tools=True,
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            tools=[
                {
                    "type": "api_call",
                    "name": "hello",
                    "api_call": {
                        "method": "GET",
                        "url": f"https://httpbin.org/status/{status_codes_to_retry}",
                    },
                },
            ],
            main=[
                {
                    "tool": "hello",
                    "arguments": {
                        "params": {"test": "_.test"},
                    },
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        _execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        mock_run_task_execution_workflow.assert_called_once()

        # Let it run for a bit
        result_coroutine = handle.result()
        task = asyncio.create_task(result_coroutine)
        try:
            await asyncio.wait_for(task, timeout=10)
        except BaseException:
            task.cancel()

        # Get the history
        history = await handle.fetch_history()
        events = [MessageToDict(e) for e in history.events]
        assert len(events) > 0

        # NOTE: super janky but works
        events_strings = [json.dumps(event) for event in events]
        num_retries = len([event for event in events_strings if "execute_api_call" in event])

        assert num_retries >= 2


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_tool_call_integration_dummy(
    """workflow: tool call integration dummy"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            tools=[
                {
                    "type": "integration",
                    "name": "hello",
                    "integration": {
                        "provider": "dummy",
                    },
                },
            ],
            main=[
                {
                    "tool": "hello",
                    "arguments": {"test": "_.test"},
                },
            ],
            inherit_tools=True,
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input
        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["test"] == data.input["test"]


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_tool_call_integration_mocked_weather(
    """workflow: tool call integration mocked weather"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            tools=[
                {
                    "type": "integration",
                    "name": "get_weather",
                    "integration": {
                        "provider": "weather",
                        "setup": {"openweathermap_api_key": "test"},
                        "arguments": {"location": "fake"},
                    },
                },
            ],
            main=[
                {
                    "tool": "get_weather",
                    "arguments": {"location": "_.test"},
                },
            ],
        ),
        connection_pool=pool,
    )

    expected_output = {"temperature": 20, "humidity": 60}

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        with patch_integration_service(expected_output) as mock_integration_service:
            execution, handle = await start_execution(
                developer_id=developer_id,
                task_id=task.id,
                data=data,
                connection_pool=pool,
            )

            assert handle is not None
            assert execution.task_id == task.id
            assert execution.input == data.input
            mock_run_task_execution_workflow.assert_called_once()
            result = await handle.result()
            # Verify the integration service was called with correct arguments
            mock_integration_service.assert_called_once()
            assert result == expected_output


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_wait_for_input_step_start(
    """workflow: wait for input step start"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[
                {"wait_for_input": {"info": {"hi": '"bye"'}}},
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
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
        except TimeoutError:
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
        activities_scheduled = [activity for activity in activities_scheduled if activity]

        assert "wait_for_input_step" in activities_scheduled


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_foreach_wait_for_input_step_start(
    """workflow: foreach wait for input step start"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[
                {
                    "foreach": {
                        "in": "'a b c'.split()",
                        "do": {"wait_for_input": {"info": {"hi": '"bye"'}}},
                    },
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
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
        except TimeoutError:
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
        activities_scheduled = [activity for activity in activities_scheduled if activity]

        assert "for_each_step" in activities_scheduled


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_if_else_step(
    """workflow: if-else step"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task_def = CreateTaskRequest(
        name="test task",
        description="test task about",
        input_schema={"type": "object", "additionalProperties": True},
        main=[
            {
                "if": "False",
                "then": {"evaluate": {"hello": '"world"'}},
                "else": {"evaluate": {"hello": "random.randint(0, 10)"}},
            },
        ],
    )

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=task_def,
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input

        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_switch_step(
    """workflow: switch step"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[
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
                    ],
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input

        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result["hello"] == "world"


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_for_each_step(
    """workflow: for each step"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[
                {
                    "foreach": {
                        "in": "'a b c'.split()",
                        "do": {"evaluate": {"hello": '"world"'}},
                    },
                },
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input

        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result[0]["hello"] == "world"


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_map_reduce_step(
    """workflow: map reduce step"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
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

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(**task_def),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input

        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert [r["res"] for r in result] == ["a", "b", "c"]


for p in [1, 3, 5]:

    @pytest.mark.skip(reason="needs to be fixed")
    @pytest.mark.asyncio
    async def test_workflow_map_reduce_step_parallel_parallelism_p(
        """workflow: map reduce step parallel (parallelism={p})"""
        dsn=pg_dsn,
        developer_id=test_developer_id,
        agent=test_agent,
        _s3_client=s3_client,  # Adding coz blob store might be used
    ):
        pool = await create_db_pool(dsn=dsn)
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

        task = await create_task(
            developer_id=developer_id,
            agent_id=agent.id,
            data=CreateTaskRequest(**task_def),
            connection_pool=pool,
        )

        async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
            execution, handle = await start_execution(
                developer_id=developer_id,
                task_id=task.id,
                data=data,
                connection_pool=pool,
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


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_prompt_step_python_expression(
    """workflow: prompt step (python expression)"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    mock_model_response = ModelResponse(
        id="fake_id",
        choices=[Choices(message={"role": "assistant", "content": "Hello, world!"})],
        created=0,
        object="text_completion",
    )

    with patch("agents_api.clients.litellm.acompletion") as acompletion:
        acompletion.return_value = mock_model_response
        data = CreateExecutionRequest(input={"test": "input"})

        task = await create_task(
            developer_id=developer_id,
            agent_id=agent.id,
            data=CreateTaskRequest(
                name="test task",
                description="test task about",
                input_schema={"type": "object", "additionalProperties": True},
                main=[
                    {
                        "prompt": "$_ [{'role': 'user', 'content': _.test}]",
                        "settings": {},
                    },
                ],
            ),
            connection_pool=pool,
        )

        async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
            execution, handle = await start_execution(
                developer_id=developer_id,
                task_id=task.id,
                data=data,
                connection_pool=pool,
            )

            assert handle is not None
            assert execution.task_id == task.id
            assert execution.input == data.input

            mock_run_task_execution_workflow.assert_called_once()

            result = await handle.result()
            result = result["choices"][0]["message"]
            assert result["content"] == "Hello, world!"
            assert result["role"] == "assistant"


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_prompt_step(
    """workflow: prompt step"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    mock_model_response = ModelResponse(
        id="fake_id",
        choices=[Choices(message={"role": "assistant", "content": "Hello, world!"})],
        created=0,
        object="text_completion",
    )

    with patch("agents_api.clients.litellm.acompletion") as acompletion:
        acompletion.return_value = mock_model_response
        data = CreateExecutionRequest(input={"test": "input"})

        task = await create_task(
            developer_id=developer_id,
            agent_id=agent.id,
            data=CreateTaskRequest(
                name="test task",
                description="test task about",
                input_schema={"type": "object", "additionalProperties": True},
                main=[
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
            ),
            connection_pool=pool,
        )

        async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
            execution, handle = await start_execution(
                developer_id=developer_id,
                task_id=task.id,
                data=data,
                connection_pool=pool,
            )

            assert handle is not None
            assert execution.task_id == task.id
            assert execution.input == data.input

            mock_run_task_execution_workflow.assert_called_once()

            result = await handle.result()
            result = result["choices"][0]["message"]
            assert result["content"] == "Hello, world!"
            assert result["role"] == "assistant"


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_prompt_step_unwrap(
    """workflow: prompt step unwrap"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    mock_model_response = ModelResponse(
        id="fake_id",
        choices=[Choices(message={"role": "assistant", "content": "Hello, world!"})],
        created=0,
        object="text_completion",
    )

    with patch("agents_api.clients.litellm.acompletion") as acompletion:
        acompletion.return_value = mock_model_response
        data = CreateExecutionRequest(input={"test": "input"})

        task = await create_task(
            developer_id=developer_id,
            agent_id=agent.id,
            data=CreateTaskRequest(
                name="test task",
                description="test task about",
                input_schema={"type": "object", "additionalProperties": True},
                main=[
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
            ),
            connection_pool=pool,
        )

        async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
            execution, handle = await start_execution(
                developer_id=developer_id,
                task_id=task.id,
                data=data,
                connection_pool=pool,
            )

            assert handle is not None
            assert execution.task_id == task.id
            assert execution.input == data.input

            mock_run_task_execution_workflow.assert_called_once()

            result = await handle.result()
            assert result == "Hello, world!"


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_set_and_get_steps(
    """workflow: set and get steps"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    pool = await create_db_pool(dsn=dsn)
    data = CreateExecutionRequest(input={"test": "input"})

    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[
                {"set": {"test_key": '"test_value"'}},
                {"get": "test_key"},
            ],
        ),
        connection_pool=pool,
    )

    async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
        execution, handle = await start_execution(
            developer_id=developer_id,
            task_id=task.id,
            data=data,
            connection_pool=pool,
        )

        assert handle is not None
        assert execution.task_id == task.id
        assert execution.input == data.input

        mock_run_task_execution_workflow.assert_called_once()

        result = await handle.result()
        assert result == "test_value"


@pytest.mark.skip(reason="needs to be fixed")
@pytest.mark.asyncio
async def test_workflow_execute_yaml_task(
    """workflow: execute yaml task"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    pool = await create_db_pool(dsn=dsn)
    mock_model_response = ModelResponse(
        id="fake_id",
        choices=[
            Choices(message={"role": "assistant", "content": "found: true\nvalue: 'Gaga'"}),
        ],
        created=0,
        object="text_completion",
    )

    with (
        patch("agents_api.clients.litellm.acompletion") as acompletion,
        open("./tests/sample_tasks/find_selector.yaml") as task_file,
    ):
        input = {
            "screenshot_base64": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA",
            "network_requests": [{"request": {}, "response": {"body": "Lady Gaga"}}],
            "parameters": ["name"],
        }
        task_definition = yaml.safe_load(task_file)
        acompletion.return_value = mock_model_response
        data = CreateExecutionRequest(input=input)

        task = await create_task(
            developer_id=developer_id,
            agent_id=agent.id,
            data=CreateTaskRequest(**task_definition),
            connection_pool=pool,
        )

        async with patch_testing_temporal() as (_, mock_run_task_execution_workflow):
            execution, handle = await start_execution(
                developer_id=developer_id,
                task_id=task.id,
                data=data,
                connection_pool=pool,
            )

            assert handle is not None
            assert execution.task_id == task.id
            assert execution.input == data.input

            mock_run_task_execution_workflow.assert_called_once()

            await handle.result()
