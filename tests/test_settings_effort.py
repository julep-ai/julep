import pytest

from composable_agents.dotctx import reasoner_from_settings


def test_suffix_extracted_and_model_canonicalized() -> None:
    r = reasoner_from_settings(
        {"model": "openai/gpt-5.4-nano@medium"}, name="t1")
    assert r.model == "openai:gpt-5.4-nano"
    assert r.reasoning_effort == "medium"


def test_explicit_key_wins_over_suffix() -> None:
    r = reasoner_from_settings(
        {"model": "openai/gpt-5.4-nano@medium", "reasoning_effort": "high"},
        name="t2")
    assert r.reasoning_effort == "high"


def test_invalid_effort_key_raises() -> None:
    with pytest.raises(ValueError, match="reasoning_effort"):
        reasoner_from_settings(
            {"model": "openai:gpt-4o", "reasoning_effort": "auto"}, name="t3")


def test_output_retries_mapped() -> None:
    r = reasoner_from_settings(
        {"model": "openai:gpt-4o", "output_retries": 2}, name="t4")
    assert r.output_retries == 2


def test_require_tool_call_parsed() -> None:
    r = reasoner_from_settings(
        {"model": "openai:gpt-4o", "require_tool_call": True}, name="t5")
    assert r.require_tool_call is True


def test_require_tool_call_and_response_format_default_unset() -> None:
    r = reasoner_from_settings({"model": "openai:gpt-4o"}, name="t6")
    assert r.require_tool_call is False
    assert r.response_format is None


def test_require_tool_call_non_bool_errors() -> None:
    with pytest.raises(ValueError, match="require_tool_call"):
        reasoner_from_settings(
            {"model": "openai:gpt-4o", "require_tool_call": "yes"}, name="t7")


def test_response_format_json_object_parsed() -> None:
    r = reasoner_from_settings(
        {"model": "openai:gpt-4o", "response_format": {"type": "json_object"}},
        name="t8")
    assert r.response_format == "json_object"


@pytest.mark.parametrize(
    "bad", ["json", {"type": "json_schema"}, ["json_object"], {"type": "json_object", "extra": 1}]
)
def test_response_format_bad_shape_errors(bad: object) -> None:
    with pytest.raises(ValueError, match="json_object"):
        reasoner_from_settings(
            {"model": "openai:gpt-4o", "response_format": bad}, name="t9")


def test_numeric_string_settings_coerce() -> None:
    # Yglu/env values arrive as strings: $env.get("...") returns the env
    # var verbatim (record/execute.ctx's max_rounds is the real case).
    r = reasoner_from_settings(
        {"model": "openai:gpt-4o", "max_rounds": "12", "max_tokens": "120",
         "output_retries": "1", "temperature": "0.3"}, name="t10")
    assert r.max_rounds == 12
    assert r.max_tokens == 120
    assert r.output_retries == 1
    assert r.temperature == 0.3


def test_explicit_zero_settings_do_not_fall_through_to_camel_case() -> None:
    r = reasoner_from_settings(
        {
            "model": "openai:gpt-4o",
            "max_rounds": 0,
            "maxRounds": 12,
            "max_tokens": 0,
            "maxTokens": 120,
            "output_retries": 0,
            "outputRetries": 2,
            "temperature": 0,
        },
        name="t10.zero",
    )
    assert r.max_rounds == 0
    assert r.max_tokens == 0
    assert r.output_retries == 0
    assert r.temperature == 0.0


@pytest.mark.parametrize(
    "key, value",
    [("max_rounds", "many"), ("max_tokens", "12.5"),
     ("output_retries", "once"), ("temperature", "warm")],
)
def test_non_numeric_string_settings_error(key: str, value: str) -> None:
    with pytest.raises(ValueError, match=key):
        reasoner_from_settings({"model": "openai:gpt-4o", key: value}, name="t11")
