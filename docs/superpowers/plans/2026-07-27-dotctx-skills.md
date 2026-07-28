# dotctx Skills (Progressive Disclosure) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach Julep the `skills:` dotctx setting — a package activates named `SKILL.md` sidecars, whose descriptions ride in the system prompt and whose bodies the model pulls mid-call through a reserved `__load_skill__` tool resolved from the frozen release.

**Architecture:** A skill is a content-addressed registry citizen (`skill/<name>@v<hash12>`) sitting beside pures, renderers, and reasoners. `Reasoner.skills` holds those keys, so an edited skill body changes the reasoner identity by the same mechanism an edited template already does. Disclosure happens *inside* `complete_reasoner` as a bounded inner provider loop — the same shape `output_retries` already uses — so it never touches the IR: a `think` leaf stays a `think` leaf and `max_rounds` keeps meaning rounds of task progress.

**Tech Stack:** Python 3.12+, PyYAML, pytest. No new dependencies. jinja2 is deliberately *not* required — `julep/skills.py` must import cleanly without the `[dotctx]` extra.

## Global Constraints

- Target release: **rc6**. rc5 has shipped; nothing here may change the meaning of an already-frozen artifact.
- Skills resolve **only** from `<pkg>.ctx/skills/<name>/SKILL.md`. No upward search, no shared root — dotctx packages stay standalone. Duplication across packages is accepted and deduplicated by content hash, not by path.
- Activation is **explicit**: the `skills:` key absent means no skills. This deliberately diverges from mem-mcp's implicit-all rule.
- Only `SKILL.md` is supported inside a skill directory. Any other file is a load-time error. Levels 1+2 of Anthropic's three-level skill format; level 3 (bundled `references/`, `scripts/`) is reserved.
- Every failure is loud at load time with the offending file/name in the message (G-8: loud, never silent).
- Skill bodies never live on `Reasoner` and never reach the provider except as a tool result.
- Content hashes cover `name`, `description`, `body` — never the source path.
- Declarations blob schema version bumps `2` → `3`.
- Run tests with `uv run python -m pytest` (a bare `pytest` also collects; `pythonpath = ["."]` is set in `pyproject.toml:147`).

## Design Decision Requiring Confirmation

`julep/execution/llm.py:653` sets `native_response_format = native and not has_tools` — offering *any* tool disables provider-native `response_format` and falls back to prompt-injected schema guidance. All three real skill-using packages (`briefs/draft.ctx`, `briefs/review.ctx`, `briefs/plan_sections.ctx`) carry a `schema.pyi`, so they currently get native structured output.

**Chosen default (implemented by Task 7):** a two-phase call. The skill tool is offered only while undisclosed skills remain; once the model has loaded what it wants (or the budget closes), the tool is withdrawn and the final call runs tool-free, restoring native `response_format` for reasoners that grant no real tools.

**The residual cost:** when the model loads *no* skill, the single call it makes still carried the tool, so that call loses native structured output. `output_retries` (set to `1` on all three packages) is the existing safety net. Relaxing the blanket `not has_tools` rule for providers that support tools alongside structured outputs is a real fix but is **out of scope here** — it changes behavior for every tool-bearing reasoner, not just skill users.

---

## File Structure

**Created:**
- `julep/skills.py` — the whole skill vocabulary: `Skill`, key derivation, `SKILL.md` parsing, package loading, prompt-block and tool-definition formatting, batch inlining. No jinja2, no `Reasoner` import (keeps it importable from `julep/dotctx.py` without a cycle).
- `tests/test_skills.py` — value type, parser, package loader, registry.
- `tests/test_skills_dotctx.py` — settings wiring across all three package layouts.
- `tests/test_skills_declarations.py` — artifact identity and blob round trip.
- `tests/test_llm_skills.py` — the runtime disclosure loop.
- `tests/fixtures/memmcp/brief_draft.ctx/` — a vendored skill-bearing package.

**Modified:**
- `julep/registry.py` — `Registry.skills`, `register_skill`, `get_skill`.
- `julep/dotctx.py` — `Reasoner.skills` field, `replace()`, `_REPLACE_HANDLED_FIELDS`, minimal-layout wiring in `reasoner_from_settings`.
- `julep/dotctx_rich.py` — `_ALLOWED_SETTINGS`, `_build_reasoner`, `RichDotctx.skills`, single-file rejection.
- `julep/deploy.py` — `_reasoner_identity`.
- `julep/app.py` — `_reasoner_runtime_declaration`.
- `julep/declarations.py` — blob `skills` section, rebuild, schema version.
- `julep/execution/llm_result.py` — `LlmCallMeta.skill_loads`.
- `julep/execution/llm.py` — the disclosure loop.
- `julep/execution/openai_batch.py`, `julep/execution/anthropic_batch.py` — single-shot inlining.
- `julep/__init__.py` — public exports.
- `tests/test_memmcp_compat.py` — drop the tolerance.
- `docs-site/content/docs/internals/dotctx-format.md` — document the format.

---

### Task 1: The `Skill` value type and `SKILL.md` parser

**Files:**
- Create: `julep/skills.py`
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Skill(name: str, description: str, body: str, source: str = "")` (frozen dataclass, `source` excluded from equality); `skill_key(skill: Skill) -> str`; `parse_skill_markdown(text: str, *, origin: str) -> Skill`; `SkillError(JulepError)`; `SKILL_TOOL: str = "__load_skill__"`; `SKILL_KEY_RE: re.Pattern`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_skills.py`:

```python
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
    with pytest.raises(SkillError, match="frontmatter"):
        parse_skill_markdown("# Just a heading\n", origin="skills/x/SKILL.md")


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m pytest tests/test_skills.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'julep.skills'`

- [ ] **Step 3: Write `julep/skills.py`**

```python
"""Agent skills for dotctx packages.

A *skill* is a named block of reusable instructions living beside a dotctx
package as ``skills/<name>/SKILL.md`` — YAML frontmatter (``name``,
``description``) followed by a markdown body. A package activates skills by
name through the ``skills:`` setting; activation is explicit, so a ``skills/``
directory on its own changes nothing.

Disclosure is progressive. Only each activated skill's *name and description*
reach the system prompt; the body arrives mid-call when the model asks for it
through the reserved ``__load_skill__`` tool, which
:mod:`julep.execution.llm` resolves from the frozen release — never from the
filesystem, so replay is deterministic.

Skills are content-addressed as ``skill/<name>@v<hash12>`` over
(name, description, body). Byte-identical copies in different packages
converge on one registry entry and one copy in the deploy artifact, while an
edited body yields a different key — and because ``Reasoner.skills`` holds
those keys, an edited skill moves the reasoner identity exactly the way an
edited template already does.

This module deliberately imports neither jinja2 nor :class:`~julep.dotctx.Reasoner`:
skills work in the minimal settings-only layout, without the ``[dotctx]`` extra.
"""

from __future__ import annotations

import hashlib
import os
import re
import warnings
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from .errors import JulepError

# Reserved native tool: the LLM caller resolves a call to this from the frozen
# skill set and re-asks, rather than surfacing it to the agent loop.
SKILL_TOOL = "__load_skill__"

_HASH_PREFIX_LEN = 12
SKILL_KEY_RE = re.compile(r"^skill/(?P<name>[^@]+)@v[0-9a-f]{%d}$" % _HASH_PREFIX_LEN)

# Same frontmatter shape mem-mcp's loader and the single-file .ctx format use.
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


class SkillError(JulepError):
    """A skill sidecar or ``skills:`` declaration is malformed."""


class InertSkillsDirectoryWarning(UserWarning):
    """A package ships ``skills/`` but activates nothing."""


@dataclass(frozen=True)
class Skill:
    """One ``SKILL.md`` sidecar.

    ``source`` is diagnostics only: it is excluded from equality and from the
    content hash so identical skills in different packages are one skill.
    """

    name: str
    description: str
    body: str
    source: str = field(default="", compare=False)


def skill_key(skill: Skill) -> str:
    """The content-addressed registry key for ``skill``."""
    material = "\0".join((skill.name, skill.description, skill.body))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"skill/{skill.name}@v{digest[:_HASH_PREFIX_LEN]}"


def skill_name_of(key: str) -> str:
    """The declared name inside a registry key, for error messages."""
    match = SKILL_KEY_RE.match(key)
    if match is None:
        raise SkillError(
            f"malformed skill key {key!r}; expected 'skill/<name>@v<12 hex chars>'"
        )
    return match.group("name")


def parse_skill_markdown(text: str, *, origin: str) -> Skill:
    """Parse a ``SKILL.md``: YAML frontmatter then a markdown body."""
    import yaml

    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise SkillError(
            f"skill {origin!r} has no YAML frontmatter; a SKILL.md must open with "
            "'---', a mapping with name/description, then '---'"
        )
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except Exception as exc:
        raise SkillError(f"skill {origin!r} frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise SkillError(f"skill {origin!r} frontmatter must be a YAML mapping")

    raw_name = frontmatter.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        raise SkillError(f"skill {origin!r} frontmatter needs a non-empty name")

    raw_description = frontmatter.get("description", "")
    description = (
        raw_description if isinstance(raw_description, str) else str(raw_description)
    )
    body = match.group(2).strip()
    if not body:
        raise SkillError(
            f"skill {origin!r} has an empty body; a skill with no instructions "
            "cannot be disclosed"
        )
    return Skill(
        name=raw_name.strip(),
        description=" ".join(description.split()),
        body=body,
        source=origin,
    )
```

