"""Progressive skill disclosure: the prompt block, the tool, and the inner loop."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

import pytest

from julep.dotctx import Reasoner
from julep.registry import Registry
from julep.skills import (
    SKILL_TOOL,
    Skill,
    batch_system_text,
    inline_skills_block,
    load_skill_tool_def,
    resolve_skill_keys,
    skills_prompt_block,
)

ALPHA = Skill(name="alpha", description="Use for alpha work.", body="ALPHA BODY")
BETA = Skill(name="beta", description="Use for beta work.", body="BETA BODY")


def test_prompt_block_lists_names_and_descriptions_but_never_bodies() -> None:
    block = skills_prompt_block([ALPHA, BETA])
    assert "alpha" in block and "Use for alpha work." in block
    assert "beta" in block and "Use for beta work." in block
    assert "ALPHA BODY" not in block and "BETA BODY" not in block
    assert SKILL_TOOL in block


def test_tool_def_enumerates_only_undisclosed_skills() -> None:
    definition = load_skill_tool_def([ALPHA, BETA], loaded=["alpha"])
    assert definition["function"]["name"] == SKILL_TOOL
    enum = definition["function"]["parameters"]["properties"]["name"]["enum"]
    assert enum == ["beta"]
    assert definition["function"]["parameters"]["required"] == ["name"]


def test_inline_block_carries_full_bodies() -> None:
    block = inline_skills_block([ALPHA])
    assert "ALPHA BODY" in block and "Use for alpha work." in block


def test_resolve_skill_keys_reads_the_registry() -> None:
    reg = Registry()
    key = reg.register_skill(ALPHA)
    assert resolve_skill_keys([key], registry=reg) == (ALPHA,)


def test_batch_system_text_inlines_and_preserves_the_system() -> None:
    reg = Registry()
    key = reg.register_skill(ALPHA)
    text = batch_system_text("You draft.", [key], registry=reg)
    assert text.endswith("You draft.")
    assert "ALPHA BODY" in text


def test_batch_system_text_passes_through_without_skills() -> None:
    assert batch_system_text("You draft.", [], registry=Registry()) == "You draft."
