# Tests for task queries

from uuid_extensions import uuid7
from ward import test

from agents_api.clients.pg import create_db_pool
from tests.fixtures import pg_dsn, test_agent, test_developer_id
from tests.utils import patch_http_client_with_temporal


@test("workflow route: evaluate step single")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    pool = await create_db_pool(dsn=dsn)
    agent_id = str(agent.id)
    task_id = str(uuid7())

    async with patch_http_client_with_temporal(
        postgres_pool=pool, developer_id=developer_id
    ) as (
        make_request,
        postgres_pool,
    ):
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

        execution_data = dict(input={"test": "input"})

        make_request(
            method="POST",
            url=f"/tasks/{task_id}/executions",
            json=execution_data,
        ).raise_for_status()


@test("workflow route: evaluate step single with yaml")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    pool = await create_db_pool(dsn=dsn)
    agent_id = str(agent.id)

    async with patch_http_client_with_temporal(
        postgres_pool=pool, developer_id=developer_id
    ) as (
        make_request,
        postgres_pool,
    ):
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

        execution_data = dict(input={"test": "input"})

        make_request(
            method="POST",
            url=f"/tasks/{task_id}/executions",
            json=execution_data,
        ).raise_for_status()


@test("workflow route: create or update: evaluate step single with yaml")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    pool = await create_db_pool(dsn=dsn)
    agent_id = str(agent.id)
    task_id = str(uuid7())

    async with patch_http_client_with_temporal(
        postgres_pool=pool, developer_id=developer_id
    ) as (
        make_request,
        postgres_pool,
    ):
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

        execution_data = dict(input={"test": "input"})

        make_request(
            method="POST",
            url=f"/tasks/{task_id}/executions",
            json=execution_data,
        ).raise_for_status()