Add `from .skills import SkillError` is *not* needed in `errors.py`; `JulepError` already lives there (confirm with `grep -n "class JulepError" julep/errors.py`).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_skills.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add julep/skills.py tests/test_skills.py
git commit -m "feat(skills): Skill value type and SKILL.md parser"
```

---

### Task 2: Package loading with the explicit allowlist

**Files:**
- Modify: `julep/skills.py`
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: `Skill`, `SkillError`, `parse_skill_markdown` from Task 1.
- Produces: `load_package_skills(pkg_dir: str, allowlist: Optional[Sequence[str]]) -> tuple[Skill, ...]`; `parse_skills_setting(value: Any, *, origin: str) -> Optional[tuple[str, ...]]`; `InertSkillsDirectoryWarning`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_skills.py`:

```python
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
    with pytest.raises(SkillError, match="directory 'alpha'.*'not-alpha'"):
        load_package_skills(pkg, ["not-alpha"])


def test_duplicate_names_are_unresolvable(tmp_path) -> None:
    pkg = str(tmp_path)
    _write_skill(pkg, "alpha", name="alpha")
    os.makedirs(os.path.join(pkg, "skills", "alpha-copy"))
    with open(os.path.join(pkg, "skills", "alpha-copy", "SKILL.md"), "w") as fh:
        fh.write("---\nname: alpha\ndescription: dupe\n---\n\nbody\n")
    with pytest.raises(SkillError, match="directory 'alpha-copy'"):
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m pytest tests/test_skills.py -v`
Expected: FAIL — `ImportError: cannot import name 'load_package_skills'`

- [ ] **Step 3: Implement the loader**

Append to `julep/skills.py`:

```python
def parse_skills_setting(value: Any, *, origin: str) -> Optional[tuple[str, ...]]:
    """Normalize the ``skills:`` setting.

    ``None`` means the key is absent (activate nothing); ``()`` means an
    explicit empty list. Mapping items are rejected by name so per-skill
    options remain an additive change later.
    """
    if value is None:
        return None
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise SkillError(
            f"settings 'skills' in {origin!r} must be a list of skill names"
        )
    names: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise SkillError(
                f"settings 'skills' in {origin!r} must be a list of skill names; "
                f"got {item!r} (per-skill option mappings are not supported yet)"
            )
        names.append(item.strip())
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise SkillError(
            f"settings 'skills' in {origin!r} has duplicate entries: "
            + ", ".join(duplicates)
        )
    return tuple(names)


def load_package_skills(
    pkg_dir: str, allowlist: Optional[Sequence[str]]
) -> tuple[Skill, ...]:
    """Load the skills a package activates, in declaration order.

    ``allowlist`` is ``None`` when the ``skills:`` key is absent — nothing is
    activated, and a present-but-inert ``skills/`` directory warns. Every
    configured name must resolve; a skill directory must hold exactly one
    ``SKILL.md`` (level-3 bundled resources are not supported yet).
    """
    skills_dir = os.path.join(pkg_dir, "skills")
    has_dir = os.path.isdir(skills_dir)

    if allowlist is None:
        if has_dir:
            warnings.warn(
                f"dotctx package {pkg_dir!r} has a skills/ directory but no "
                "'skills:' setting, so no skill is active; list the names you "
                "want to activate",
                InertSkillsDirectoryWarning,
                stacklevel=3,
            )
        return ()
    if not allowlist:
        return ()
    if not has_dir:
        raise SkillError(
            f"dotctx package {pkg_dir!r} activates skills "
            f"({', '.join(allowlist)}) but has no skills/ directory"
        )

    by_name: dict[str, Skill] = {}
    origin_of: dict[str, str] = {}
    for entry in sorted(os.listdir(skills_dir)):
        entry_path = os.path.join(skills_dir, entry)
        if not os.path.isdir(entry_path):
            raise SkillError(
                f"{os.path.join('skills', entry)!r} in {pkg_dir!r} is not a skill "
                "directory; skills/ may contain only <name>/SKILL.md directories"
            )
        contents = sorted(os.listdir(entry_path))
        if contents != ["SKILL.md"]:
            extra = [name for name in contents if name != "SKILL.md"]
            if not extra:
                raise SkillError(
                    f"skill directory {entry!r} in {pkg_dir!r} has no SKILL.md"
                )
            raise SkillError(
                f"skill directory {entry!r} in {pkg_dir!r} contains unsupported "
                f"files: {', '.join(extra)}; only SKILL.md is read (bundled skill "
                "resources are not supported yet)"
            )
        origin = os.path.join(skills_dir, entry, "SKILL.md")
        with open(origin, "r", encoding="utf-8") as fh:
            skill = parse_skill_markdown(fh.read(), origin=origin)
        if skill.name != entry:
            raise SkillError(
                f"skill directory {entry!r} in {pkg_dir!r} declares name "
                f"{skill.name!r}; the directory name and the frontmatter name "
                "must match"
            )
        if skill.name in by_name:
            raise SkillError(
                f"skill {skill.name!r} is declared twice in {pkg_dir!r}: "
                f"directory {origin_of[skill.name]!r} and directory {entry!r}"
            )
        by_name[skill.name] = skill
        origin_of[skill.name] = entry

    missing = [name for name in allowlist if name not in by_name]
    if missing:
        raise SkillError(
            f"dotctx package {pkg_dir!r} activates unknown skills: "
            f"{', '.join(missing)} (available: {', '.join(sorted(by_name)) or 'none'})"
        )
    return tuple(by_name[name] for name in allowlist)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_skills.py -v`
Expected: PASS (23 tests)

- [ ] **Step 5: Commit**

```bash
git add julep/skills.py tests/test_skills.py
git commit -m "feat(skills): package loader with explicit allowlist and level-2 limit"
```

---

### Task 3: Registry citizenship

**Files:**
- Modify: `julep/registry.py:310-321` (the `Registry.__init__` body), and add methods after `get_renderer` (`julep/registry.py:565`)
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: `Skill`, `skill_key` from Task 1.
- Produces: `Registry.skills: dict[str, Skill]`; `Registry.register_skill(skill: Skill) -> str` returning the key; `Registry.get_skill(key: str) -> Skill`; module-level `julep.skills.register_skill(skill, *, registry=DEFAULT_REGISTRY) -> str`, `julep.skills.get_skill(key, *, registry=DEFAULT_REGISTRY) -> Skill`, and `julep.skills.skill_keys(items: Sequence[Skill | str], *, registry=DEFAULT_REGISTRY) -> tuple[str, ...]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_skills.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m pytest tests/test_skills.py -k "registry or register or skill_keys or unknown_key or converge or coexist" -v`
Expected: FAIL — `AttributeError: 'Registry' object has no attribute 'register_skill'`

- [ ] **Step 3: Implement registry support**

In `julep/registry.py`, add to the imports at the top:

```python
from .skills import Skill, skill_key
```

In `Registry.__init__` (after `self.renderer_declarations` on line 314), add:

```python
        # Content-addressed agent skills (skill/<name>@v<hash12>). Keys carry
        # their own content hash, so sharing them process-wide is safe.
        self.skills: dict[str, Skill] = {}
```

After `get_renderer` (line 569), add:

