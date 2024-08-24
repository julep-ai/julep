# Tests for task queries

import os
from uuid import uuid4

from ward import raises, test

from ..fixtures import cozo_client, test_agent, test_developer_id
from ..utils import patch_embed_acompletion, patch_http_client_with_temporal

this_dir = os.path.dirname(__file__)


@test("workflow sample: find-selector create task")
async def _(
    cozo_client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    agent_id = str(agent.id)
    task_id = str(uuid4())

    with patch_embed_acompletion(), open(
        f"{this_dir}/find_selector.yaml", "r"
    ) as sample_file:
        task_def = sample_file.read()

        async with patch_http_client_with_temporal(
            cozo_client=cozo_client, developer_id=developer_id
        ) as (
            make_request,
            _,
        ):
            make_request(
                method="POST",
                url=f"/agents/{agent_id}/tasks/{task_id}",
                headers={"Content-Type": "application/x-yaml"},
                data=task_def,
            ).raise_for_status()


@test("workflow sample: find-selector start with bad input should fail")
async def _(
    cozo_client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    agent_id = str(agent.id)
    task_id = str(uuid4())

    with patch_embed_acompletion(), open(
        f"{this_dir}/find_selector.yaml", "r"
    ) as sample_file:
        task_def = sample_file.read()

        async with patch_http_client_with_temporal(
            cozo_client=cozo_client, developer_id=developer_id
        ) as (
            make_request,
            temporal_client,
        ):
            make_request(
                method="POST",
                url=f"/agents/{agent_id}/tasks/{task_id}",
                headers={"Content-Type": "application/x-yaml"},
                data=task_def,
            ).raise_for_status()

            execution_data = dict(input={"test": "input"})

            with raises(BaseException):
                make_request(
                    method="POST",
                    url=f"/tasks/{task_id}/executions",
                    json=execution_data,
                ).raise_for_status()


@test("workflow sample: find-selector start with correct input")
async def _(
    cozo_client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    agent_id = str(agent.id)
    task_id = str(uuid4())

    with patch_embed_acompletion(), open(
        f"{this_dir}/find_selector.yaml", "r"
    ) as sample_file:
        task_def = sample_file.read()

        async with patch_http_client_with_temporal(
            cozo_client=cozo_client, developer_id=developer_id
        ) as (
            make_request,
            temporal_client,
        ):
            make_request(
                method="POST",
                url=f"/agents/{agent_id}/tasks/{task_id}",
                headers={"Content-Type": "application/x-yaml"},
                data=task_def,
            ).raise_for_status()

            input = dict(
                screenshot_base64="iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA",
                network_requests=[{"request": {}, "response": {"body": "Lady Gaga"}}],
                parameters=["name"],
            )
            execution_data = dict(input=input)

            execution_created = make_request(
                method="POST",
                url=f"/tasks/{task_id}/executions",
                json=execution_data,
            ).json()

            handle = temporal_client.get_workflow_handle(execution_created["jobs"][0])

            await handle.result()
