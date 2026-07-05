import pytest

from julep.model_slugs import ModelSlug, normalize_model_slug


@pytest.mark.parametrize(
    "raw,model,effort",
    [
        ("openai/gpt-5.4-nano@medium", "openai:gpt-5.4-nano", "medium"),
        ("anthropic:claude-sonnet-4-6@high", "anthropic:claude-sonnet-4-6", "high"),
        ("openrouter:inception/mercury-2", "openrouter:inception/mercury-2", None),
        ("openrouter/inception/mercury-2@low", "openrouter:inception/mercury-2", "low"),
        ("openai/gpt-5.4-mini@none", "openai:gpt-5.4-mini", "none"),
        ("claude-opus-4-8", "claude-opus-4-8", None),          # bare slug untouched
        ("vertex_ai/gemini-2.5-pro", "vertexai:gemini-2.5-pro", None),
        ("google/gemini-2.5-flash", "gemini:gemini-2.5-flash", None),
        ("gemini/gemini-2.5-flash@xhigh", "gemini:gemini-2.5-flash", "xhigh"),
        ("openai:gpt-4o", "openai:gpt-4o", None),               # canonical passes through
        ("model@vintage", "model@vintage", None),               # unknown suffix is part of the name
        ("  openai/gpt-4o@LOW  ", "openai:gpt-4o", "low"),      # trim + case-fold suffix
    ],
)
def test_normalize(raw: str, model: str, effort: str | None) -> None:
    out = normalize_model_slug(raw)
    assert out == ModelSlug(model=model, reasoning_effort=effort, raw=raw)


def test_empty_raises() -> None:
    with pytest.raises(ValueError):
        normalize_model_slug("   ")
