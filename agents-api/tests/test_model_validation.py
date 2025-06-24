from unittest.mock import patch

import pytest
from agents_api.routers.utils.model_validation import validate_model
from fastapi import HTTPException

SAMPLE_MODELS = [
    {"id": "gpt-4o-mini"},
    {"id": "gpt-4"},
    {"id": "claude-3-opus"},
]


async def test_validate_model_succeeds_when_model_is_available_in_model_list():
    # Use async context manager for patching
    with patch(
        "agents_api.routers.utils.model_validation.get_model_list"
    ) as mock_get_models:
        mock_get_models.return_value = SAMPLE_MODELS
        await validate_model("gpt-4o-mini")
        mock_get_models.assert_called_once()


async def test_validate_model_fails_when_model_is_unavailable_in_model_list():
    with patch(
        "agents_api.routers.utils.model_validation.get_model_list"
    ) as mock_get_models:
        mock_get_models.return_value = SAMPLE_MODELS
        with pytest.raises(HTTPException) as exc:
            await validate_model("non-existent-model")

        assert exc.value.status_code == 400
        assert "Model non-existent-model not available" in exc.value.detail
        mock_get_models.assert_called_once()


async def test_validate_model_fails_when_model_is_none():
    with patch(
        "agents_api.routers.utils.model_validation.get_model_list"
    ) as mock_get_models:
        mock_get_models.return_value = SAMPLE_MODELS
        with pytest.raises(HTTPException) as exc:
            await validate_model(None)

        assert exc.value.status_code == 400
        assert "Model None not available" in exc.value.detail
