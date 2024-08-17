# Tests for task queries

from ward import test

from agents_api.autogen.openapi_model import CreateExecutionRequest
from agents_api.routers.tasks.create_task_execution import start_execution

from .fixtures import cozo_client, test_developer_id, test_task
from .utils import patch_testing_temporal


@test("workflow: create task execution")
async def _(client=cozo_client, developer_id=test_developer_id, task=test_task):
    data = CreateExecutionRequest(input={"test": "input"})

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
