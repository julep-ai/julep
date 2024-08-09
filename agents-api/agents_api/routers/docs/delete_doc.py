from typing import Annotated

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_202_ACCEPTED

from ...autogen.openapi_model import ResourceDeletedResponse
from ...dependencies.developer_id import get_developer_id
from ...models.docs.delete_doc import delete_doc as delete_doc_query
from .router import router


@router.delete("/docs/{doc_id}", status_code=HTTP_202_ACCEPTED, tags=["docs"])
async def delete_doc(
    doc_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    return delete_doc_query(developer_id=x_developer_id, doc_id=doc_id)
