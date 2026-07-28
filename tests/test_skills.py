"""Skill value type, SKILL.md parsing, package loading, and registration."""

from __future__ import annotations

import pytest

from julep.skills import (
    SKILL_TOOL,
    Skill,
    SkillError,
    parse_skill_markdown,
    skill_key,
)

SKILL_MD = """\
---
name: natural-writing
description: >
  Write like a human, not a language model.
---

# Natural Writing

Cut the significance inflation.
"""


def test_parse_skill_markdown_splits_frontmatter_from_body() -> None:
    skill = parse_skill_markdown(SKILL_MD, origin="skills/natural-writing/SKILL.md")
    assert skill.name == "natural-writing"
    assert skill.description == "Write like a human, not a language model."
    assert skill.body.startswith("# Natural Writing")
    assert "significance inflation" in skill.body
    assert skill.source == "skills/natural-writing/SKILL.md"


def test_key_is_content_addressed_and_ignores_source() -> None:
    a = parse_skill_markdown(SKILL_MD, origin="pkg_a/skills/natural-writing/SKILL.md")
    b = parse_skill_markdown(SKILL_MD, origin="pkg_b/skills/natural-writing/SKILL.md")
    assert skill_key(a) == skill_key(b)
    assert a == b                       # source is excluded from equality
    assert skill_key(a).startswith("skill/natural-writing@v")
    assert len(skill_key(a).rsplit("@v", 1)[1]) == 12


def test_key_changes_when_body_changes() -> None:
    a = parse_skill_markdown(SKILL_MD, origin="x")
    b = parse_skill_markdown(SKILL_MD.replace("inflation", "deflation"), origin="x")
    assert skill_key(a) != skill_key(b)


def test_key_changes_when_description_changes() -> None:
    a = parse_skill_markdown(SKILL_MD, origin="x")
    b = parse_skill_markdown(SKILL_MD.replace("a language model", "an LLM"), origin="x")
    assert skill_key(a) != skill_key(b)


def test_missing_frontmatter_is_a_loud_error() -> None:
    with pytest.raises(SkillError, match="has no YAML frontmatter"):
        parse_skill_markdown("# Just a heading\n", origin="skills/x/SKILL.md")


def test_crlf_document_matches_lf_skill_key() -> None:
    lf_skill = parse_skill_markdown(SKILL_MD, origin="skills/natural-writing/SKILL.md")
    crlf_skill = parse_skill_markdown(
        SKILL_MD.replace("\n", "\r\n"),
        origin="skills/natural-writing/SKILL.md",
    )
    assert crlf_skill == lf_skill
    assert skill_key(crlf_skill) == skill_key(lf_skill)


def test_delimiter_trailing_whitespace_is_accepted() -> None:
    text = SKILL_MD.replace("---\n", "--- \n", 1).replace("\n---\n", "\n---\t\n", 1)
    skill = parse_skill_markdown(text, origin="skills/natural-writing/SKILL.md")
    assert skill.name == "natural-writing"
    assert skill.body.startswith("# Natural Writing")


def test_utf8_bom_is_accepted() -> None:
    skill = parse_skill_markdown(
        "\ufeff" + SKILL_MD,
        origin="skills/natural-writing/SKILL.md",
    )
    assert skill.name == "natural-writing"


def test_empty_frontmatter_reports_missing_name() -> None:
    with pytest.raises(SkillError, match="frontmatter needs a non-empty name"):
        parse_skill_markdown("---\n---\n\nbody\n", origin="skills/x/SKILL.md")


def test_missing_name_is_a_loud_error() -> None:
    text = "---\ndescription: no name here\n---\n\nbody\n"
    with pytest.raises(SkillError, match="non-empty name"):
        parse_skill_markdown(text, origin="skills/x/SKILL.md")


def test_non_mapping_frontmatter_is_a_loud_error() -> None:
    with pytest.raises(SkillError, match="YAML mapping"):
        parse_skill_markdown("---\n- a\n- b\n---\n\nbody\n", origin="skills/x/SKILL.md")


def test_empty_body_is_a_loud_error() -> None:
    text = "---\nname: x\ndescription: d\n---\n\n   \n"
    with pytest.raises(SkillError, match="empty body"):
        parse_skill_markdown(text, origin="skills/x/SKILL.md")


