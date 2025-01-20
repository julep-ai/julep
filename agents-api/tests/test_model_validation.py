from unittest.mock import patch

from agents_api.routers.utils.model_validation import validate_model
from fastapi import HTTPException
from ward import raises, test

from tests.fixtures import SAMPLE_MODELS


@test("validate_model: succeeds when model is available")
async def _():
    # Use async context manager for patching
    with patch("agents_api.routers.utils.model_validation.get_model_list") as mock_get_models:
        mock_get_models.return_value = SAMPLE_MODELS
        await validate_model("gpt-4o-mini")
        mock_get_models.assert_called_once()


@test("validate_model: fails when model is unavailable")
async def _():
    with patch("agents_api.routers.utils.model_validation.get_model_list") as mock_get_models:
        mock_get_models.return_value = SAMPLE_MODELS
        with raises(HTTPException) as exc:
            await validate_model("non-existent-model")

        assert exc.raised.status_code == 400
        assert "Model non-existent-model not available" in exc.raised.detail
        mock_get_models.assert_called_once()
