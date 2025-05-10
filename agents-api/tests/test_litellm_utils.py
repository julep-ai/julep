from unittest.mock import patch

from agents_api.clients.litellm import acompletion
from agents_api.common.utils.llm_providers import get_api_key_env_var_name
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
