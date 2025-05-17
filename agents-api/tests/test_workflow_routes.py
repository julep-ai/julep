# Tests for task queries

from uuid_extensions import uuid7
import pytest

from tests.fixtures import make_request, test_agent
from tests.utils import patch_testing_temporal


@pytest.mark.asyncio
async def test_workflow_route_evaluate_step_single(
    """workflow route: evaluate step single"""
    make_request=make_request,
    agent=test_agent,
):
    agent_id = str(agent.id)
    task_id = str(uuid7())

    async with patch_testing_temporal():
        task_data = {
            "name": "test task",
            "description": "test task about",
            "input_schema": {"type": "object", "additionalProperties": True},
            "main": [{"evaluate": {"hello": '"world"'}}],
        }

        make_request(
            method="POST",
            url=f"/agents/{agent_id}/tasks/{task_id}",
            json=task_data,
        ).raise_for_status()

        execution_data = {"input": {"test": "input"}}

        make_request(
            method="POST",
            url=f"/tasks/{task_id}/executions",
            json=execution_data,
        ).raise_for_status()


@pytest.mark.asyncio
async def test_workflow_route_evaluate_step_single_with_yaml(
    """workflow route: evaluate step single with yaml"""
    make_request=make_request,
    agent=test_agent,
):
    agent_id = str(agent.id)

    async with patch_testing_temporal():
        task_data = """
name: test task
description: test task about
input_schema:
  type: object
  additionalProperties: true

main:
  - evaluate:
      hello: '"world"'
"""

        result = (
            make_request(
                method="POST",
                url=f"/agents/{agent_id}/tasks",
                content=task_data.encode("utf-8"),
                headers={"Content-Type": "text/yaml"},
            )
            .raise_for_status()
            .json()
        )

        task_id = result["id"]

        execution_data = {"input": {"test": "input"}}

        make_request(
            method="POST",
            url=f"/tasks/{task_id}/executions",
            json=execution_data,
        ).raise_for_status()


@pytest.mark.asyncio
async def test_workflow_route_evaluate_step_single_with_yaml_nested(
    """workflow route: evaluate step single with yaml - nested"""
    make_request=make_request,
    agent=test_agent,
):
    agent_id = str(agent.id)

    async with patch_testing_temporal():
        task_data = """
name: test task
description: test task about
input_schema:
  type: object
  additionalProperties: true

main:
  - evaluate:
      hello: '"world"'
      hello2:
        hello3:
          hello4: inputs[0]['test']
"""

        result = (
            make_request(
                method="POST",
                url=f"/agents/{agent_id}/tasks",
                content=task_data.encode("utf-8"),
                headers={"Content-Type": "text/yaml"},
            )
            .raise_for_status()
            .json()
        )

        task_id = result["id"]

        execution_data = {"input": {"test": "input"}}

        make_request(
            method="POST",
            url=f"/tasks/{task_id}/executions",
            json=execution_data,
        ).raise_for_status()


@pytest.mark.asyncio
async def test_workflow_route_create_or_update_evaluate_step_single_with_yaml(
    """workflow route: create or update: evaluate step single with yaml"""
    make_request=make_request,
    agent=test_agent,
):
    agent_id = str(agent.id)
    task_id = str(uuid7())

    async with patch_testing_temporal():
        task_data = """
name: test task
description: test task about
input_schema:
  type: object
  additionalProperties: true

main:
  - evaluate:
      hello: '"world"'
"""

        make_request(
            method="POST",
            url=f"/agents/{agent_id}/tasks/{task_id}",
            content=task_data.encode("utf-8"),
            headers={"Content-Type": "text/yaml"},
        ).raise_for_status()

        execution_data = {"input": {"test": "input"}}

        make_request(
            method="POST",
            url=f"/tasks/{task_id}/executions",
            json=execution_data,
        ).raise_for_status()