```python
    def register_skill(self, skill: Skill) -> str:
        """Register a skill under its content key and return that key.

        ``Skill`` equality ignores ``source``, so byte-identical sidecars in
        different packages register once. A genuine mismatch under one key is
        impossible (the key hashes every compared field) and is treated as a
        corrupt-input error rather than silently overwritten.
        """
        key = skill_key(skill)
        existing = self.skills.get(key)
        if existing is not None and existing != skill:
            raise ValueError(
                f"skill key {key!r} already registered with different content"
            )
        self.skills[key] = skill
        return key

    def get_skill(self, key: str) -> Skill:
        try:
            return self.skills[key]
        except KeyError as e:
            raise KeyError(
                f"unknown skill {key!r}; load its dotctx package or call "
                "register_skill()"
            ) from e
```

Then append the module-level helpers to `julep/skills.py`:

```python
def register_skill(skill: Skill, *, registry: Any = None) -> str:
    """Register ``skill`` and return its content-addressed key."""
    from .registry import DEFAULT_REGISTRY

    target = DEFAULT_REGISTRY if registry is None else registry
    return target.register_skill(skill)


def get_skill(key: str, *, registry: Any = None) -> Skill:
    """Look up a registered skill by key."""
    from .registry import DEFAULT_REGISTRY

    target = DEFAULT_REGISTRY if registry is None else registry
    return target.get_skill(key)


def skill_keys(items: Sequence[Any], *, registry: Any = None) -> tuple[str, ...]:
    """Bridge from authored ``Skill`` objects to ``Reasoner.skills`` keys.

    ``Reasoner`` is a pure value type and never touches the registry, so a
    code-first caller registers here and passes the returned keys in.
    """
    keys: list[str] = []
    for item in items:
        if isinstance(item, Skill):
            keys.append(register_skill(item, registry=registry))
        elif isinstance(item, str):
            keys.append(item)
        else:
            raise SkillError(
                f"expected a Skill or a skill key string, got {item!r}"
            )
    return tuple(keys)
```

Note the deferred `from .registry import DEFAULT_REGISTRY` inside each function: `julep/registry.py` imports `julep/skills.py` at module scope, so the reverse import must stay lazy.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_skills.py -v`
Expected: PASS (29 tests)

- [ ] **Step 5: Verify no import cycle broke anything**

Run: `uv run python -m pytest tests/test_renderer_registry.py tests/test_core.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add julep/registry.py julep/skills.py tests/test_skills.py
git commit -m "feat(skills): content-addressed skill registry"
```

---

### Task 4: `Reasoner.skills` and artifact identity

**Files:**
- Modify: `julep/dotctx.py:56-63` (`_REPLACE_HANDLED_FIELDS`), `julep/dotctx.py:183-200` (field block), `julep/dotctx.py:202-253` (`__init__`), `julep/dotctx.py:255-310` (`replace`)
- Modify: `julep/deploy.py:200-229` (`_reasoner_identity`)
- Test: `tests/test_skills_declarations.py`

**Interfaces:**
- Consumes: `SKILL_KEY_RE`, `SkillError` from Task 1.
- Produces: `Reasoner.skills: tuple[str, ...]` (keyword-only in `__init__` and `replace`); `_reasoner_identity` emits `"skills"` only when non-empty.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_skills_declarations.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m pytest tests/test_skills_declarations.py -v`
Expected: FAIL — `TypeError: Reasoner.__init__() got an unexpected keyword argument 'skills'`

- [ ] **Step 3: Add the field**

In `julep/dotctx.py`, extend `_REPLACE_HANDLED_FIELDS` (line 56) with `"skills"`:

```python
_REPLACE_HANDLED_FIELDS = frozenset(
    {
        "name", "model", "system", "reply_schema", "tools", "temperature",
        "max_rounds", "is_agent", "sub_contract", "context_scope",
        "system_render", "user_render", "max_tokens", "reasoning_effort",
        "output_retries", "require_tool_call", "response_format", "prompt_cache",
        "skills",
    }
)
```

Add the declared field after `prompt_cache` (line 200):

```python
    skills: tuple[str, ...] = ()          # content-addressed skill/<name>@v<hash> keys
```

Add the keyword-only parameter to `__init__` after `prompt_cache` (line 222):

```python
        skills: Sequence[str] = (),
```

And set it after the `prompt_cache` validation block (line 253), validating each key:

```python
        from .skills import SKILL_KEY_RE

        skill_keys_tuple = tuple(skills)
        for key in skill_keys_tuple:
            if SKILL_KEY_RE.match(key) is None:
                raise ValueError(
                    f"malformed skill key {key!r} on reasoner {name!r}; "
                    "expected 'skill/<name>@v<12 hex chars>' — pass "
                    "julep.skills.skill_keys([...]) rather than bare names"
                )
        object.__setattr__(self, "skills", skill_keys_tuple)
```

Add to `replace()`'s signature after `prompt_cache` (line 275):

```python
        skills: Sequence[str] = _KEEP,
```

and to the constructed `Reasoner` inside `replace()` (after line 303):

```python
            skills=_replacement(skills, self.skills),
```

In `julep/deploy.py`, add to `_reasoner_identity` after the `prompt_cache` clause (line 228):

```python
    if reasoner.skills:
        ident["skills"] = list(reasoner.skills)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_skills_declarations.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Verify frozen artifacts did not move**

Run: `uv run python -m pytest tests/golden tests/test_agent_and_deploy.py -q`
Expected: PASS — `_reasoner_identity` adds `skills` only when non-empty, so pre-existing artifacts hash identically.

- [ ] **Step 6: Commit**

```bash
git add julep/dotctx.py julep/deploy.py tests/test_skills_declarations.py
git commit -m "feat(skills): Reasoner.skills field and artifact identity"
```

---

### Task 5: Wire the `skills:` setting into all three package layouts

**Files:**
- Modify: `julep/dotctx_rich.py:73-97` (`_ALLOWED_SETTINGS`), `julep/dotctx_rich.py:111-128` (`RichDotctx`), `julep/dotctx_rich.py:1067-1099` (`_build_reasoner`), `julep/dotctx_rich.py:1107-1163` (single file), `julep/dotctx_rich.py:1224-1242` (rich directory)
- Modify: `julep/dotctx.py:449-505` (`reasoner_from_settings`)
- Test: `tests/test_skills_dotctx.py`

**Interfaces:**
- Consumes: `load_package_skills`, `parse_skills_setting`, `skill_keys` from Tasks 2-3.
- Produces: `RichDotctx.skills: tuple[Skill, ...]`; `skills:` accepted in `settings.yaml` for the minimal and rich directory layouts and rejected for single-file `.ctx`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_skills_dotctx.py`:

