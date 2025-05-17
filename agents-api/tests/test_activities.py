from agents_api.clients import temporal
from agents_api.env import temporal_task_queue
from agents_api.workflows.demo import DemoWorkflow
from agents_api.workflows.task_execution.helpers import DEFAULT_RETRY_POLICY
from uuid_extensions import uuid7
import pytest

from .utils import patch_testing_temporal


@pytest.mark.asyncio
async def test_activity_call_demo_workflow_via_temporal_client():
    """activity: call demo workflow via temporal client"""
    async with patch_testing_temporal() as (_, mock_get_client):
        client = await temporal.get_client()

        result = await client.execute_workflow(
            DemoWorkflow.run,
            args=[1, 2],
            id=str(uuid7()),
            task_queue=temporal_task_queue,
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        assert result == 3
        mock_get_client.assert_called_once()
