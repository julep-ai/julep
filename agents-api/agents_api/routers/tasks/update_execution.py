from typing import Annotated

from fastapi import Depends, HTTPException
from uuid import UUID

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
            wf_handle = temporal_client.get_workflow_handle_for(
                *get_temporal_workflow_data(execution_id=execution_id)
            )
            await wf_handle.cancel()

        case ResumeExecutionRequest():

            token_data = get_paused_execution_token(
                developer_id=x_developer_id, execution_id=execution_id
            )
            act_handle = temporal_client.get_async_activity_handle(
                task_token=str.encode(token_data["task_token"], encoding="latin-1")
            )
            await act_handle.complete(data.input)
            print("Resumed execution successfully")
        case _:
            raise HTTPException(status_code=400, detail="Invalid request data")
