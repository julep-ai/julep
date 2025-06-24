from uuid_extensions import uuid7

from tests.utils import patch_testing_temporal


async def test_workflow_route_evaluate_step_single(
    make_request,
    test_agent,
):
    """workflow route: evaluate step single"""
    agent_id = str(test_agent.id)
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


async def test_workflow_route_evaluate_step_single_with_yaml(
    make_request,
    test_agent,
):
    """workflow route: evaluate step single with yaml"""
    agent_id = str(test_agent.id)

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


async def test_workflow_route_evaluate_step_single_with_yaml_nested(
    make_request,
    test_agent,
):
    """workflow route: evaluate step single with yaml - nested"""
    agent_id = str(test_agent.id)

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


async def test_workflow_route_create_or_update_evaluate_step_single_with_yaml(
    make_request,
    test_agent,
):
    """workflow route: create or update: evaluate step single with yaml"""
    agent_id = str(test_agent.id)
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
