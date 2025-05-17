from unittest.mock import patch

from agents_api.routers.utils.model_validation import validate_model
from fastapi import HTTPException
import pytest

from tests.fixtures import SAMPLE_MODELS


@pytest.mark.asyncio
async def test_validate_model_succeeds_when_model_is_available_in_model_list():
    """validate_model: succeeds when model is available in model list"""
    # Use async context manager for patching
    with patch("agents_api.routers.utils.model_validation.get_model_list") as mock_get_models:
        mock_get_models.return_value = SAMPLE_MODELS
        await validate_model("gpt-4o-mini")
        mock_get_models.assert_called_once()


@pytest.mark.asyncio
async def test_validate_model_fails_when_model_is_unavailable_in_model_list():
    """validate_model: fails when model is unavailable in model list"""
    with patch("agents_api.routers.utils.model_validation.get_model_list") as mock_get_models:
        mock_get_models.return_value = SAMPLE_MODELS
        with pytest.raises(HTTPException) as exc:
            await validate_model("non-existent-model")

        assert exc.raised.status_code == 400
        assert "Model non-existent-model not available" in exc.raised.detail
        mock_get_models.assert_called_once()


@pytest.mark.asyncio
async def test_validate_model_fails_when_model_is_none():
    """validate_model: fails when model is None"""
    with patch("agents_api.routers.utils.model_validation.get_model_list") as mock_get_models:
        mock_get_models.return_value = SAMPLE_MODELS
        with pytest.raises(HTTPException) as exc:
            await validate_model(None)

        assert exc.raised.status_code == 400
        assert "Model None not available" in exc.raised.detail
