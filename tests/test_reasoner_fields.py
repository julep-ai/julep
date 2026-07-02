from composable_agents.dotctx import Reasoner
from composable_agents.execution.llm import _with_model


def test_fields_default() -> None:
    r = Reasoner(name="t", model="openai:gpt-4o")
    assert r.reasoning_effort is None
    assert r.output_retries == 0


def test_with_model_carries_new_fields() -> None:
    r = Reasoner(name="t", model="openai:gpt-4o",
                 reasoning_effort="high", output_retries=2)
    moved = _with_model(r, "anthropic:claude-sonnet-4-6")
    assert moved.model == "anthropic:claude-sonnet-4-6"
    assert moved.reasoning_effort == "high"
    assert moved.output_retries == 2


def test_reasoner_identity_stable_on_defaults_and_moves_on_values() -> None:
    from composable_agents.deploy import _reasoner_identity
    from composable_agents.dotctx import DEFAULT_REGISTRY

    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="ident-a", model="m"))
    DEFAULT_REGISTRY.register_reasoner(
        Reasoner(name="ident-b", model="m", reasoning_effort="low", output_retries=1))
    a, b = _reasoner_identity("ident-a"), _reasoner_identity("ident-b")
    assert "reasoningEffort" not in a and "outputRetries" not in a  # defaults: hash-stable
    assert b["reasoningEffort"] == "low" and b["outputRetries"] == 1
