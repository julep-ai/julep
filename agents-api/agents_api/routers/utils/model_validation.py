# AIDEV-NOTE: Validates model names against LiteLLM and raises HTTPException for invalid names.
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from ...clients.litellm import get_model_list


async def validate_model(model_name: str | None) -> None:
    """
    Validates if a given model name is available in LiteLLM.
    Raises HTTPException if model is not available.
    """
    models = await get_model_list()
    available_models = [model["id"] for model in models]

    if model_name not in available_models:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Model {model_name} not available. Available models: {available_models}",
        )
