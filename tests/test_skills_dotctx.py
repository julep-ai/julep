"""The skills: setting across the minimal, rich, and single-file layouts."""

from __future__ import annotations

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


def test_single_file_ctx_rejects_null_skills(tmp_path) -> None:
    path = tmp_path / "solo.ctx"
    path.write_text(
        "---\nmodel: openai:gpt-5.5\nskills:\n---\nBody.\n", encoding="utf-8"
    )
    with pytest.raises(SkillError, match="single-file"):
        load_rich_dotctx(str(path), registry=Registry(), env={})


def test_rich_package_rejects_null_skills(tmp_path) -> None:
    pkg = _rich_pkg(tmp_path, "model: openai:gpt-5.5\nskills:\n")
    with pytest.raises(SkillError, match="must be a list of skill names"):
        load_rich_dotctx(str(pkg), registry=Registry(), env={})


def test_minimal_package_rejects_null_skills(tmp_path) -> None:
    pkg = tmp_path / "planner"
    pkg.mkdir()
    (pkg / "settings.yaml").write_text(
        "model: openai:gpt-5.5\nsystem: You plan.\nskills:\n", encoding="utf-8"
    )
    with pytest.raises(SkillError, match="must be a list of skill names"):
        load_dotctx(str(pkg), env={}, _registry=Registry())
