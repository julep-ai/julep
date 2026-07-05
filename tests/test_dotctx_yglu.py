"""Task 7: yglu-evaluated settings.yaml with an explicit $env binding.

The first group of tests exercises real yglu evaluation and skips without the
[yglu] extra (per-test importorskip). The hard-error test runs everywhere —
it is exactly the no-yglu path.
"""
import os

import pytest

from julep.dotctx import load_dotctx
from julep.dotctx_yglu import has_yglu_tags, load_settings

SETTINGS = 'model: !? $env.get("SUMMARY_MODEL", "openai/gpt-5.4-nano@medium")\n'


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
    # text to yglu (where load reports the real error).
    assert has_yglu_tags('a: [unclosed\nb: !? $env.get("X", "y")\n')
    assert not has_yglu_tags("a: [unclosed\nb: plain\n")


def test_env_default_when_unset() -> None:
    pytest.importorskip("yglu")
    out = load_settings(SETTINGS, env={}, filepath="settings.yaml")
    assert out["model"] == "openai/gpt-5.4-nano@medium"


def test_explicit_env_wins_and_ambient_never_leaks() -> None:
    pytest.importorskip("yglu")
    os.environ["SUMMARY_MODEL"] = "ambient:leak"
    try:
        out = load_settings(SETTINGS, env={"SUMMARY_MODEL": "openai:gpt-5.5@low"},
                            filepath="settings.yaml")
        assert out["model"] == "openai:gpt-5.5@low"
        out2 = load_settings(SETTINGS, env={}, filepath="settings.yaml")
        assert out2["model"] == "openai/gpt-5.4-nano@medium"   # ambient invisible
    finally:
        del os.environ["SUMMARY_MODEL"]


def test_load_dotctx_end_to_end(tmp_path) -> None:
    pytest.importorskip("yglu")
    d = tmp_path / "summary.ctx"
    d.mkdir()
    (d / "settings.yaml").write_text(SETTINGS)
    r = load_dotctx(str(d), env={"SUMMARY_MODEL": "anthropic:claude-sonnet-4-6@high"})
    assert r.model == "anthropic:claude-sonnet-4-6"
    assert r.reasoning_effort == "high"


def test_tagged_settings_without_yglu_is_hard_error(tmp_path, monkeypatch) -> None:
    import julep.dotctx_yglu as dy
    monkeypatch.setattr(dy, "_import_yglu", lambda: (_ for _ in ()).throw(
        ImportError("no yglu")))
    d = tmp_path / "t.ctx"
    d.mkdir()
    (d / "settings.yaml").write_text(SETTINGS)
    with pytest.raises(ImportError, match=r"julep\[yglu\]"):
        load_dotctx(str(d))
