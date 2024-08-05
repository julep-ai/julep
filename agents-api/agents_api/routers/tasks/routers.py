import logging
from typing import Annotated, Literal
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from pycozo.client import QueryException
from pydantic import UUID4, BaseModel
from starlette.status import HTTP_201_CREATED

from agents_api.autogen.openapi_model import (
    CreateExecutionRequest,
    CreateTaskRequest,
    Execution,
    ResourceCreatedResponse,
    ResumeExecutionRequest,
    StopExecutionRequest,
    # ResourceUpdatedResponse,
    Task,
    Transition,
    UpdateExecutionRequest,
)
from agents_api.clients.temporal import get_client, run_task_execution_workflow
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.execution.create_execution import (
    create_execution as create_execution_query,
)
from agents_api.models.execution.get_execution import (
    get_execution as get_execution_query,
)
from agents_api.models.execution.get_paused_execution_token import (
    get_paused_execution_token,
)
from agents_api.models.execution.get_temporal_workflow_data import (
    get_temporal_workflow_data,
)

# from agents_api.models.execution.get_execution_transition import (
#     get_execution_transition as get_execution_transition_query,
# )
from agents_api.models.execution.list_execution_transitions import (
    list_execution_transitions as list_execution_transitions_query,
)
from agents_api.models.execution.list_executions import (
    list_executions as list_executions_query,
)
from agents_api.models.execution.list_executions import (
    list_executions as list_task_executions_query,
)
from agents_api.models.execution.prepare_execution_input import prepare_execution_input
from agents_api.models.execution.update_execution import (
    update_execution as update_execution_query,
)

# from agents_api.models.execution.update_execution_transition import (
#     update_execution_transition_query,
# )
from agents_api.models.task.create_task import create_task as create_task_query
from agents_api.models.task.get_task import get_task as get_task_query
from agents_api.models.task.list_tasks import list_tasks as list_tasks_query

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TaskList(BaseModel):
    items: list[Task]


class ExecutionList(BaseModel):
    items: list[Execution]


class ExecutionTransitionList(BaseModel):
    items: list[Transition]


router = APIRouter()


