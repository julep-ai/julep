from fastapi import APIRouter
from pydantic import UUID4
from temporalio.client import WorkflowExecutionStatus

from agents_api.autogen.openapi_model import JobStatus, State
from agents_api.clients.temporal import get_client

router = APIRouter()


def map_job_status(status: WorkflowExecutionStatus) -> State:
    match status:
        case WorkflowExecutionStatus.RUNNING:
            return State.in_progress
        case WorkflowExecutionStatus.COMPLETED:
            return State.succeeded
        case WorkflowExecutionStatus.FAILED:
            return State.failed
        case WorkflowExecutionStatus.CANCELED:
            return State.aborted
        case WorkflowExecutionStatus.TERMINATED:
            return State.aborted
        case WorkflowExecutionStatus.CONTINUED_AS_NEW:
            return State.in_progress
        case WorkflowExecutionStatus.TIMED_OUT:
            return State.failed
        case _:
            return State.unknown


@router.get("/jobs/{job_id}", tags=["jobs"])
async def get_job_status(job_id: UUID4) -> JobStatus:
    client = await get_client()
    handle = client.get_workflow_handle(
        workflow_id=str(job_id),
    )
    job_description = await handle.describe()
    state = map_job_status(job_description.status)

    return JobStatus(
        name=handle.id,
        reason=f"Execution status: {state.name}",
        created_at=job_description.start_time,
        updated_at=job_description.execution_time,
        id=job_id,
        has_progress=False,
        progress=0,
        state=state,
    )
