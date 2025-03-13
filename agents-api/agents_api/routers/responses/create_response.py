from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import BaseModel

from ...dependencies.developer_id import get_developer_id
from .router import router


# FIXME: Remove these placeholder models once models are generated from typespec
class CreateResponseRequest(BaseModel):
    response: str


class CreateResponseResponse(BaseModel):
    id: str


@router.post("/responses/", tags=["responses"])
async def create_response(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    response: CreateResponseRequest,
) -> CreateResponseResponse:
    return {
        "id": "123",
    }
