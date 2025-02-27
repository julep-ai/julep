from unittest.mock import patch

from agents_api.clients.litellm import acompletion
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
