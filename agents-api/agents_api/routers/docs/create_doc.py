from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED
from temporalio.client import Client as TemporalClient

from ...autogen.openapi_model import CreateDocRequest, ResourceCreatedResponse
from ...clients import temporal
from ...dependencies.developer_id import get_developer_id
from ...models.docs.create_doc import create_doc as create_doc_query
from .router import router


async def run_embed_docs_task(
    doc_id: UUID,
    title: str,
    content: list[str],
    job_id: UUID,
    client: TemporalClient | None = None,
):
    client = client or (await temporal.get_client())

    await client.execute_workflow(
        "EmbedDocsWorkflow",
        args=[str(doc_id), title, content],
        task_queue="memory-task-queue",
        id=str(job_id),
    )


@router.post("/users/{user_id}/docs", status_code=HTTP_201_CREATED, tags=["docs"])
async def create_user_doc(
    user_id: UUID4,
    data: CreateDocRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    doc = create_doc_query(
        developer_id=x_developer_id,
        owner_type="user",
        owner_id=user_id,
        data=data,
    )

    embed_job_id = uuid4()

    await run_embed_docs_task(
        doc_id=doc.id,
        title=doc.title,
        content=doc.content,
        job_id=embed_job_id,
    )

    return ResourceCreatedResponse(
        id=doc.id, created_at=doc.created_at, jobs=[embed_job_id]
    )


@router.post("/agents/{agent_id}/docs", status_code=HTTP_201_CREATED, tags=["docs"])
async def create_agent_doc(
    agent_id: UUID4,
    data: CreateDocRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    doc = create_doc_query(
        developer_id=x_developer_id,
        owner_type="agent",
        owner_id=agent_id,
        data=data,
    )

    embed_job_id = uuid4()

    await run_embed_docs_task(
        doc_id=doc.id,
        title=doc.title,
        content=doc.content,
        job_id=embed_job_id,
    )

    return ResourceCreatedResponse(
        id=doc.id, created_at=doc.created_at, jobs=[embed_job_id]
    )