```python
"""The skills: setting across the minimal, rich, and single-file layouts."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("jinja2")

from julep.dotctx import load_dotctx
from julep.dotctx_rich import load_rich_dotctx
from julep.registry import Registry
from julep.skills import InertSkillsDirectoryWarning, SkillError, skill_key


def _skill_dir(pkg, name: str, body: str = "Do the thing.") -> None:
    path = pkg / "skills" / name
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: describes {name}\n---\n\n{body}\n",
        encoding="utf-8",
    )


def _rich_pkg(tmp_path, settings: str):
    pkg = tmp_path / "draft.ctx"
    pkg.mkdir()
    (pkg / "settings.yaml").write_text(settings, encoding="utf-8")
    (pkg / "prompt.j2").write_text(
        "<<< role:system >>>\nYou draft.\n<<< role:user >>>\nGo.\n", encoding="utf-8"
    )
    return pkg


def test_rich_package_activates_a_skill(tmp_path) -> None:
    pkg = _rich_pkg(tmp_path, "model: openai:gpt-5.5\nskills: [alpha]\n")
    _skill_dir(pkg, "alpha")
    _skill_dir(pkg, "beta")
    registry = Registry()
    rich = load_rich_dotctx(str(pkg), registry=registry, env={})
    assert [s.name for s in rich.skills] == ["alpha"]
    assert rich.reasoner.skills == (skill_key(rich.skills[0]),)
    assert rich.reasoner.skills[0] in registry.skills


def test_rich_package_with_empty_list_activates_nothing(tmp_path) -> None:
    pkg = _rich_pkg(tmp_path, "model: openai:gpt-5.5\nskills: []\n")
    _skill_dir(pkg, "alpha")
    rich = load_rich_dotctx(str(pkg), registry=Registry(), env={})
    assert rich.skills == () and rich.reasoner.skills == ()


def test_rich_package_warns_on_an_inert_skills_dir(tmp_path) -> None:
    pkg = _rich_pkg(tmp_path, "model: openai:gpt-5.5\n")
    _skill_dir(pkg, "alpha")
    with pytest.warns(InertSkillsDirectoryWarning):
        rich = load_rich_dotctx(str(pkg), registry=Registry(), env={})
    assert rich.reasoner.skills == ()


def test_rich_package_missing_skill_fails_closed(tmp_path) -> None:
    pkg = _rich_pkg(tmp_path, "model: openai:gpt-5.5\nskills: [ghost]\n")
    _skill_dir(pkg, "alpha")
    with pytest.raises(SkillError, match="ghost"):
        load_rich_dotctx(str(pkg), registry=Registry(), env={})


def test_skills_is_an_accepted_settings_key(tmp_path) -> None:
    pkg = _rich_pkg(tmp_path, "model: openai:gpt-5.5\nskills: [alpha]\n")
    _skill_dir(pkg, "alpha")
    load_rich_dotctx(str(pkg), registry=Registry(), env={})  # no unknown-key error


def test_minimal_layout_supports_skills(tmp_path) -> None:
    pkg = tmp_path / "planner"
    pkg.mkdir()
    (pkg / "settings.yaml").write_text(
        "model: openai:gpt-5.5\nsystem: You plan.\nskills: [alpha]\n", encoding="utf-8"
    )
    _skill_dir(pkg, "alpha")
    reasoner = load_dotctx(str(pkg), env={}, _registry=Registry())
    assert len(reasoner.skills) == 1
    assert reasoner.skills[0].startswith("skill/alpha@v")


def test_single_file_ctx_rejects_skills(tmp_path) -> None:
    path = tmp_path / "solo.ctx"
    path.write_text(
        "---\nmodel: openai:gpt-5.5\nskills: [alpha]\n---\nBody.\n", encoding="utf-8"
    )
    with pytest.raises(SkillError, match="single-file"):
        load_rich_dotctx(str(path), registry=Registry(), env={})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m pytest tests/test_skills_dotctx.py -v`
Expected: FAIL — `ValueError: unknown settings keys ... skills`

- [ ] **Step 3: Wire the loaders**

In `julep/dotctx_rich.py`, add `"skills",` to `_ALLOWED_SETTINGS` (after `"tools",` on line 95).

Add the import near the other `julep` imports (after line 61):

```python
from .skills import Skill, load_package_skills, parse_skills_setting
```

Add the field to `RichDotctx` (after line 128):

```python
    skills: tuple[Skill, ...] = ()
```

Give `_build_reasoner` a `skills` parameter — change its signature (line 1067) to add, after `user_render`:

```python
    skill_keys_: tuple[str, ...] = (),
```

and pass it into the constructed `Reasoner` (after line 1098):

```python
        skills=skill_keys_,
```

In `load_single_file_dotctx`, immediately after `_validate_settings_keys(settings, path)` (line 1133), add:

```python
    if parse_skills_setting(settings.get("skills"), origin=path) is not None:
        raise SkillError(
            f"single-file dotctx {path!r} cannot activate skills; skills load from "
            "<package>.ctx/skills/<name>/SKILL.md, which needs the directory layout"
        )
```

and import `SkillError` alongside the others.

In `load_rich_dotctx`, after the `tools` tuple is built (line 1222), add:

```python
    skills = load_package_skills(
        path, parse_skills_setting(settings.get("skills"), origin=path)
    )
    skill_key_tuple = tuple(registry.register_skill(skill) for skill in skills)
```

pass `skill_keys_=skill_key_tuple` into `_build_reasoner`, and add `skills=skills` to the returned `RichDotctx`.

In `julep/dotctx.py`, inside `reasoner_from_settings`, resolve skills before constructing the Reasoner (just before the `return _registry.register_reasoner(...)` at line 505 — locate the `Reasoner(` construction that begins around line 484):

```python
    from .skills import load_package_skills, parse_skills_setting

    skill_key_tuple: tuple[str, ...] = ()
    declared = parse_skills_setting(settings.get("skills"), origin=base_dir or nm)
    if base_dir is not None:
        skill_key_tuple = tuple(
            _registry.register_skill(skill)
            for skill in load_package_skills(base_dir, declared)
        )
    elif declared:
        raise ValueError(
            f"reasoner {nm!r} declares skills but was built without a base_dir; "
            "skills load from <package>/skills/<name>/SKILL.md"
        )
```

and add `skills=skill_key_tuple,` to that `Reasoner(...)` call.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_skills_dotctx.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Verify existing dotctx tests still pass**

Run: `uv run python -m pytest tests/test_dotctx_rich.py tests/test_dotctx_single_file.py tests/test_dotctx_reply.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add julep/dotctx_rich.py julep/dotctx.py tests/test_skills_dotctx.py
git commit -m "feat(skills): accept skills: in the minimal and rich dotctx layouts"
```

---

### Task 6: Ship skills in the declarations blob

**Files:**
- Modify: `julep/app.py:535-571` (`_reasoner_runtime_declaration`)
- Modify: `julep/declarations.py:23` (schema version), `julep/declarations.py:94-190` (`declarations_blob`), `julep/declarations.py:290-355` (`_reasoner_from_json`), `julep/declarations.py:418-530` (`load_declarations`)
- Test: `tests/test_skills_declarations.py`

**Interfaces:**
- Consumes: `Reasoner.skills` (Task 4), `Registry.register_skill`/`get_skill` (Task 3).
- Produces: blob key `"skills": {key: {"name", "description", "body"}}`; `_BLOB_SCHEMA_VERSION == 3`; `load_declarations` registers rebuilt skills into every target registry *and* `DEFAULT_REGISTRY`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_skills_declarations.py`:

```python
import hashlib
import json


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m pytest tests/test_skills_declarations.py -k blob -v`
Expected: FAIL — `KeyError: 'skills'` / `assert 2 == 3`

- [ ] **Step 3: Implement blob support**

In `julep/app.py`, add to the dict returned by `_reasoner_runtime_declaration` (after `"promptCache"`, line 569):

```python
        "skills": list(reasoner.skills),
```

In `julep/declarations.py`:

Bump line 23 to `_BLOB_SCHEMA_VERSION = 3`.

In `declarations_blob`, after the `renderers` loop and before the `agents` block (line 143), add:

```python
    skills: dict[str, dict[str, Any]] = {}
    for reasoner in reasoner_values.values():
        for key in reasoner.skills:
            if key in skills:
                continue
            skill = registry.skills.get(key)
            if skill is None:
                raise ApplicationDefinitionError(
                    f"reasoner {reasoner.name!r} references skill {key!r} with no "
                    "registered content; load its dotctx package before releasing"
                )
            skills[key] = {
                "name": skill.name,
                "description": skill.description,
                "body": skill.body,
            }
```

and add to the `payload` dict (after `"agents"`, line 187):

```python
        "skills": {name: skills[name] for name in sorted(skills)},
```

In `_reasoner_from_json`, read the list before constructing the Reasoner:

```python
    skills_raw = value.get("skills", [])
    if not isinstance(skills_raw, list) or not all(
        isinstance(item, str) for item in skills_raw
    ):
        _fail(f"reasoner {name!r} skills must be a list of strings")
```

and pass `skills=skills_raw,` into the returned `Reasoner(...)`.

In `load_declarations`, after the renderers are rebuilt (line 452) add the skill rebuild:

```python
    from .skills import Skill, skill_key

    skill_values = _object(payload.get("skills", {}), label="declarations skills")
    rebuilt_skills: dict[str, Skill] = {}
    for key, raw in skill_values.items():
        entry = _object(raw, label=f"skill {key!r}")
        skill = Skill(
            name=_string(entry.get("name"), label=f"skill {key!r} name"),
            description=_string(
                entry.get("description"), label=f"skill {key!r} description"
            ),
            body=_string(entry.get("body"), label=f"skill {key!r} body"),
        )
        if skill_key(skill) != key:
            _fail(f"skill {key!r} does not match the content hash of its declaration")
        rebuilt_skills[key] = skill
