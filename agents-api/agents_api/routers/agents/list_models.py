from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header

from ...autogen.openapi_model import ListModelsResponse, ModelInfo
from ...clients.litellm import get_model_list
from ...dependencies.developer_id import get_developer_id
from .router import router


@router.get("/agents/models", tags=["agents"])
async def list_models(
    _x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    x_custom_api_key: str | None = Header(None),
) -> ListModelsResponse:
    """
    List all available models that can be used with agents.

    Returns:
        ListModelsResponse: A list of available models
    """
    models_data = await get_model_list(custom_api_key=x_custom_api_key)
    model_infos = [ModelInfo(id=model["id"]) for model in models_data]

    return ListModelsResponse(models=model_infos)
