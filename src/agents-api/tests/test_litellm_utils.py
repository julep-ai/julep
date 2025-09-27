from unittest.mock import AsyncMock, patch

from agents_api.clients.litellm import acompletion
from agents_api.common.utils.llm_providers import (
    get_api_key_env_var_name,
    get_litellm_model_name,
)
from litellm.types.utils import ModelResponse
from ward import test


@test("litellm_utils: acompletion - no tools")
async def _():
    with patch("agents_api.clients.litellm._acompletion") as mock_acompletion:
        mock_acompletion.return_value = ModelResponse(
            id="test-id",
            choices=[{"message": {"content": "test"}}],
            model="gpt-4",
            usage={"total_tokens": 10},
        )

        messages = [{"role": "user", "content": "test", "tool_calls": []}]

        await acompletion(model="gpt-4", messages=messages)

        # Check that tool_calls was removed from the message
        mock_acompletion.assert_called_once()
        called_messages = mock_acompletion.call_args[1]["messages"]
        assert "tool_calls" not in called_messages[0]


@test("litellm_utils: get_api_key_env_var_name")
async def _():
    with patch("agents_api.common.utils.llm_providers.get_config") as mock_get_config:
        mock_get_config.return_value = {
            "model_list": [
                {
                    "model_name": "gpt-4",
                    "litellm_params": {"api_key": "os.environ/OPENAI_API_KEY"},
                }
            ]
        }

        result = get_api_key_env_var_name("gpt-4")
        assert result == "OPENAI_API_KEY"


@test("litellm_utils: get_litellm_model_name - known models")
async def _():
    with patch("agents_api.common.utils.llm_providers.get_config") as mock_get_config:
        mock_get_config.return_value = {
            "model_list": [
                {
                    "model_name": "gpt-4o",
                    "litellm_params": {"model": "openai/gpt-4o"},
                },
                {
                    "model_name": "gemini-1.5-pro",
                    "litellm_params": {"model": "gemini/gemini-1.5-pro"},
                },
                {
                    "model_name": "claude-3.5-sonnet",
                    "litellm_params": {"model": "claude-3-5-sonnet-20241022"},
                },
            ]
        }

        assert get_litellm_model_name("gpt-4o") == "openai/gpt-4o"
        assert get_litellm_model_name("gemini-1.5-pro") == "gemini/gemini-1.5-pro"
        assert get_litellm_model_name("claude-3.5-sonnet") == "claude-3-5-sonnet-20241022"


@test("litellm_utils: get_litellm_model_name - unknown model")
async def _():
    with patch("agents_api.common.utils.llm_providers.get_config") as mock_get_config:
        mock_get_config.return_value = {
            "model_list": [
                {
                    "model_name": "gpt-4o",
                    "litellm_params": {"model": "openai/gpt-4o"},
                }
            ]
        }

        # Unknown model should return unchanged
        assert get_litellm_model_name("unknown-model") == "unknown-model"


@test("litellm_utils: get_litellm_model_name - empty config")
async def _():
    with patch("agents_api.common.utils.llm_providers.get_config") as mock_get_config:
        mock_get_config.return_value = {}

        # With empty config, any model returns unchanged
        assert get_litellm_model_name("any-model") == "any-model"


@test("litellm_utils: acompletion - custom_api_key takes precedence over secret")
async def _():
    with (
        patch("agents_api.clients.litellm._acompletion") as mock_acompletion,
        patch("agents_api.clients.litellm.get_secret_by_name") as mock_get_secret,
        patch("agents_api.clients.litellm.get_litellm_model_name") as mock_get_model_name,
    ):
        # Setup mocks
        mock_acompletion.return_value = ModelResponse(
            id="test-id",
            choices=[{"message": {"content": "test"}}],
            model="gpt-4o",
            usage={"total_tokens": 10},
        )
        mock_get_secret.return_value = AsyncMock(value="secret-api-key")
        mock_get_model_name.return_value = "openai/gpt-4o"

        messages = [{"role": "user", "content": "test"}]

        # Call with both custom_api_key and user (which would trigger secret lookup)
        await acompletion(
            model="gpt-4o",
            messages=messages,
            custom_api_key="custom-api-key",
            user="test-user-id",
        )

        # Verify custom_api_key is used, not the secret
        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args[1]
        assert call_kwargs["api_key"] == "custom-api-key"
        assert call_kwargs["base_url"] is None
        assert call_kwargs["model"] == "openai/gpt-4o"


@test("litellm_utils: acompletion - secret used when no custom_api_key")
async def _():
    with (
        patch("agents_api.clients.litellm._acompletion") as mock_acompletion,
        patch("agents_api.clients.litellm.get_secret_by_name") as mock_get_secret,
        patch("agents_api.clients.litellm.get_litellm_model_name") as mock_get_model_name,
        patch("agents_api.clients.litellm.get_api_key_env_var_name") as mock_get_env_var,
    ):
        # Setup mocks
        mock_acompletion.return_value = ModelResponse(
            id="test-id",
            choices=[{"message": {"content": "test"}}],
            model="gpt-4o",
            usage={"total_tokens": 10},
        )
        secret_mock = AsyncMock()
        secret_mock.value = "secret-api-key"
        mock_get_secret.return_value = secret_mock
        mock_get_model_name.return_value = "openai/gpt-4o"
        mock_get_env_var.return_value = "OPENAI_API_KEY"

        messages = [{"role": "user", "content": "test"}]

        # Call without custom_api_key but with user
        await acompletion(
            model="gpt-4o", messages=messages, user="550e8400-e29b-41d4-a716-446655440000"
        )

        # Verify secret's API key is used
        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args[1]
        assert call_kwargs["api_key"] == "secret-api-key"
        assert call_kwargs["base_url"] is None
        assert call_kwargs["model"] == "openai/gpt-4o"


@test("litellm_utils: acompletion - proxy used when no custom_api_key or secret")
async def _():
    with (
        patch("agents_api.clients.litellm._acompletion") as mock_acompletion,
        patch("agents_api.clients.litellm.get_secret_by_name") as mock_get_secret,
        patch("agents_api.clients.litellm.litellm_master_key", "master-key"),
        patch("agents_api.clients.litellm.litellm_url", "http://litellm-proxy"),
    ):
        # Setup mocks
        mock_acompletion.return_value = ModelResponse(
            id="test-id",
            choices=[{"message": {"content": "test"}}],
            model="openai/gpt-4o",
            usage={"total_tokens": 10},
        )
        # No secret found
        mock_get_secret.side_effect = Exception("Secret not found")

        messages = [{"role": "user", "content": "test"}]

        # Call without custom_api_key
        await acompletion(model="gpt-4o", messages=messages)

        # Verify proxy configuration is used
        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args[1]
        assert call_kwargs["api_key"] == "master-key"
        assert call_kwargs["base_url"] == "http://litellm-proxy"
        assert call_kwargs["model"] == "openai/gpt-4o"  # Note the openai/ prefix
