"""Shared helpers for validating model identifiers against LiteLLM."""

from __future__ import annotations

from typing import Sequence

from ...clients.litellm import get_model_list


class ModelNotAvailableError(ValueError):
    """Raised when a requested model identifier is not present in the catalog."""

    def __init__(self, model_name: str | None, available_models: Sequence[str]) -> None:
        self.requested_model = model_name
        self.available_models = list(available_models)
        message = (
            "Model {model} not available. Available models: {available}".format(
                model=model_name,
                available=self.available_models,
            )
        )
        super().__init__(message)


async def ensure_model_available(
    model_name: str | None,
    *,
    custom_api_key: str | None = None,
) -> Sequence[str]:
    """Ensure ``model_name`` exists in LiteLLM's configured catalog."""

    models = await get_model_list(custom_api_key=custom_api_key)
    available_models = [model["id"] for model in models]

    if model_name not in available_models:
        raise ModelNotAvailableError(model_name, available_models)

    return available_models