def test_skill_tool_name_is_provider_safe() -> None:
    from julep.execution.llm import provider_safe_tool_name

    assert provider_safe_tool_name(SKILL_TOOL) == SKILL_TOOL


import os

from julep.skills import (
    InertSkillsDirectoryWarning,
    load_package_skills,
    parse_skills_setting,
)


def _write_skill(pkg: str, dirname: str, *, name: str, body: str = "Do the thing.") -> None:
    path = os.path.join(pkg, "skills", dirname)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as fh:
        fh.write(f"---\nname: {name}\ndescription: describes {name}\n---\n\n{body}\n")


def test_allowlist_selects_and_orders_by_declaration(tmp_path) -> None:
    pkg = str(tmp_path)
    _write_skill(pkg, "alpha", name="alpha")
    _write_skill(pkg, "beta", name="beta")
    skills = load_package_skills(pkg, ["beta", "alpha"])
    assert [s.name for s in skills] == ["beta", "alpha"]


def test_absent_key_activates_nothing_and_warns_when_dir_exists(tmp_path) -> None:
    pkg = str(tmp_path)
    _write_skill(pkg, "alpha", name="alpha")
    with pytest.warns(InertSkillsDirectoryWarning, match="skills/"):
        assert load_package_skills(pkg, None) == ()


def test_empty_list_activates_nothing_without_warning(tmp_path, recwarn) -> None:
    pkg = str(tmp_path)
    _write_skill(pkg, "alpha", name="alpha")
    assert load_package_skills(pkg, []) == ()
    assert not [w for w in recwarn if w.category is InertSkillsDirectoryWarning]


def test_no_skills_dir_and_no_allowlist_is_silent(tmp_path, recwarn) -> None:
    assert load_package_skills(str(tmp_path), None) == ()
    assert not [w for w in recwarn if w.category is InertSkillsDirectoryWarning]


def test_configured_name_without_a_sidecar_fails_closed(tmp_path) -> None:
    pkg = str(tmp_path)
    _write_skill(pkg, "alpha", name="alpha")
    with pytest.raises(SkillError, match="ghost.*available.*alpha"):
        load_package_skills(pkg, ["ghost"])


def test_allowlist_without_a_skills_dir_fails_closed(tmp_path) -> None:
    with pytest.raises(SkillError, match="no skills/ directory"):
        load_package_skills(str(tmp_path), ["alpha"])


def test_extra_file_in_a_skill_directory_is_rejected(tmp_path) -> None:
    pkg = str(tmp_path)
    _write_skill(pkg, "alpha", name="alpha")
    with open(os.path.join(pkg, "skills", "alpha", "references.md"), "w") as fh:
        fh.write("more")
    with pytest.raises(SkillError, match="references.md"):
        load_package_skills(pkg, ["alpha"])


def test_loose_file_directly_under_skills_is_rejected(tmp_path) -> None:
    pkg = str(tmp_path)
    _write_skill(pkg, "alpha", name="alpha")
    with open(os.path.join(pkg, "skills", "README.md"), "w") as fh:
        fh.write("hi")
    with pytest.raises(SkillError, match="README.md"):
        load_package_skills(pkg, ["alpha"])


def test_directory_name_must_match_frontmatter_name(tmp_path) -> None:
    pkg = str(tmp_path)
    _write_skill(pkg, "alpha", name="not-alpha")
    with pytest.raises(
        SkillError,
        match=(
            "directory 'alpha'.*declares name 'not-alpha'.*"
            "directory name and the frontmatter name must match"
        ),
    ):
        load_package_skills(pkg, ["not-alpha"])


def test_mismatched_directory_is_rejected_when_name_has_a_legitimate_owner(
    tmp_path,
) -> None:
    pkg = str(tmp_path)
    _write_skill(pkg, "alpha", name="alpha")
    os.makedirs(os.path.join(pkg, "skills", "alpha-copy"))
    with open(os.path.join(pkg, "skills", "alpha-copy", "SKILL.md"), "w") as fh:
        fh.write("---\nname: alpha\ndescription: dupe\n---\n\nbody\n")
    with pytest.raises(
        SkillError,
        match=(
            "directory 'alpha-copy'.*declares name 'alpha'.*"
            "directory name and the frontmatter name must match"
        ),
    ):
        load_package_skills(pkg, ["alpha"])


