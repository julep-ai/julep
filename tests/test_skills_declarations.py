"""Reasoner.skills: identity, replace(), and the declarations blob round trip."""

from __future__ import annotations

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
