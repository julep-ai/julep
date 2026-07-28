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
SKILL_KEY_RE = re.compile(r"^skill/(?P<name>[^@]+)@v[0-9a-f]{%d}$" % _HASH_PREFIX_LEN)  # noqa: UP031

# Same frontmatter shape mem-mcp's loader and the single-file .ctx format use.
_FRONTMATTER_RE = re.compile(
    r"^---[ \t]*\n(.*?)^---[ \t]*\n(.*)$", re.DOTALL | re.MULTILINE
)


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

    text = text.removeprefix("\ufeff")
    # Normalize checkout line endings so Windows and Unix content hashes agree.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
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
        by_name[skill.name] = skill

    missing = [name for name in allowlist if name not in by_name]
    if missing:
        raise SkillError(
            f"dotctx package {pkg_dir!r} activates unknown skills: "
            f"{', '.join(missing)} (available: {', '.join(sorted(by_name)) or 'none'})"
        )
    return tuple(by_name[name] for name in allowlist)


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