```

After the reasoner renderer cross-check loop (line 477), add the skill cross-check:

```python
        for skill_ref in reasoner.skills:
            if skill_ref not in rebuilt_skills:
                _fail(f"reasoner {name!r} references undeclared skill {skill_ref!r}")
```

In the conflict-detection loop over `targets` (line 484), add:

```python
        for key, skill in rebuilt_skills.items():
            existing_skill = target.skills.get(key)
            if existing_skill is not None and existing_skill != skill:
                raise ApplicationDefinitionError(
                    f"skill {key!r} conflicts with the verified application declaration"
                )
```

In the registration loop (line 509), add:

```python
        target.skills.update(rebuilt_skills)
```

And in the release-scoped global share block at the end (alongside renderers), add:

```python
    if release_scoped and registry is not DEFAULT_REGISTRY:
        # Skill keys are content-addressed like renderer names, and the LLM
        # caller resolves skill bodies from DEFAULT_REGISTRY, so share them.
        DEFAULT_REGISTRY.skills.update(rebuilt_skills)
```

Place that inside the existing `if release_scoped and registry is not DEFAULT_REGISTRY:` block rather than adding a second one.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_skills_declarations.py -v`
Expected: PASS (10 tests)

- [ ] **Step 5: Run the declarations and application suites**

Run: `uv run python -m pytest tests/test_declarations.py tests/test_application.py -q`
Expected: PASS. Any test asserting `schemaVersion == 2` must be updated to `3` — that is the intended breaking change for rc6.

- [ ] **Step 6: Commit**

```bash
git add julep/app.py julep/declarations.py tests/test_skills_declarations.py
git commit -m "feat(skills): carry skill bodies in the declarations blob (schema v3)"
```

---

### Task 7: Prompt block and tool definition

**Files:**
- Modify: `julep/skills.py`
- Test: `tests/test_llm_skills.py`

**Interfaces:**
- Consumes: `Skill` from Task 1.
- Produces: `skills_prompt_block(skills: Sequence[Skill]) -> str`; `load_skill_tool_def(skills: Sequence[Skill], *, loaded: Sequence[str]) -> dict[str, Any]`; `inline_skills_block(skills: Sequence[Skill]) -> str`; `resolve_skill_keys(keys: Sequence[str], *, registry=None) -> tuple[Skill, ...]`; `batch_system_text(system: str, keys: Sequence[str], *, registry=None) -> str`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_llm_skills.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m pytest tests/test_llm_skills.py -v`
Expected: FAIL — `ImportError: cannot import name 'skills_prompt_block'`

- [ ] **Step 3: Implement the formatters**

Append to `julep/skills.py`:

```python
def resolve_skill_keys(keys: Sequence[str], *, registry: Any = None) -> tuple[Skill, ...]:
    """Look up skill content for a reasoner's keys, in declaration order."""
    from .registry import DEFAULT_REGISTRY

    target = DEFAULT_REGISTRY if registry is None else registry
    return tuple(target.get_skill(key) for key in keys)


def skills_prompt_block(skills: Sequence[Skill]) -> str:
    """The always-present metadata block: names and descriptions only.

    This is disclosure level 1. It is a stable prefix, so it sits ahead of the
    authored system prompt where prompt caching can cover it.
    """
    lines = [
        "# Available skills",
        "",
        "Each skill below is a set of instructions you may load when it is "
        f"relevant to the task. Call the `{SKILL_TOOL}` tool with the skill's "
        "name to read its full instructions before you act on it. Load a skill "
        "only when it applies; do not mention this mechanism in your reply.",
        "",
    ]
    for skill in skills:
        lines.append(f"- **{skill.name}** — {skill.description or '(no description)'}")
    return "\n".join(lines)


def inline_skills_block(skills: Sequence[Skill]) -> str:
    """Every activated skill in full, for single-shot paths that cannot ask.

    Batch submission has no tool round trip, so disclosure collapses to
    inlining rather than silently dropping the instructions.
    """
    blocks = [
        f"## {skill.name}\nDescription: {skill.description or '(none)'}\n\n{skill.body}".strip()
        for skill in skills
    ]
    return "# Available skills\n\nUse these skills when they are relevant.\n\n" + "\n\n".join(
        blocks
    )