@router.get("/agents/{agent_id}/tasks", tags=["tasks"])
async def list_tasks(
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> TaskList:
    query_results = list_tasks_query(
        agent_id=agent_id,
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
    )

    items = []
    for _, row in query_results.iterrows():
        row_dict = row.to_dict()

        for workflow in row_dict["workflows"]:
            if workflow["name"] == "main":
                row_dict["main"] = workflow["steps"]
                break

        items.append(Task(**row_dict))

    return TaskList(items=items)


@router.post("/agents/{agent_id}/tasks", status_code=HTTP_201_CREATED, tags=["tasks"])
async def create_task(
    request: CreateTaskRequest,
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    task_id = uuid4()

    # TODO: Do thorough validation of the task spec

    workflows = [
        {"name": "main", "steps": [w.model_dump() for w in request.main]},
    ] + [{"name": name, "steps": steps} for name, steps in request.model_extra.items()]

    resp: pd.DataFrame = create_task_query(
        agent_id=agent_id,
        task_id=task_id,
        developer_id=x_developer_id,
        name=request.name,
        description=request.description,
        input_schema=request.input_schema or {},
        tools_available=request.tools or [],
        workflows=workflows,
    )

    return ResourceCreatedResponse(
        id=resp["task_id"][0], created_at=resp["created_at"][0]
    )


@router.get("/agents/{agent_id}/tasks/{task_id}", tags=["tasks"])
async def get_task(
    task_id: UUID4,
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> Task:
    try:
        resp = [
            row.to_dict()
            for _, row in get_task_query(
                agent_id=agent_id, task_id=task_id, developer_id=x_developer_id
            ).iterrows()
        ][0]

        for workflow in resp["workflows"]:
            if workflow["name"] == "main":
                resp["main"] = workflow["steps"]
                break

        return Task(**resp)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    except QueryException as e:
        if e.code == "transact::assertion_failure":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        raise


@router.post(
    "/tasks/{task_id}/executions",
    status_code=HTTP_201_CREATED,
    tags=["tasks"],
)
async def create_task_execution(
    task_id: UUID4,
    data: CreateExecutionRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    try:
        task = [
            row.to_dict()
            for _, row in get_task_query(
                task_id=task_id, developer_id=x_developer_id
            ).iterrows()
        ][0]

        validate(data.input, task["input_schema"])
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request arguments schema",
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    except QueryException as e:
        if e.code == "transact::assertion_failure":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        raise

    execution_id = uuid4()
    execution_input = prepare_execution_input(
        developer_id=x_developer_id,
        task_id=task_id,
        execution_id=execution_id,
    )

    try:
        handle = await run_task_execution_workflow(
            execution_input=execution_input,
            job_id=uuid4(),
        )
    except Exception as e:
        logger.exception(e)

        update_execution_query(
            developer_id=x_developer_id,
            task_id=task_id,
            execution_id=execution_id,
            data=UpdateExecutionRequest(status="failed"),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task creation failed",
        )

    execution = create_execution_query(
        developer_id=x_developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data=data,
        workflow_hande=handle,
    )

    return ResourceCreatedResponse(
        id=execution["execution_id"][0], created_at=execution["created_at"][0]
    )


@router.get("/agents/{agent_id}/tasks/{task_id}/executions", tags=["tasks"])
async def list_task_executions(
    task_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
) -> ExecutionList:
    res = list_task_executions_query(
        task_id=task_id, developer_id=x_developer_id, limit=limit, offse=offset
    )
    return ExecutionList(
        items=[Execution(**row.to_dict()) for _, row in res.iterrows()]
    )


@router.get("/executions/{execution_id}", tags=["executions"])
async def get_execution(task_id: UUID4, execution_id: UUID4) -> Execution:
    try:
        res = [
            row.to_dict()
            for _, row in get_execution_query(execution_id=execution_id).iterrows()
        ][0]
        return Execution(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )


# TODO: write PATCH query
@router.patch("/tasks/{task_id}/executions/{execution_id}", tags=["tasks"])
async def patch_execution(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    task_id: UUID4,
    execution_id: UUID4,
    data: UpdateExecutionRequest,
) -> Execution:
    try:
        res = [
            row.to_dict()
            for _, row in update_execution_query(
                developer_id=x_developer_id,
                task_id=task_id,
                execution_id=execution_id,
                data=data,
            ).iterrows()
        ][0]
        return Execution(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )


@router.put("/tasks/{task_id}/executions/{execution_id}", tags=["tasks"])
async def put_execution(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    execution_id: UUID4,
    data: ResumeExecutionRequest | StopExecutionRequest,
) -> Execution:
    temporal_client = await get_client()
    if isinstance(data, StopExecutionRequest):
        handle = temporal_client.get_workflow_handle_for(
            *get_temporal_workflow_data(execution_id=execution_id)
        )
        await handle.cancel()
    else:
        token_data = get_paused_execution_token(
            developer_id=x_developer_id, execution_id=execution_id
        )
        handle = temporal_client.get_async_activity_handle(token_data["task_token"])
        await handle.complete("finished")


@router.get("/tasks/{task_id}/executions", tags=["tasks"])
async def list_execution(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    task_id: UUID4,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> list[Execution]:
    try:
        res = [
            Execution(**row.to_dict())
            for _, row in list_executions_query(
                developer_id=x_developer_id,
                task_id=task_id,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                direction=direction,
            ).iterrows()
        ]
        return res
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )


# @router.get("/executions/{execution_id}/transitions/{transition_id}", tags=["tasks"])
# async def get_execution_transition(
#     execution_id: UUID4,
#     transition_id: UUID4,
# ) -> Transition:
#     try:
#         res = [
#             row.to_dict()
#             for _, row in get_execution_transition_query(
#                 execution_id, transition_id
#             ).iterrows()
#         ][0]
#         return Transition(**res)
#     except (IndexError, KeyError):
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Transition not found",
#         )


# TODO: Later; for resuming waiting transitions
# TODO: Ask for a task token to resume a waiting transition
# @router.put("/executions/{execution_id}/transitions/{transition_id}", tags=["tasks"])
# async def update_execution_transition(
#     execution_id: UUID4,
#     transition_id: UUID4,
#     request: Transition,
# ) -> ResourceUpdatedResponse:
#     try:
#         resp = update_execution_transition_query(
#             execution_id, transition_id, **request.model_dump()
#         )

#         return ResourceUpdatedResponse(
#             id=resp["transition_id"][0],
#             updated_at=resp["updated_at"][0][0],
#         )
#     except (IndexError, KeyError):
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Transition not found",
#         )


@router.get("/executions/{execution_id}/transitions", tags=["executions"])
async def list_execution_transitions(
    execution_id: UUID4,
    limit: int = 100,
    offset: int = 0,
) -> ExecutionTransitionList:
    res = list_execution_transitions_query(
        execution_id=execution_id, limit=limit, offset=offset
    )
    return ExecutionTransitionList(
        items=[Transition(**row.to_dict()) for _, row in res.iterrows()]
    )
