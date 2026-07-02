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
