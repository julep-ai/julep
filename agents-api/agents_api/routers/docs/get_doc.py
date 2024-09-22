from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import Doc
from ...dependencies.developer_id import get_developer_id
from ...models.docs.get_doc import get_doc as get_doc_query
from .router import router


@router.get("/docs/{doc_id}", tags=["docs"])
async def get_doc(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    doc_id: UUID,
) -> Doc:
    return get_doc_query(developer_id=x_developer_id, doc_id=doc_id)
