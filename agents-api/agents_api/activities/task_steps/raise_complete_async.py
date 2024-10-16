import base64
from typing import Any

from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import CreateTransitionRequest
from ...common.protocol.tasks import StepContext
from ...common.storage_handler import auto_blob_store
from .transition_step import original_transition_step


@activity.defn
@auto_blob_store
@beartype
async def raise_complete_async(context: StepContext, output: Any) -> None:
    activity_info = activity.info()

    captured_token = base64.b64encode(activity_info.task_token).decode("ascii")
    activity_id = activity_info.activity_id
    workflow_run_id = activity_info.workflow_run_id
    workflow_id = activity_info.workflow_id

    transition_info = CreateTransitionRequest(
        current=context.cursor,
        type="wait",
        next=None,
        output=output,
        task_token=captured_token,
        metadata={
            "x-activity-id": activity_id,
            "x-run-id": workflow_run_id,
            "x-workflow-id": workflow_id,
        },
    )

    await original_transition_step(context, transition_info)

    activity.raise_complete_async()
