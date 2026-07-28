"""Native ``!? $env.get(...)`` settings evaluation with an explicit env binding."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from julep.dotctx import load_dotctx
from julep.dotctx_yglu import (
    default_env,
    has_yglu_tags,
    load_settings,
    set_default_env,
)

SETTINGS = 'model: !? $env.get("SUMMARY_MODEL", "openai/gpt-5.4-nano@medium")\n'


@pytest.fixture
def restore_default_env() -> Iterator[None]:
    previous = default_env()
    try:
        yield
    finally:
        set_default_env(previous)


def test_has_yglu_tags() -> None:
    assert has_yglu_tags(SETTINGS)
    assert not has_yglu_tags("model: openai:gpt-4o\n")


def test_has_yglu_tags_all_tag_forms() -> None:
    assert has_yglu_tags("x: !() $_\n")
    assert has_yglu_tags("x: !if cond\n")
    assert has_yglu_tags("x: !for [1, 2]\n")
    assert has_yglu_tags("x: !concat [a, b]\n")
    assert has_yglu_tags("x: !merge [a, b]\n")


def test_has_yglu_tags_ignores_punctuation_in_strings() -> None:
    # `!?` inside a scalar is content, not a YAML tag (codex PR #11 review).
    assert not has_yglu_tags('system: "Really!?"\n')
    assert not has_yglu_tags("system: Really!? yes\n")
    assert not has_yglu_tags('system: "ask this: !? verbatim"\n')


def test_has_yglu_tags_unscannable_text_falls_back_to_regex() -> None:
    # Broken YAML cannot be scanned; the regex fallback still routes tagged
    # text to the native evaluator, where loading reports the real error.
    assert has_yglu_tags('a: [unclosed\nb: !? $env.get("X", "y")\n')
    assert not has_yglu_tags("a: [unclosed\nb: plain\n")


def test_unset_vars_preserve_string_and_int_defaults() -> None:
    text = """\
model: !? $env.get("MODEL", "openai/gpt-5.4-nano@medium")
max_rounds: !? $env.get("MAX_ROUNDS", 12)
"""
    out = load_settings(text, env={}, filepath="settings.yaml")
    assert out["model"] == "openai/gpt-5.4-nano@medium"
    assert out["max_rounds"] == 12
    assert isinstance(out["max_rounds"], int)


def test_set_env_values_win_verbatim_as_strings() -> None:
    text = """\
model: !? $env.get("MODEL", "fallback")
max_rounds: !? $env.get("MAX_ROUNDS", 12)
"""
    out = load_settings(
        text,
        env={"MODEL": "synthetic-model", "MAX_ROUNDS": "60"},
        filepath="settings.yaml",
    )
    assert out["model"] == "synthetic-model"
    assert out["max_rounds"] == "60"
    assert isinstance(out["max_rounds"], str)


def test_nested_env_fallback_chains() -> None:
    text = """\