def test_duplicate_allowlist_entries_are_rejected() -> None:
    with pytest.raises(SkillError, match="duplicate"):
        parse_skills_setting(["a", "a"], origin="settings.yaml")


def test_parse_skills_setting_forms() -> None:
    assert parse_skills_setting(None, origin="s") is None
    assert parse_skills_setting([], origin="s") == ()
    assert parse_skills_setting(["a", "b"], origin="s") == ("a", "b")


def test_mapping_items_reserved_for_future_options() -> None:
    with pytest.raises(SkillError, match="list of skill names"):
        parse_skills_setting([{"name": "a", "mode": "inline"}], origin="s")


def test_non_list_setting_is_rejected() -> None:
    with pytest.raises(SkillError, match="list of skill names"):
        parse_skills_setting("natural-writing", origin="s")


from julep.registry import Registry
from julep.skills import get_skill, register_skill, skill_keys


def _skill(name: str, body: str = "body") -> Skill:
    return Skill(name=name, description=f"describes {name}", body=body)


def test_register_returns_the_content_key_and_round_trips() -> None:
    reg = Registry()
    key = reg.register_skill(_skill("alpha"))
    assert key == skill_key(_skill("alpha"))
    assert reg.get_skill(key).body == "body"


def test_identical_skills_from_different_sources_converge() -> None:
    reg = Registry()
    a = Skill(name="alpha", description="describes alpha", body="body", source="pkg_a")
    b = Skill(name="alpha", description="describes alpha", body="body", source="pkg_b")
    assert reg.register_skill(a) == reg.register_skill(b)
    assert len(reg.skills) == 1


def test_edited_copies_coexist_under_distinct_keys() -> None:
    reg = Registry()
    first = reg.register_skill(_skill("alpha", body="one"))
    second = reg.register_skill(_skill("alpha", body="two"))
    assert first != second
    assert len(reg.skills) == 2


def test_register_rejects_nul_boundary_key_collision() -> None:
    reg = Registry()
    first = Skill(name="a", description="x\0y", body="z")
    second = Skill(name="a", description="x", body="y\0z")
    assert skill_key(first) == skill_key(second)
    assert first != second
    reg.register_skill(first)
    with pytest.raises(ValueError, match="already registered with different content"):
        reg.register_skill(second)


def test_unknown_key_teaches() -> None:
    reg = Registry()
    with pytest.raises(KeyError, match="unknown skill"):
        reg.get_skill("skill/ghost@v000000000000")


def test_skill_keys_registers_objects_and_passes_strings_through() -> None:
    reg = Registry()
    existing = reg.register_skill(_skill("beta"))
    keys = skill_keys([_skill("alpha"), existing], registry=reg)
    assert keys == (skill_key(_skill("alpha")), existing)
    assert set(reg.skills) == set(keys)


def test_module_level_helpers_use_the_default_registry() -> None:
    key = register_skill(_skill("gamma-unique-to-this-test"))
    assert get_skill(key).name == "gamma-unique-to-this-test"


def test_default_registry_skills_are_restored_between_tests() -> None:
    key = skill_key(_skill("gamma-unique-to-this-test"))
    with pytest.raises(KeyError, match="unknown skill"):
        get_skill(key)


def test_public_exports() -> None:
    import julep

    assert julep.Skill is Skill
    assert julep.SKILL_TOOL == SKILL_TOOL
    for name in (
        "Skill",
        "SkillError",
        "SKILL_TOOL",
        "register_skill",
        "get_skill",
        "skill_keys",
        "load_package_skills",
    ):
        assert name in julep.__all__, name


def test_code_first_authoring_round_trip() -> None:
    from julep.dotctx import Reasoner
    from julep.registry import Registry

    reg = Registry()
    written = Skill(
        name="house-style", description="How we write.", body="Short sentences."
    )
    reasoner = Reasoner(
        name="code-first",
        model="openai:gpt-5.5",
        system="You write.",
        skills=skill_keys([written], registry=reg),
    )
    assert reg.get_skill(reasoner.skills[0]).body == "Short sentences."
