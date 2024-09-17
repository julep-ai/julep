from typing import Annotated

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import Doc
from ...dependencies.developer_id import get_developer_id
from ...models.docs.get_doc import get_doc as get_doc_query
from .router import router


@router.get("/docs/{doc_id}", tags=["docs"])
async def get_doc(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    doc_id: UUID4,
) -> Doc:
    return get_doc_query(developer_id=x_developer_id, doc_id=doc_id)
