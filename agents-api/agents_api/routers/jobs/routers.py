from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from temporalio.client import WorkflowExecutionStatus

from agents_api.autogen.openapi_model import JobStatus
from agents_api.clients.temporal import get_client

router: APIRouter = APIRouter()


def map_job_status(
    status: WorkflowExecutionStatus,
) -> Literal[
    "pending",
    "in_progress",
    "retrying",
    "succeeded",
    "aborted",
    "failed",
    "unknown",
]:
    match status:
        case WorkflowExecutionStatus.RUNNING:
            return "in_progress"
        case WorkflowExecutionStatus.COMPLETED:
            return "succeeded"
        case WorkflowExecutionStatus.FAILED:
            return "failed"
        case WorkflowExecutionStatus.CANCELED:
            return "aborted"
        case WorkflowExecutionStatus.TERMINATED:
            return "aborted"
        case WorkflowExecutionStatus.CONTINUED_AS_NEW:
            return "in_progress"
        case WorkflowExecutionStatus.TIMED_OUT:
            return "failed"
        case _:
            return "unknown"


@router.get("/jobs/{job_id}", tags=["jobs"])
async def get_job_status(job_id: UUID) -> JobStatus:
    client = await get_client()
    handle = client.get_workflow_handle(
        workflow_id=str(job_id),
    )
    job_description = await handle.describe()
    state = map_job_status(job_description.status)

    return JobStatus(
        name=job_description.workflow_type,
        reason=f"Execution status: {state}",
        created_at=job_description.start_time,
        updated_at=job_description.execution_time,
        id=job_id,
        has_progress=False,
        progress=0,
        state=state,
    )
