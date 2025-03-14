from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from ...autogen.openapi_model import Response
from ...dependencies.developer_id import get_developer_id

router = APIRouter()


@router.get("/responses/{id}", tags=["responses"])
async def get_response(
    id: str,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> Response:
    # TODO: Implement the logic to get a response by id
    pass
