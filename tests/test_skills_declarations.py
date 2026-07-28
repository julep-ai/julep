"""Reasoner.skills: identity, replace(), and the declarations blob round trip."""

from __future__ import annotations

import hashlib
import json

import pytest

from julep.dotctx import Reasoner
from julep.skills import Skill, skill_key

ALPHA = Skill(name="alpha", description="describes alpha", body="Do alpha.")
BETA = Skill(name="beta", description="describes beta", body="Do beta.")
ALPHA_KEY = skill_key(ALPHA)
BETA_KEY = skill_key(BETA)


def test_reasoner_defaults_to_no_skills() -> None:
    assert Reasoner(name="r", model="openai:gpt-5.5").skills == ()


def test_reasoner_stores_skill_keys_in_order() -> None:
    r = Reasoner(name="r", model="openai:gpt-5.5", skills=[BETA_KEY, ALPHA_KEY])
    assert r.skills == (BETA_KEY, ALPHA_KEY)


def test_malformed_skill_key_is_rejected_at_construction() -> None:
    with pytest.raises(ValueError, match="malformed skill key"):
        Reasoner(name="r", model="openai:gpt-5.5", skills=["natural-writing"])


def test_replace_preserves_and_overrides_skills() -> None:
    r = Reasoner(name="r", model="openai:gpt-5.5", skills=[ALPHA_KEY])
    assert r.replace(temperature=0.5).skills == (ALPHA_KEY,)
    assert r.replace(skills=()).skills == ()
    assert r.replace(skills=[BETA_KEY]).skills == (BETA_KEY,)


def test_identity_omits_skills_when_absent_and_includes_them_when_set() -> None:
    from julep.deploy import _reasoner_identity
    from julep.registry import DEFAULT_REGISTRY

    plain = Reasoner(name="ident-plain", model="openai:gpt-5.5")
    DEFAULT_REGISTRY.register_reasoner(plain)
    assert "skills" not in _reasoner_identity("ident-plain")

    skilled = Reasoner(name="ident-skilled", model="openai:gpt-5.5", skills=[ALPHA_KEY])
    DEFAULT_REGISTRY.register_reasoner(skilled)
    assert _reasoner_identity("ident-skilled")["skills"] == [ALPHA_KEY]


def test_editing_a_skill_body_moves_the_reasoner_identity() -> None:
    from julep.deploy import _reasoner_identity
    from julep.registry import DEFAULT_REGISTRY

    edited = Skill(name="alpha", description="describes alpha", body="Do alpha DIFFERENTLY.")
    before = Reasoner(name="ident-drift", model="openai:gpt-5.5", skills=[ALPHA_KEY])
    DEFAULT_REGISTRY.register_reasoner(before)
    first = _reasoner_identity("ident-drift")

    DEFAULT_REGISTRY.reasoners.pop("ident-drift")
    after = Reasoner(name="ident-drift", model="openai:gpt-5.5", skills=[skill_key(edited)])
    DEFAULT_REGISTRY.register_reasoner(after)
    assert _reasoner_identity("ident-drift") != first


def test_blob_carries_skill_bodies_and_round_trips() -> None:
    from julep.declarations import declarations_blob, load_declarations
    from julep.registry import Registry

    source = Registry()
    key = source.register_skill(ALPHA)
    reasoner = Reasoner(name="blob-r", model="openai:gpt-5.5", skills=[key])
    blob = declarations_blob([reasoner], registry=source)

    payload = json.loads(blob)
    assert payload["schemaVersion"] == 3
    assert payload["skills"][key] == {
        "name": "alpha",
        "description": "describes alpha",
        "body": "Do alpha.",
    }
    assert payload["reasoners"]["blob-r"]["skills"] == [key]

    target = Registry()
    load_declarations(
        blob,
        expected_hash="sha256:" + hashlib.sha256(blob).hexdigest(),
        registry=target,
    )
    assert target.get_reasoner("blob-r").skills == (key,)
    assert target.get_skill(key).body == "Do alpha."


def test_blob_rejects_a_skill_key_that_does_not_match_its_content() -> None:
    from julep.declarations import DeclarationError, load_declarations
    from julep.registry import Registry

    payload = {
        "schemaVersion": 3,
        "reasoners": {},
        "renderers": {},
        "agents": {},
        "skills": {
            "skill/alpha@v000000000000": {
                "name": "alpha",
                "description": "describes alpha",
                "body": "Do alpha.",
            }
        },
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with pytest.raises(DeclarationError, match="content hash"):
        load_declarations(
            blob,
            expected_hash="sha256:" + hashlib.sha256(blob).hexdigest(),
            registry=Registry(),
        )


def test_blob_rejects_a_reasoner_referencing_an_undeclared_skill() -> None:
    from julep.declarations import DeclarationError, load_declarations
    from julep.registry import Registry

    payload = {
        "schemaVersion": 3,
        "reasoners": {
            "orphan": {
                "name": "orphan",
                "model": "openai:gpt-5.5",
                "system": "",
                "replySchema": None,
                "tools": [],
                "temperature": None,
                "maxRounds": None,
                "isAgent": False,
                "subContract": None,
                "contextScope": "local",
                "systemRender": None,
                "userRender": None,
                "maxTokens": None,
                "reasoningEffort": None,
                "outputRetries": 0,
                "requireToolCall": False,
                "responseFormat": None,
                "promptCache": None,
                "skills": [ALPHA_KEY],
                "rendererSourceHashes": {},
            }
        },
        "renderers": {},
        "agents": {},
        "skills": {},
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with pytest.raises(DeclarationError, match="undeclared skill"):
        load_declarations(
            blob,
            expected_hash="sha256:" + hashlib.sha256(blob).hexdigest(),
            registry=Registry(),
        )


def test_blob_fails_when_the_source_registry_lacks_a_referenced_skill() -> None:
    from julep.app import ApplicationDefinitionError
    from julep.declarations import declarations_blob
    from julep.registry import Registry

    reasoner = Reasoner(name="missing-skill", model="openai:gpt-5.5", skills=[BETA_KEY])
    with pytest.raises(ApplicationDefinitionError, match="no registered content"):
        declarations_blob([reasoner], registry=Registry())
