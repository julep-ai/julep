import base64
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from agents_api.autogen.openapi_model import (
    ResumeExecutionRequest,
    StopExecutionRequest,
)
from agents_api.clients.temporal import get_client
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.execution.get_paused_execution_token import (
    get_paused_execution_token,
)
from agents_api.models.execution.get_temporal_workflow_data import (
    get_temporal_workflow_data,
)

from .router import router


@router.put("/executions/{execution_id}", tags=["executions"])
async def update_execution(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    execution_id: UUID,
    data: ResumeExecutionRequest | StopExecutionRequest,
):
    temporal_client = await get_client()

    match data:
        case StopExecutionRequest():
            try:
                wf_handle = temporal_client.get_workflow_handle_for(
                    *get_temporal_workflow_data(execution_id=execution_id)
                )
                await wf_handle.cancel()
            except Exception as e:
                raise HTTPException(status_code=500, detail="Failed to stop execution")

        case ResumeExecutionRequest():
            token_data = get_paused_execution_token(
                developer_id=x_developer_id, execution_id=execution_id
            )
            activity_id = token_data["metadata"].get("x-activity-id", None)
            run_id = token_data["metadata"].get("x-run-id", None)
            workflow_id = token_data["metadata"].get("x-workflow-id", None)
            if activity_id is None or run_id is None or workflow_id is None:
                act_handle = temporal_client.get_async_activity_handle(
                    task_token=base64.b64decode(token_data["task_token"].encode('ascii')),
                )

            else:
                act_handle = temporal_client.get_async_activity_handle(
                    activity_id=activity_id,
                    workflow_id=workflow_id,
                    run_id=run_id,
                )
            try:
                await act_handle.complete(data.input)
            except Exception as e:
                raise HTTPException(status_code=500, detail="Failed to resume execution")
        case _:
            raise HTTPException(status_code=400, detail="Invalid request data")
