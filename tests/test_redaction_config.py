"""Configuration-driven trajectory redaction tests."""

from __future__ import annotations

import json

import pytest

from julep.trajectory import (
    REDACTED_PLACEHOLDER,
    RedactionConfig,
    build_redactor,
    redact_secret_shaped,
)


def test_redaction_config_from_mapping_validates_strictly() -> None:
    config = RedactionConfig.from_mapping(
        {
            "key_patterns": ["^private$"],
            "path_patterns": ("items.*.note",),
            "disable_default": True,
        }
    )
    assert config == RedactionConfig(
        key_patterns=("^private$",),
        path_patterns=("items.*.note",),
        disable_default=True,
    )

    with pytest.raises(ValueError, match="unknown redaction config keys"):
        RedactionConfig.from_mapping({"extra": True})
    with pytest.raises(ValueError, match="key_patterns"):
        RedactionConfig.from_mapping({"key_patterns": ["valid", 1]})
    with pytest.raises(ValueError, match="disable_default"):
        RedactionConfig.from_mapping({"disable_default": "yes"})
    with pytest.raises(ValueError, match="invalid redaction.*regex"):
        RedactionConfig.from_mapping({"key_patterns": ["["]})
    with pytest.raises(ValueError, match="path_patterns"):
        RedactionConfig.from_mapping({"path_patterns": ["items..note"]})


def test_redaction_config_from_json_requires_object() -> None:
    config = RedactionConfig.from_json(
        '{"key_patterns":["^private$"],"disable_default":true}'
    )
    assert config.key_patterns == ("^private$",)
    assert config.disable_default is True

    with pytest.raises(ValueError, match="invalid redaction JSON"):
        RedactionConfig.from_json("{")
    with pytest.raises(ValueError, match="must be an object"):
        RedactionConfig.from_json("[]")


def test_build_redactor_custom_key_patterns_preserve_other_payloads() -> None:
    redactor = build_redactor(
        RedactionConfig(key_patterns=(r"^private$",), disable_default=True)
    )
    value = {
        "public": {"private": "hidden", "count": 2},
        "items": [{"private_note": "kept"}],
    }
    assert redactor(value) == {
        "public": {"private": REDACTED_PLACEHOLDER, "count": 2},
        "items": [{"private_note": "kept"}],
    }

    unmatched = {"public": [{"count": 2, "ok": True}], "none": None}
    assert json.dumps(redactor(unmatched), sort_keys=True) == json.dumps(
        unmatched, sort_keys=True
    )


def test_build_redactor_composes_default_secret_floor() -> None:
    redactor = build_redactor(RedactionConfig(key_patterns=(r"^private$",)))
    assert redactor(
        {"api_key": "secret", "authorization": "Bearer x", "private": "pii"}
    ) == {
        "api_key": REDACTED_PLACEHOLDER,
        "authorization": REDACTED_PLACEHOLDER,
        "private": REDACTED_PLACEHOLDER,
    }


def test_build_redactor_can_disable_default_floor() -> None:
    redactor = build_redactor(
        RedactionConfig(key_patterns=(r"^authorization$",), disable_default=True)
    )
    assert redactor({"api_key": "kept", "authorization": "hidden"}) == {
        "api_key": "kept",
        "authorization": REDACTED_PLACEHOLDER,
    }


def test_build_redactor_path_patterns_target_exact_paths_and_list_levels() -> None:
    redactor = build_redactor(
        RedactionConfig(
            path_patterns=("profile.private", "items.*.secret"),
            disable_default=True,
        )
    )
    value = {
        "profile": {"private": {"deep": "hidden"}, "public": "kept"},
        "items": [
            {"secret": "one", "sibling": "a"},
            {"secret": "two", "sibling": "b"},
        ],
        "other": {"secret": "kept"},
    }
    assert redactor(value) == {
        "profile": {"private": REDACTED_PLACEHOLDER, "public": "kept"},
        "items": [
            {"secret": REDACTED_PLACEHOLDER, "sibling": "a"},
            {"secret": REDACTED_PLACEHOLDER, "sibling": "b"},
        ],
        "other": {"secret": "kept"},
    }


def test_empty_config_matches_default_redactor() -> None:
    value = {
        "api_key": "secret",
        "nested": [{"authorization": "Bearer x", "public": 1}],
        "other": {"enabled": True},
    }
    assert build_redactor(RedactionConfig())(value) == redact_secret_shaped(value)


def test_build_redactor_does_not_mutate_input() -> None:
    value = {"items": [{"secret": "raw", "sibling": [1, 2]}]}
    before = json.loads(json.dumps(value))
    redactor = build_redactor(
        RedactionConfig(path_patterns=("items.*.secret",), disable_default=True)
    )

    redactor(value)

    assert value == before
