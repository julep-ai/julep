from types import SimpleNamespace

from composable_agents.execution.anthropic_batch import AnthropicBatchProvider
from composable_agents.execution.openai_batch import OpenAIBatchProvider


def test_openai_batch_parse_surfaces_usage():
    body = {
        "choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 9, "completion_tokens": 4, "total_tokens": 13},
    }
    prov = OpenAIBatchProvider.__new__(OpenAIBatchProvider)  # avoid real client init
    out = prov.parse_with_usage(body, reasoner=SimpleNamespace(reply_schema=None))
    assert out.input_tokens == 9
    assert out.output_tokens == 4


def test_anthropic_batch_parse_surfaces_usage():
    message = SimpleNamespace(
        usage=SimpleNamespace(input_tokens=9, output_tokens=4),
        content=[SimpleNamespace(type="text", text="ok")],
    )
    prov = AnthropicBatchProvider.__new__(AnthropicBatchProvider)  # avoid real client init
    out = prov.parse_with_usage(message, reasoner=SimpleNamespace(reply_schema=None))
    assert out.input_tokens == 9
    assert out.output_tokens == 4
