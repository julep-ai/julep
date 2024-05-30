from typing import Annotated, Literal
from uuid import uuid4
from agents_api.models.execution.create_execution import create_execution_query
from agents_api.models.execution.get_execution_status import get_execution_status_query
from agents_api.models.execution.get_execution_transition import (
    get_execution_transition_query,
)
from agents_api.models.task.create_task import create_task_query
from agents_api.models.task.get_task import get_task_query
from agents_api.models.task.list_tasks import list_tasks_query
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
import pandas as pd
from pydantic import BaseModel
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED

from pycozo.client import QueryException
from agents_api.autogen.openapi_model import (
    CreateTask,
    CreateExecution,
    Task,
    Execution,
    ExecutionTransition,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
)
from agents_api.dependencies.developer_id import get_developer_id


class TaskList(BaseModel):
    items: list[Task]


router = APIRouter()


@router.get("/tasks", tags=["tasks"])
async def list_sessions(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> TaskList:
    query_results = list_tasks_query(x_developer_id)
    return TaskList(
        items=[Task(**row.to_dict()) for _, row in query_results.iterrows()]
    )


@router.get("/tasks/{task_id}", tags=["tasks"])
async def get_task(
    task_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> Task:
    query_results = get_task_query(x_developer_id, task_id)
    pass


@router.post("/tasks", status_code=HTTP_201_CREATED, tags=["tasks"])
async def create_task(
    request: CreateTask,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    task_id = uuid4()
    resp: pd.DataFrame = create_task_query(
        task_id=task_id,
        developer_id=x_developer_id,
    )
    return ResourceCreatedResponse(
        id=resp["task_id"][0], created_at=resp["created_at"][0]
    )


@router.post("/tasks/{task_id}/executions", status_code=HTTP_201_CREATED, tags=["tasks"])
async def create_task_execution(
    task_id: UUID4,
    request: CreateExecution,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    resp = create_execution_query()
    return ResourceCreatedResponse(
        id=resp["execution_id"][0], created_at=resp["created_at"][0]
    )


@router.get("/tasks/{task_id}/executions", tags=["tasks"])
async def get_task_execution_status(
    task_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> Literal["queued", "starting", "running", "waiting_for_input", "success", "failed"]:

    resp = get_execution_status_query(task_id, x_developer_id)
    pass


@router.get("/executions/{execution_id}/transitions/{transition_id}")
async def get_execution_transition(
    execution_id: UUID4,
    transition_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ExecutionTransition:
    resp = get_execution_transition_query(execution_id, transition_id, x_developer_id)

    pass
