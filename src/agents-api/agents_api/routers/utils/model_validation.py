# AIDEV-NOTE: Validates model names against LiteLLM and raises HTTPException for invalid names.
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from ...common.utils.model_validation import (
    ModelNotAvailableError,
    ensure_model_available,
)


async def validate_model(model_name: str | None) -> None:
    """Validate that ``model_name`` exists in LiteLLM's catalog."""

    try:
        await ensure_model_available(model_name)
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
