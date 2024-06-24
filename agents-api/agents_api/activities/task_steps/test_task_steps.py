# Tests for agent queries
from uuid import uuid4

from temporalio.client import Client
from temporalio.worker import Worker
from ward import test

from ...common.protocol.tasks import ExecutionInput
from ...workflows.task_execution import TaskExecutionWorkflow
from .prompt_step import prompt_step_mocked


@test("task step: prompt step")
async def _():
    client: Client = await Client.connect("localhost:7233")
    task_queue_name = str(uuid4())

    # Provide the mocked Activity implementation to the Worker
    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[TaskExecutionWorkflow],
        activities=[prompt_step_mocked],
    ):
        test_input = ExecutionInput.mocked()

        result = await client.execute_workflow(
            TaskExecutionWorkflow.run,
            test_input,
            id=str(uuid4()),
            task_queue=task_queue_name,
        )

        assert result is not None
