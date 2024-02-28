from fastapi import APIRouter
from pydantic import UUID4

from agents_api.autogen.openapi_model import (
    JobStatus,
)


router = APIRouter()


@router.get("/jobs/{job_id}", tags=["jobs"])
async def get_job_status(job_id: UUID4) -> JobStatus:
    # TODO: implement this endpoint
    #
    # - Use temporal_client.get_workflow_handle(workflow_id=job_id) to get the workflow handle
    # - User workflow_handle.describe().status to get the status of the workflow
    # - You can use the `JobStatus` model to return a response

    # https://docs.temporal.io/dev-guide/python/foundations#get-workflow-results
    # https://python.temporal.io/temporalio.client.WorkflowHandle.html#describe
    # https://python.temporal.io/temporalio.client.WorkflowExecutionDescription.html
    raise NotImplementedError