def load_skill_tool_def(
    skills: Sequence[Skill], *, loaded: Sequence[str] = ()
) -> dict[str, Any]:
    """The provider tool definition for ``__load_skill__``.

    The enum lists only skills that have not been disclosed yet, so a model
    cannot spend a round re-reading something already in its context.
    """
    remaining = [skill.name for skill in skills if skill.name not in set(loaded)]
    return {
        "type": "function",
        "function": {
            "name": SKILL_TOOL,
            "description": (
                "Load the full instructions for one available skill. Call this "
                "before acting when a skill applies to the task."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The skill to load.",
                        "enum": remaining,
                    }
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    }


def batch_system_text(
    system: str, keys: Sequence[str], *, registry: Any = None
) -> str:
    """System text for a single-shot batch request: skills inlined, or unchanged."""
    if not keys:
        return system
    block = inline_skills_block(resolve_skill_keys(keys, registry=registry))
    return f"{block}\n\n{system}" if system else block
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_llm_skills.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add julep/skills.py tests/test_llm_skills.py
git commit -m "feat(skills): prompt metadata block, load_skill tool def, batch inlining"
```

---

### Task 8: The disclosure loop in `complete_reasoner`

**Files:**
- Modify: `julep/execution/llm_result.py:24-42` (`LlmCallMeta`) and its `to_attrs`
- Modify: `julep/execution/llm.py:618-800` (inside `complete_reasoner`)
- Test: `tests/test_llm_skills.py`

**Interfaces:**
- Consumes: `SKILL_TOOL`, `resolve_skill_keys`, `skills_prompt_block`, `load_skill_tool_def` (Task 7); `Reasoner.skills` (Task 4).
- Produces: `LlmCallMeta.skill_loads: tuple[str, ...]` and the `llm.skill_loads` attr; `complete_reasoner` transparently resolving `__load_skill__` calls.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_llm_skills.py`:

```python
from conftest import run
from julep.execution.llm import complete_reasoner


@dataclass
class FakeFunction:
    name: str
    arguments: str


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunction


@dataclass
class FakeMessage:
    content: Optional[str] = None
    parsed: Any = None
    tool_calls: Optional[list[FakeToolCall]] = None


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]
    usage: Any = None
    model: str = "m"


def _text(content: str) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(FakeMessage(content=content))])


def _skill_call(name: str, call_id: str = "c1") -> FakeCompletion:
    return FakeCompletion(
        choices=[
            FakeChoice(
                FakeMessage(
                    tool_calls=[
                        FakeToolCall(call_id, FakeFunction(SKILL_TOOL, json.dumps({"name": name})))
                    ]
                )
            )
        ]
    )


def _registry_with(*skills: Skill) -> tuple[Registry, tuple[str, ...]]:
    reg = Registry()
    return reg, tuple(reg.register_skill(skill) for skill in skills)


def _reasoner(keys: tuple[str, ...], **kwargs: Any) -> Reasoner:
    return Reasoner(
        name="skilled",
        model="gemini:gemini-2.5-flash",   # prompt-fallback provider: one dispatch path
        system="You draft.",
        skills=list(keys),
        **kwargs,
    )


def test_descriptions_are_in_the_system_prompt_and_bodies_are_not(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return _text("done")

    run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    system = seen[0][0]["content"]
    assert "Use for alpha work." in system
    assert "ALPHA BODY" not in system
    assert system.rstrip().endswith("You draft.")


def test_skill_tool_is_offered_when_skills_are_active(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    seen: list[Any] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs.get("tools"))
        return _text("done")

    run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert [t["function"]["name"] for t in seen[0]] == [SKILL_TOOL]


def test_no_tool_and_no_block_without_skills() -> None:
    seen: list[Any] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs)
        return _text("done")

    run(complete_reasoner(_reasoner(()), "hi", acompletion=acompletion))
    assert "tools" not in seen[0]
    assert "Available skills" not in seen[0]["messages"][0]["content"]


def test_loading_a_skill_feeds_the_body_back_and_re_asks(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _text("drafted")])
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.reply == "drafted"
    assert result.meta.skill_loads == ("alpha",)
    assert result.meta.to_attrs()["llm.skill_loads"] == ["alpha"]
    tool_turns = [m for m in seen[1] if m.get("role") == "tool"]
    assert tool_turns and tool_turns[0]["content"] == "ALPHA BODY"


def test_tool_is_withdrawn_after_the_last_skill_loads(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _text("drafted")])
    seen: list[Any] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs.get("tools"))
        return next(replies)

    run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert seen[0] is not None and seen[1] is None


def test_second_skill_stays_loadable(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA, BETA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _skill_call("beta", "c2"), _text("drafted")])

    async def acompletion(**kwargs: Any) -> Any:
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.meta.skill_loads == ("alpha", "beta")


def test_unknown_skill_name_is_answered_not_raised(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("ghost"), _text("drafted")])
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.reply == "drafted"
    assert result.meta.skill_loads == ()
    tool_turn = [m for m in seen[1] if m.get("role") == "tool"][0]
    assert "ghost" in tool_turn["content"] and "alpha" in tool_turn["content"]


def test_repeated_requests_cannot_spin_forever(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    calls = 0

    async def acompletion(**kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return _skill_call("ghost", f"c{calls}")

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert calls <= 4                      # bounded, not unbounded
    assert result.meta.skill_loads == ()


def test_skill_calls_never_leak_to_the_agent_loop(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)

    async def acompletion(**kwargs: Any) -> Any:
        return _skill_call("alpha")        # never stops asking, budget closes it

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    calls = result.reply.get("tool_calls", []) if isinstance(result.reply, dict) else []
    assert all(call["tool"] != SKILL_TOOL for call in calls)
    assert result.meta.native_tool_calls == 0


def test_real_tool_name_colliding_with_the_reserved_name_is_rejected(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    tools = [{"type": "function", "function": {"name": SKILL_TOOL, "parameters": {}}}]

    async def acompletion(**kwargs: Any) -> Any:
        return _text("done")

    with pytest.raises(ValueError, match="reserved"):
        run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion, tools=tools))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m pytest tests/test_llm_skills.py -v`
Expected: FAIL — `AttributeError: 'LlmCallMeta' object has no attribute 'skill_loads'`

- [ ] **Step 3: Add the meta field**

In `julep/execution/llm_result.py`, add after `native_tool_calls` (line 36):

```python
    skill_loads: tuple[str, ...] = ()
```

and in `to_attrs`, after the existing entries, add:

```python
        if self.skill_loads:
            out["llm.skill_loads"] = list(self.skill_loads)
```

- [ ] **Step 4: Implement the loop**

In `julep/execution/llm.py`, add the imports near the other `julep` imports. `DEFAULT_REGISTRY` must be bound at module scope — `resolve_skill_keys` would otherwise resolve it lazily inside `julep.skills`, and the tests below (like `julep/prompt.py`'s renderer lookups) patch it on this module:

```python
from ..registry import DEFAULT_REGISTRY
from ..skills import (
    SKILL_TOOL,
    load_skill_tool_def,
    resolve_skill_keys,
    skills_prompt_block,
)
```

Immediately after `safe_tools, tool_name_reverse = (...)` (line 625), insert the skill state:

```python
    active_skills = (
        resolve_skill_keys(reasoner.skills, registry=DEFAULT_REGISTRY)
        if reasoner.skills
        else ()
    )
    if active_skills and any(
        tool_def.get("function", {}).get("name") == SKILL_TOOL for tool_def in safe_tools
    ):
        raise ValueError(
            f"reasoner {reasoner.name!r} grants a tool named {SKILL_TOOL!r}, which is "
            "reserved for skill disclosure; rename the tool"
        )
    system_text = reasoner.system
    if active_skills:
        block = skills_prompt_block(active_skills)
        system_text = f"{block}\n\n{reasoner.system}" if reasoner.system else block
    loaded_skills: list[str] = []
    skill_turns: list[dict[str, Any]] = []
    skill_tool_open = bool(active_skills)
    skill_error_budget = 2

    def _offering_tools() -> bool:
        return bool(safe_tools) or skill_tool_open
```

Replace all three `reasoner.system` arguments inside `call()` (lines 660, 671, 678) with `system_text`.

Inside `call()`, replace the `native_response_format` line (653) and the `has_tools` tool-attachment block (line 679) with:

```python
        offered_tools = list(safe_tools)
        if skill_tool_open:
            offered_tools.append(load_skill_tool_def(active_skills, loaded=loaded_skills))
        native_response_format = native and not offered_tools
```

```python
        if offered_tools:
            kwargs["tools"] = offered_tools
            if parallel_tool_calls is not None:
                kwargs["parallel_tool_calls"] = parallel_tool_calls
```

Also inside `call()`, append the accumulated skill turns right before the `retry_note` append (line 683):

```python
        messages.extend(skill_turns)
```

In `dispatch_once`, change the native-attempt guard (line 727) from `if not has_tools and ...` to:

```python
        if not _offering_tools() and (schema is not None or json_object) and native_ok \
                and provider not in _PROMPT_FALLBACK_PROVIDERS:
```

Replace the block from `completion = await dispatch_once()` (line 744) through the end of the `output_retries` loop (line 778) with:

```python
    pt = ct = tt = None
    cache_read = cache_creation = None

    def _accumulate(result: Any) -> None:
        nonlocal pt, ct, tt, cache_read, cache_creation
        apt, act, att = _usage_of(result)
        pt, ct, tt = _add_tokens(pt, apt), _add_tokens(ct, act), _add_tokens(tt, att)
        rcr, rcc = _cache_usage_of(result)
        cache_read = _add_tokens(cache_read, rcr)
        cache_creation = _add_tokens(cache_creation, rcc)

    def _parse(result: Any, *, expect_json: bool) -> tuple[Any, int]:
        parsed, calls = (
            parse_responses_reply(result, expect_json=expect_json)
            if is_responses_result(result)
            else _parse_completion_reply(result, expect_json=expect_json)
        )
        return _restore_tool_calls(parsed), calls

    def _skill_requests(parsed: Any) -> list[tuple[Any, Any]]:
        if not isinstance(parsed, dict):
            return []
        calls = parsed.get("tool_calls")
        if not isinstance(calls, list):
            return []
        return [
            (call.get("id"), (call.get("input") or {}).get("name"))
            for call in calls
            if isinstance(call, dict) and call.get("tool") == SKILL_TOOL
        ]

    def _drop_skill_calls(parsed: Any) -> tuple[Any, int]:
        """Skill calls are resolved here and must never reach the agent loop."""
        if not isinstance(parsed, dict) or not isinstance(parsed.get("tool_calls"), list):
            return parsed, 0
        kept = [call for call in parsed["tool_calls"] if call.get("tool") != SKILL_TOOL]
        if len(kept) == len(parsed["tool_calls"]):
            return parsed, len(kept)
        remainder = {key: item for key, item in parsed.items() if key != "tool_calls"}
        if kept:
            remainder["tool_calls"] = kept
        return (remainder or None), len(kept)

    completion = await dispatch_once()
    _accumulate(completion)
    reply, native_tool_calls = _parse(completion, expect_json=schema is not None)

    # Progressive skill disclosure: resolve __load_skill__ from the frozen skill
    # set and re-ask, inside this one call. The IR never sees these rounds, so a
    # think leaf stays a think leaf and max_rounds keeps counting task progress.
    while skill_tool_open:
        requests = _skill_requests(reply)
        if not requests:
            skill_tool_open = False
            break
        by_name = {skill.name: skill for skill in active_skills}
        skill_turns.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": SKILL_TOOL,
                            "arguments": json.dumps({"name": name}),
                        },
                    }
                    for call_id, name in requests
                ],
            }
        )
        for call_id, name in requests:
            if name in loaded_skills:
                skill_error_budget -= 1
                content = f"skill {name!r} was already provided above"
            elif name not in by_name:
                skill_error_budget -= 1
                content = (
                    f"unknown skill {name!r}; available skills are: "
                    + ", ".join(sorted(by_name))
                )
            else:
                loaded_skills.append(str(name))
                content = by_name[name].body
            skill_turns.append(
                {"role": "tool", "tool_call_id": call_id, "content": content}
            )
        if len(loaded_skills) >= len(active_skills) or skill_error_budget <= 0:
            skill_tool_open = False
        completion = await dispatch_once()
        _accumulate(completion)
        reply, native_tool_calls = _parse(completion, expect_json=schema is not None)

    reply, native_tool_calls = _drop_skill_calls(reply)

    validation_error = _final_output_schema_error(reply, native_tool_calls)
    while schema is not None and validation_error is not None and retries_used < reasoner.output_retries:
        retries_used += 1
        logger.warning(
            "reply for %s failed JSON-Schema validation (%s); re-ask %d/%d",
            reasoner.name, validation_error, retries_used, reasoner.output_retries,
        )
        completion = await dispatch_once(
            retry_note=(
                "Your previous reply was not a single valid JSON object matching "
                f"the required schema ({validation_error}). Reply again with ONLY "
                "the corrected JSON object."
            )
        )
        _accumulate(completion)
        reply, native_tool_calls = _parse(completion, expect_json=True)
        reply, native_tool_calls = _drop_skill_calls(reply)
        validation_error = _final_output_schema_error(reply, native_tool_calls)
```

Finally, add `skill_loads=tuple(loaded_skills),` to the `LlmCallMeta(...)` construction (around line 798).

Note `_drop_skill_calls` returns the count of *real* tool calls, which is what `native_tool_calls` must report; when a turn held only skill calls it returns `None` as the reply so schema validation treats it as a missing answer rather than an intermediate tool turn.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_llm_skills.py -v`
Expected: PASS (16 tests)

- [ ] **Step 6: Verify the existing LLM suites are untouched**

Run: `uv run python -m pytest tests/test_llm.py tests/test_llm_output_retries.py tests/test_llm_native_tools.py tests/test_llm_prompt_cache.py tests/test_llm_effort.py tests/test_llm_fallback_recorded.py tests/test_openai_responses.py -q`
Expected: PASS — a reasoner with no skills takes exactly the old path.

- [ ] **Step 7: Commit**

```bash
git add julep/execution/llm.py julep/execution/llm_result.py tests/test_llm_skills.py
git commit -m "feat(skills): progressive disclosure loop inside complete_reasoner"
```

---

### Task 9: Batch paths inline instead of dropping

**Files:**
- Modify: `julep/execution/openai_batch.py:55-66`
- Modify: `julep/execution/anthropic_batch.py:66-80`
- Test: `tests/test_llm_skills.py`

**Interfaces:**
- Consumes: `batch_system_text` (Task 7).
- Produces: both batch adapters emitting inlined skill bodies for skill-bearing reasoners.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_llm_skills.py`:

```python
def test_openai_batch_inlines_skill_bodies(monkeypatch) -> None:
    from julep.execution.openai_batch import OpenAIBatchProvider

    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.openai_batch.DEFAULT_REGISTRY", reg)
    reasoner = Reasoner(
        name="batched", model="openai:gpt-5.5", system="You draft.", skills=list(keys)
    )
    request = OpenAIBatchProvider().build_request("cid", reasoner, {"x": 1})
    system = request["body"]["messages"][0]["content"]
    assert "ALPHA BODY" in system and system.rstrip().endswith("You draft.")


def test_openai_batch_is_unchanged_without_skills(monkeypatch) -> None:
    from julep.execution.openai_batch import OpenAIBatchProvider

    reasoner = Reasoner(name="plain-batch", model="openai:gpt-5.5", system="You draft.")
    request = OpenAIBatchProvider().build_request("cid", reasoner, {"x": 1})
    assert request["body"]["messages"][0]["content"] == "You draft."
```

The provider classes are `OpenAIBatchProvider` (`julep/execution/openai_batch.py:26`) and `AnthropicBatchProvider` (`julep/execution/anthropic_batch.py:37`); `build_request(custom_id, reasoner, value, *, transcript=None, dispatch=None)` is the shared signature.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m pytest tests/test_llm_skills.py -k batch -v`
Expected: FAIL — the system message is `"You draft."` with no skill body.

- [ ] **Step 3: Implement**

In `julep/execution/openai_batch.py`, add the imports:

```python
from ..registry import DEFAULT_REGISTRY
from ..skills import batch_system_text
```

and replace `reasoner.system` in the `_messages(...)` call (line 61) with:

```python
                batch_system_text(reasoner.system, reasoner.skills, registry=DEFAULT_REGISTRY),
```

Make the identical change in `julep/execution/anthropic_batch.py` at its `_messages(...)` call (line 72).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_llm_skills.py -k batch -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run the batch suites**

Run: `uv run python -m pytest tests/test_anthropic_batch.py tests/test_batch_provider.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add julep/execution/openai_batch.py julep/execution/anthropic_batch.py tests/test_llm_skills.py
git commit -m "feat(skills): inline skills on the single-shot batch paths"
```

---

### Task 10: Public API surface

**Files:**
- Modify: `julep/__init__.py:201` (the `from .dotctx import (...)` block area) and the `__all__` list near line 343
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `julep.Skill`, `julep.register_skill`, `julep.get_skill`, `julep.skill_keys`, `julep.load_package_skills`, `julep.SkillError`, `julep.SKILL_TOOL`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_skills.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run python -m pytest tests/test_skills.py -k "public_exports or code_first" -v`
Expected: FAIL — `AttributeError: module 'julep' has no attribute 'Skill'`

- [ ] **Step 3: Add the exports**

In `julep/__init__.py`, next to the other submodule imports, add:

```python
from .skills import (
    SKILL_TOOL as SKILL_TOOL,
    Skill as Skill,
    SkillError as SkillError,
    get_skill as get_skill,
    load_package_skills as load_package_skills,
    register_skill as register_skill,
    skill_keys as skill_keys,
)
```

and extend `__all__` with:

```python
    "Skill", "SkillError", "SKILL_TOOL",
    "register_skill", "get_skill", "skill_keys", "load_package_skills",
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python -m pytest tests/test_skills.py -v`
Expected: PASS (31 tests)

- [ ] **Step 5: Commit**

```bash
git add julep/__init__.py tests/test_skills.py
git commit -m "feat(skills): public API exports"
```

---

### Task 11: mem-mcp compat fixture and sweep cleanup

**Files:**
- Create: `tests/fixtures/memmcp/brief_draft.ctx/settings.yaml`, `prompt.j2`, `schema.pyi`, `skills/natural-writing/SKILL.md`
- Modify: `tests/test_memmcp_compat.py:1-14` (docstring), `tests/test_memmcp_compat.py:176-209` (the sweep)
- Test: `tests/test_memmcp_compat.py`

**Interfaces:**
- Consumes: the full stack, Tasks 1-10.
- Produces: the sweep tolerance removed; a vendored skill-bearing fixture.

- [ ] **Step 1: Create the fixture**

`tests/fixtures/memmcp/brief_draft.ctx/settings.yaml`:

```yaml
# AI-ANCHOR: prompt: living brief draft agent settings
model: !? $env.get("LIVING_BRIEF_DRAFT_MODEL", "openai:chat-latest")
temperature: 1.0
reasoning_effort: medium
max_rounds: 2
output_retries: 1
skills: [natural-writing]
```

`tests/fixtures/memmcp/brief_draft.ctx/prompt.j2`:

```jinja
<<< role:system >>>
You draft a living brief.
<<< role:user >>>
Draft the brief for {{ title }}.
```

`tests/fixtures/memmcp/brief_draft.ctx/schema.pyi`:

```python
class Output:
    draft: str
```

`tests/fixtures/memmcp/brief_draft.ctx/skills/natural-writing/SKILL.md` (body trimmed, structure exact — mirrors the real sidecar):

```markdown
---
name: natural-writing
description: >
  Write like a human, not a language model. Use this skill whenever Claude is
  producing prose meant to be read by people.
---

# Natural Writing

LLM text is detectable because it regresses to the mean.

## 1. Cut the Significance Inflation

Do not stuff sentences with claims about how pivotal something is.
```

- [ ] **Step 2: Write the failing test**

Append to `tests/test_memmcp_compat.py`:

```python
# --------------------------------------------------------------------------- #
# brief_draft.ctx: the skills: setting with progressive disclosure.
# --------------------------------------------------------------------------- #
def test_brief_draft_activates_one_skill_without_inlining_it() -> None:
    from julep.prompt import get_renderer
    from julep.registry import Registry

    rich = load_rich_dotctx(
        str(FIXTURES / "brief_draft.ctx"), registry=Registry(), env={}
    )
    assert [s.name for s in rich.skills] == ["natural-writing"]
    assert rich.reasoner.skills[0].startswith("skill/natural-writing@v")
    # Disclosure is progressive: the body is not in the rendered system prompt.
    system = get_renderer(rich.reasoner.system_render)({})
    assert "Significance Inflation" not in system
    assert system.startswith("You draft a living brief.")
```

- [ ] **Step 3: Run the test to verify it passes**

Run: `uv run python -m pytest tests/test_memmcp_compat.py::test_brief_draft_activates_one_skill_without_inlining_it -v`
Expected: PASS (the stack is complete by now; this is a characterization test proving the fixture loads).

- [ ] **Step 4: Remove the sweep tolerance**

In `tests/test_memmcp_compat.py`, delete the `except` clause's tolerance (lines 196-201), leaving:

```python
        try:
            rich = load_rich_dotctx(str(path), registry=Registry(), env={})
        except Exception as exc:
            failures.append(f"{path.relative_to(_MEM_MCP_PROMPTS)}: {exc}")
            continue
```

Wrap the sweep body so the inert-directory warning does not fail a `-W error` run — add at the top of `test_sibling_repo_supported_prompts_all_load`:

```python
    # plan_sections.ctx ships skills/ with no skills: key. Under Julep's
    # explicit-activation rule that is inert and warns; the sweep only cares
    # that every package still loads.
    warnings.filterwarnings("ignore", category=InertSkillsDirectoryWarning)
```

with `import warnings` and `from julep.skills import InertSkillsDirectoryWarning` at the top of the file.

Update the module docstring's fixture inventory (lines 1-14) to mention `brief_draft.ctx` alongside the others.

- [ ] **Step 5: Run the compat suite**

Run: `uv run python -m pytest tests/test_memmcp_compat.py -v`
Expected: PASS, including `test_sibling_repo_supported_prompts_all_load` with zero tolerated failures (the sibling repo is checked out at `/home/diwank/github.com/julep-ai/mem-mcp`).

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/memmcp/brief_draft.ctx tests/test_memmcp_compat.py
git commit -m "test(skills): vendor a skill-bearing fixture and drop the sweep tolerance"
```

---

### Task 12: Documentation

**Files:**
- Modify: `docs-site/content/docs/internals/dotctx-format.md:35-50` (the layout block) and add a `### Skills` section after the `tools.pyi` section (around line 156)
- Test: `uv run python -m pytest tests/test_cookbook_examples.py -q` (docs snippets are executed by the docs runner)

**Interfaces:**
- Consumes: the finished feature.
- Produces: user-facing documentation of the format, the divergence from mem-mcp, and the programmatic API.

- [ ] **Step 1: Update the layout diagram**

In the rich-layout code block, add the `skills/` entry:

```
<name>.ctx/
├── settings.yaml        # name, model, temperature, max_rounds, agent, sub, context, tools, skills
├── schema.pyi           # input/output models -> reply_schema (JSON Schema)
├── tools.pyi            # tool stubs -> granted tool keys + expected schemas
├── skills/              # activated by settings.yaml `skills:` (see below)
│   └── <skill-name>/
│       └── SKILL.md     # YAML frontmatter (name, description) + markdown body
├── prompt.j2            # single-template form (optional <<< role:... >>> markers), OR
└── messages/            # multi-message form
```

- [ ] **Step 2: Add the Skills section**

```markdown
### `skills/` → progressive disclosure

A package may ship agent skills as `skills/<name>/SKILL.md` — YAML frontmatter
(`name`, `description`) followed by a markdown body. Activation is **explicit**:

```yaml
skills: [natural-writing]
```

- The key **absent** activates nothing (a present-but-unused `skills/`
  directory warns). `skills: []` also activates nothing, silently.
- A configured name with no matching sidecar is a load error, as is a
  directory whose name disagrees with its frontmatter `name`.
- Only `SKILL.md` is read. Any other file in a skill directory is a load
  error — bundled skill resources (`references/`, `scripts/`) are reserved.

Disclosure is progressive. Only the name and description of each activated
skill reach the system prompt; the body arrives when the model calls the
reserved `__load_skill__` tool, which the LLM caller resolves from the frozen
release and answers in place. Those round trips happen *inside* one reasoner
call: the flow shape is unchanged, `max_rounds` still counts rounds of task
progress, and skill calls never reach the agent loop. `LlmCallMeta.skill_loads`
records which skills were actually read.

Single-shot batch submission has no tool round trip, so a batched reasoner
inlines every activated skill instead.

Skills are content-addressed as `skill/<name>@v<hash12>` over
(name, description, body), and `Reasoner.skills` holds those keys — so editing
a skill body moves the reasoner identity exactly the way editing a template
does, and byte-identical copies in different packages cost one artifact entry.

**Differences from mem-mcp's `skills:`.** mem-mcp activates *all* skills when
the key is absent and inlines every body into the system prompt. Julep requires
explicit activation and discloses progressively, so a package migrating from
mem-mcp must list the names it wants.

Programmatically:

```python
from julep import Reasoner, Skill, skill_keys

house_style = Skill(
    name="house-style",
    description="How we write.",
    body="Short sentences. Concrete nouns.",
)
reasoner = Reasoner(
    name="drafter",
    model="openai:gpt-5.5",
    system="You draft release notes.",
    skills=skill_keys([house_style]),
)
```

`Reasoner` is a pure value type and never touches the registry, so
`skill_keys()` is the explicit bridge: it registers each `Skill` and returns
the content keys the reasoner stores.
```

- [ ] **Step 3: Verify the docs build and snippets run**

Run: `uv run python -m pytest tests/test_cookbook_examples.py tests/_docs_runner.py -q`
Expected: PASS (if `_docs_runner.py` is not collected directly, run only the cookbook test).

- [ ] **Step 4: Commit**

```bash
git add docs-site/content/docs/internals/dotctx-format.md
git commit -m "docs(skills): document the skills: setting and progressive disclosure"
```

---

### Task 13: Full-suite verification

**Files:** none modified — this task gates the branch.

- [ ] **Step 1: Run the whole suite**

Run: `uv run python -m pytest -q`
Expected: PASS. Per `FEEDBACK.md:288-296`, this suite has known order-dependent `DEFAULT_REGISTRY` collisions; compare against a pre-branch baseline rather than assuming a clean tree.

- [ ] **Step 2: Capture a baseline if failures appear**

```bash
git stash
uv run python -m pytest -q 2>&1 | tail -30 > /tmp/baseline.txt
git stash pop
uv run python -m pytest -q 2>&1 | tail -30 > /tmp/branch.txt
diff /tmp/baseline.txt /tmp/branch.txt
```

Expected: no *new* failures. Any new failure must be fixed before the branch lands — do not report completion with a diff here.

- [ ] **Step 3: Verify skills work without the `[dotctx]` extra**

Run: `uv run python -c "import sys; sys.modules['jinja2'] = None; import julep.skills; print(julep.skills.SKILL_TOOL)"`
Expected: prints `__load_skill__` — `julep/skills.py` must not import jinja2 transitively.

- [ ] **Step 4: Commit any fixes and finish**

```bash
git add -A
git commit -m "test(skills): full-suite verification"
```

---

## Self-Review

**Spec coverage:**
- Explicit activation, `[]` vs absent, missing-name failure, extra-file rejection, name/directory agreement, duplicate names → Tasks 2, 5.
- Package-local-only resolution, content addressing, dedupe → Tasks 1, 3.
- `Reasoner.skills`, identity, drift → Task 4.
- Frozen artifact carriage and worker rebuild → Task 6.
- Progressive disclosure, `__load_skill__`, bounded loop, no IR change → Tasks 7, 8.
- Batch degradation → Task 9.
- Programmatic API → Tasks 3, 10.
- mem-mcp migration and sweep → Task 11.
- Docs → Task 12.

**Known gaps, deliberately out of scope:**
- Relaxing `native_response_format = native and not has_tools` for providers that support tools alongside structured outputs (see "Design Decision Requiring Confirmation"). Without it, a skill-bearing reasoner's first call uses prompt-injected schema guidance.
- Level-3 bundled skill resources.
- Per-skill options (`mode: inline`) — the settings parser rejects mapping items by name so this stays additive.
- Eval reproducibility: `eval.yaml` has no way to pin disclosure behavior, so an eval over a skill-bearing package will vary with the model's load decisions. Worth a follow-up.
- Trajectory visibility: disclosure round trips appear in `LlmCallMeta.skill_loads`, not as trajectory nodes. This is the accepted cost of keeping skills out of the IR.
