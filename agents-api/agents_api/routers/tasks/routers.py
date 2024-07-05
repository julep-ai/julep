from typing import Annotated
from uuid import uuid4
from fastapi import BackgroundTasks
from agents_api.models.execution.create_execution import create_execution_query
from agents_api.models.execution.get_execution import get_execution_query
from agents_api.models.execution.get_execution_transition import (
    get_execution_transition_query,
)
from agents_api.models.execution.list_executions import list_task_executions_query
from agents_api.models.execution.list_execution_transitions import (
    list_execution_transitions_query,
)
from agents_api.models.execution.update_execution_transition import (
    update_execution_transition_query,
)
from agents_api.models.task.create_task import create_task_query
from agents_api.models.task.get_task import get_task_query
from agents_api.models.task.list_tasks import list_tasks_query
from fastapi import APIRouter, HTTPException, status, Depends
import pandas as pd
from pydantic import BaseModel
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from pycozo.client import QueryException
from agents_api.autogen.openapi_model import (
    CreateTask,
    Task,
    Execution,
    ExecutionTransition,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    UpdateExecutionTransitionRequest,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.clients.temporal import run_task_execution_workflow
from agents_api.common.protocol.tasks import ExecutionInput


class TaskList(BaseModel):
    items: list[Task]


class ExecutionList(BaseModel):
    items: list[Execution]


class ExecutionTransitionList(BaseModel):
    items: list[ExecutionTransition]


router = APIRouter()


@router.get("/agents/{agent_id}/tasks", tags=["tasks"])
async def list_tasks(
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
) -> TaskList:
    query_results = list_tasks_query(
        agent_id=agent_id, developer_id=x_developer_id, limit=limit, offset=offset
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
    request: CreateTask,
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
        tools_available=request.tools_available or [],
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
    "/agents/{agent_id}/tasks/{task_id}/executions",
    status_code=HTTP_201_CREATED,
    tags=["tasks"],
)
async def create_task_execution(
    agent_id: UUID4,
    task_id: UUID4,
    request: ExecutionInput,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    background_task: BackgroundTasks,
) -> ResourceCreatedResponse:
    # TODO: Do thorough validation of the input against task input schema
    resp = create_execution_query(
        agent_id=agent_id,
        task_id=task_id,
        execution_id=uuid4(),
        developer_id=x_developer_id,
        arguments=request.arguments,
    )

    # TODO: how to get previous_inputs?
    # TODO: how to get `start` tuple
    background_task.add_task(
        run_task_execution_workflow,
        execution_input=request,
        job_id=uuid4(),
        start=start,
        previous_inputs=previous_inputs,
    )

    return ResourceCreatedResponse(
        id=resp["execution_id"][0], created_at=resp["created_at"][0]
    )


@router.get("/agents/{agent_id}/tasks/{task_id}/executions", tags=["tasks"])
async def list_task_executions(
    agent_id: UUID4,
    task_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ExecutionList:
    res = list_task_executions_query(agent_id, task_id, x_developer_id)
    return ExecutionList(
        items=[Execution(**row.to_dict()) for _, row in res.iterrows()]
    )


@router.get("/tasks/{task_id}/executions/{execution_id}", tags=["tasks"])
async def get_execution(task_id: UUID4, execution_id: UUID4) -> Execution:
    try:
        res = [
            row.to_dict()
            for _, row in get_execution_query(task_id, execution_id).iterrows()
        ][0]
        return Execution(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )


@router.get("/executions/{execution_id}/transitions/{transition_id}", tags=["tasks"])
async def get_execution_transition(
    execution_id: UUID4,
    transition_id: UUID4,
) -> ExecutionTransition:
    try:
        res = [
            row.to_dict()
            for _, row in get_execution_transition_query(
                execution_id, transition_id
            ).iterrows()
        ][0]
        return ExecutionTransition(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transition not found",
        )


# TODO: Later; for resuming waiting transitions
# TODO: Ask for a task token to resume a waiting transition
@router.put("/executions/{execution_id}/transitions/{transition_id}", tags=["tasks"])
async def update_execution_transition(
    execution_id: UUID4,
    transition_id: UUID4,
    request: UpdateExecutionTransitionRequest,
) -> ResourceUpdatedResponse:
    try:
        resp = update_execution_transition_query(
            execution_id, transition_id, **request.model_dump()
        )

        return ResourceUpdatedResponse(
            id=resp["transition_id"][0],
            updated_at=resp["updated_at"][0][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transition not found",
        )


@router.get("/executions/{execution_id}/transitions", tags=["tasks"])
async def list_execution_transitions(
    execution_id: UUID4,
    limit: int = 100,
    offset: int = 0,
) -> ExecutionTransitionList:
    res = list_execution_transitions_query(
        execution_id=execution_id, limit=limit, offset=offset
    )
    return ExecutionTransitionList(
        items=[ExecutionTransition(**row.to_dict()) for _, row in res.iterrows()]
    )
