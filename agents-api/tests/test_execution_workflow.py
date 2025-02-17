# Tests for task queries

import asyncio
import ward.testing
import json
from temporalio import activity
from unittest.mock import patch

import yaml
from agents_api.autogen.openapi_model import (
    CreateExecutionRequest,
    CreateTaskRequest,
)
from agents_api.app import app
from agents_api.clients.pg import create_db_pool
from agents_api.queries.tasks.create_task import create_task
from agents_api.routers.tasks.create_task_execution import start_execution
from google.protobuf.json_format import MessageToDict
from litellm import Choices, ModelResponse
from ward import raises, skip, test

from .fixtures import (
    pg_dsn,
    s3_client,
    test_agent,
    test_developer_id,
)
from .utils import patch_integration_service, patch_testing_temporal


@activity.defn(name="base_evaluate")
async def base_evaluate_activity_mocked(*args, **kwargs):
    return "base_evaluate_activity_mocked"


@activity.defn(name="transition_step")
async def transition_step_mocked(*args, **kwargs):
    return "transition_step_mocked"


@activity.defn(name="save_inputs_remote")
async def save_inputs_remote_mocked(*args, **kwargs):
    return ["save_inputs_remote_mocked"]


@test("workflow: evaluate step single")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
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
        assert result == "base_evaluate_activity_mocked"


@test("workflow: evaluate step multiple")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
        save_inputs_remote_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
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
        assert result == "base_evaluate_activity_mocked"

@skip("it freezes")
@test("workflow: yield step")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
        save_inputs_remote_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
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
        assert result == "base_evaluate_activity_mocked"


@test("workflow: sleep step")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
        save_inputs_remote_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
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
        assert result == "save_inputs_remote_mocked"


@test("workflow: return step direct")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
        save_inputs_remote_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
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
        assert result == "base_evaluate_activity_mocked"


@test("workflow: return step nested")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
        save_inputs_remote_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
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
        assert result == "base_evaluate_activity_mocked"


@test("workflow: log step")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
        save_inputs_remote_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
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
        assert result == "save_inputs_remote_mocked"


@skip("it freezes")
@test("workflow: log step expression fail")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
        save_inputs_remote_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
        with raises(BaseException):
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
            assert result == "save_inputs_remote_mocked"


@skip("it freezes")
@test("workflow: system call - list agents")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
        save_inputs_remote_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
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
        assert result == "save_inputs_remote_mocked"


@test("workflow: tool call api_call")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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
                }
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

    activities = [
        base_evaluate_activity_mocked,
        transition_step_mocked,
        save_inputs_remote_mocked,
    ]

    async with patch_testing_temporal(activities=activities) as (_, mock_run_task_execution_workflow):
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
        assert result == "save_inputs_remote_mocked"


# @skip("needs to be fixed")
@test("workflow: tool call api_call test retry")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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
                }
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


# @skip("needs to be fixed")
@test("workflow: tool call integration dummy")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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
                }
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


# @skip("needs to be fixed")
@test("workflow: tool call integration mocked weather")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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
                }
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


# @skip("needs to be fixed")
@test("workflow: wait for input step start")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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


# @skip("needs to be fixed")
@test("workflow: foreach wait for input step start")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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


# @skip("needs to be fixed")
@test("workflow: if-else step")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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


# @skip("needs to be fixed")
@test("workflow: switch step")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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
                    ]
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


# @skip("needs to be fixed")
@test("workflow: for each step")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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


# @skip("needs to be fixed")
@test("workflow: map reduce step")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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

    # @skip("needs to be fixed")
    @test(f"workflow: map reduce step parallel (parallelism={p})")
    async def _(
        dsn=pg_dsn,
        developer_id=test_developer_id,
        agent=test_agent,
        _s3_client=s3_client,  # Adding coz blob store might be used
    ):
        pool = await create_db_pool(dsn=dsn)
        app.state.postgres_pool = pool
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


# @skip("needs to be fixed")
@test("workflow: prompt step (python expression)")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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


# @skip("needs to be fixed")
@test("workflow: prompt step")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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


# @skip("needs to be fixed")
@test("workflow: prompt step unwrap")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    _s3_client=s3_client,  # Adding coz blob store might be used
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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


# @skip("needs to be fixed")
@test("workflow: set and get steps")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
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


# @skip("needs to be fixed")
@test("workflow: execute yaml task")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool
    mock_model_response = ModelResponse(
        id="fake_id",
        choices=[
            Choices(message={"role": "assistant", "content": "found: true\nvalue: 'Gaga'"})
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


def always_one():
    return 1

ward.testing.MAX_PROCESSES = 1  # set global max_process to 1
ward.testing.available_cpu_count = always_one  # override cpu count