two: !? $env.get("OUTER", $env.get("MIDDLE", "two-default"))
three: !? $env.get("OUTER", $env.get("MIDDLE", $env.get("INNER", "three-default")))
"""
    assert load_settings(text, env={}, filepath="settings.yaml") == {
        "two": "two-default",
        "three": "three-default",
    }
    assert load_settings(text, env={"MIDDLE": "middle"}, filepath="settings.yaml") == {
        "two": "middle",
        "three": "middle",
    }
    assert load_settings(
        text,
        env={"OUTER": "outer", "MIDDLE": "middle", "INNER": "inner"},
        filepath="settings.yaml",
    ) == {"two": "outer", "three": "outer"}


def test_env_get_without_default_preserves_dict_get_semantics() -> None:
    text = 'value: !? $env.get("X")\n'
    assert load_settings(text, env={}, filepath="settings.yaml")["value"] is None
    assert load_settings(text, env={"X": "set"}, filepath="settings.yaml")["value"] == "set"


def test_default_env_binding_and_reset(restore_default_env: None) -> None:
    set_default_env({"SUMMARY_MODEL": "default-binding"})
    assert load_settings(SETTINGS, env=None, filepath="settings.yaml")["model"] == (
        "default-binding"
    )

    set_default_env(None)
    assert load_settings(SETTINGS, env=None, filepath="settings.yaml")["model"] == (
        "openai/gpt-5.4-nano@medium"
    )


def test_explicit_env_wins_and_ambient_never_leaks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUMMARY_MODEL", "ambient:leak")
    out = load_settings(
        SETTINGS,
        env={"SUMMARY_MODEL": "openai:gpt-5.5@low"},
        filepath="settings.yaml",
    )
    assert out["model"] == "openai:gpt-5.5@low"
    out_without_binding = load_settings(SETTINGS, env={}, filepath="settings.yaml")
    assert out_without_binding["model"] == "openai/gpt-5.4-nano@medium"


def test_load_dotctx_end_to_end(tmp_path: Path) -> None:
    # Reasoner names land in the process-global DEFAULT_REGISTRY: keep this one
    # distinct from other modules' `summary.ctx` packages (different models).
    path = tmp_path / "tagged_summary.ctx"
    path.mkdir()
    (path / "settings.yaml").write_text(SETTINGS)
    reasoner = load_dotctx(str(path), env={"SUMMARY_MODEL": "anthropic:claude-sonnet-4-6@high"})
    assert reasoner.model == "anthropic:claude-sonnet-4-6"
    assert reasoner.reasoning_effort == "high"


@pytest.mark.parametrize(
    "tagged_value",
    ["!() value", "!if value", "!for [value]", "!concat [value]", "!merge [value]"],
)
def test_unsupported_yglu_tags_have_actionable_errors(tagged_value: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        load_settings(f"value: {tagged_value}\n", env={}, filepath="unsupported.yaml")
    message = str(exc_info.value)
    assert "unsupported.yaml" in message
    assert tagged_value.split()[0] in message
    assert "removed in 3.0.0rc5" in message
    assert "$env.get" in message
    assert "run input/metadata" in message


@pytest.mark.parametrize(
    "expression",
    ["1 + 1", "$env", "$env.get(FOO)"],
)
def test_unsupported_expressions_have_actionable_errors(expression: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        load_settings(f"value: !? {expression}\n", env={}, filepath="invalid.yaml")
    message = str(exc_info.value)
    assert "invalid.yaml" in message
    assert expression in message
    assert "removed in 3.0.0rc5" in message
    assert "$env.get" in message
    assert "run input/metadata" in message


@pytest.mark.parametrize("node", ["[1, 2]", "{key: value}"])
def test_expression_tag_requires_scalar_node(node: str) -> None:
    with pytest.raises(ValueError, match="non-scalar") as exc_info:
        load_settings(f"value: !? {node}\n", env={}, filepath="invalid-node.yaml")
    assert "invalid-node.yaml" in str(exc_info.value)
    assert "removed in 3.0.0rc5" in str(exc_info.value)


def test_representative_memmcp_expressions() -> None:
    text = """\
model: !? $env.get("SUMMARY_MODEL", "openai/gpt-5.4-nano@medium")
classifier_model: !? $env.get("LIVING_BRIEF_DREAM_CLASSIFIER_MODEL", $env.get("LIVING_BRIEF_MEMORY_RELEVANCE_MODEL", $env.get("LIVING_BRIEF_QUALIFY_MODEL", "openai/gpt-5.4-mini@low")))
max_rounds: !? $env.get("THREAD_MERGE_AGENT_LOOP_MAX_ROUNDS", $env.get("GLOBAL_AGENT_LOOP_MAX_ROUNDS", 10))
"""
    assert load_settings(text, env={}, filepath="mem-mcp/settings.yaml") == {
        "model": "openai/gpt-5.4-nano@medium",
        "classifier_model": "openai/gpt-5.4-mini@low",
        "max_rounds": 10,
    }
    assert load_settings(
        text,
        env={
            "SUMMARY_MODEL": "synthetic-summary",
            "LIVING_BRIEF_MEMORY_RELEVANCE_MODEL": "synthetic-classifier",
            "GLOBAL_AGENT_LOOP_MAX_ROUNDS": "42",
        },
        filepath="mem-mcp/settings.yaml",
    ) == {
        "model": "synthetic-summary",
        "classifier_model": "synthetic-classifier",
        "max_rounds": "42",
    }


def test_empty_document_and_non_mapping() -> None:
    assert load_settings("", env={}, filepath="empty.yaml") == {}
    with pytest.raises(ValueError, match="settings must be a YAML mapping"):
        load_settings("- one\n- two\n", env={}, filepath="list.yaml")
