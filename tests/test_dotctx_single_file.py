"""Tests for single-file ``.ctx`` loading (mem-mcp frontmatter + template body).

A single-file ``.ctx`` is mem-mcp's compact prompt form: optional YAML
frontmatter delimited by ``---`` lines, then a Jinja body that may use
``<<< role:... >>>`` markers. The frontmatter goes through the same
Yglu-aware settings path as ``settings.yaml``; the body goes through the
same role-marker splitting as ``prompt.j2``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("jinja2")

from julep.dotctx import load_dotctx
from julep.dotctx_rich import load_single_file_dotctx
from julep.prompt import get_renderer

# Mirrors mem-mcp's single-file format: frontmatter + comment header + markers.
_SINGLE_FILE = (
    "---\n"
    "name: single.episode\n"
    "model: openai/gpt-5.4-mini@low\n"
    "temperature: 0.2\n"
    "---\n"
    "{# AI-ANCHOR: prompt: single-file episode summary #}\n"
    "<<< role:system >>>\n"
    "You are an episodic summarizer.\n"
    "Persona: {{ persona }}\n"
    "\n"
    "<<< role:user >>>\n"
    "Question: {{ question }}\n"
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_frontmatter_and_role_marker_body_load(tmp_path: Path) -> None:
    p = _write(tmp_path, "episode.ctx", _SINGLE_FILE)
    b = load_dotctx(str(p))
    assert b.name == "single.episode"
    assert b.model == "openai:gpt-5.4-mini"     # canonicalized; @effort extracted
    assert b.reasoning_effort == "low"
    assert b.temperature == 0.2
    assert b.system == ""                       # templates never live on the Reasoner
    assert b.system_render is not None and b.user_render is not None
    system = get_renderer(b.system_render)({"persona": "skeptic"})
    assert system == "You are an episodic summarizer.\nPersona: skeptic"
    assert get_renderer(b.user_render)({"question": "why?"}) == "Question: why?"


def test_single_file_has_no_sidecar_surfaces(tmp_path: Path) -> None:
    # No schema.pyi / tools.pyi can ride along in a single file.
    rich = load_single_file_dotctx(str(_write(tmp_path, "episode.ctx", _SINGLE_FILE)))
    assert rich.package == "single.episode"
    assert rich.reasoner.reply_schema is None and rich.reasoner.tools == ()
    assert rich.tool_grants == () and dict(rich.expected_tool_schemas) == {}
    assert set(rich.renderer_names) == {"system", "user"}


def test_yglu_frontmatter_binds_explicit_env(tmp_path: Path) -> None:
    pytest.importorskip("yglu")
    content = (
        "---\n"
        "name: single.tagged\n"
        'model: !? $env.get("EPISODE_MODEL", "openai/gpt-5.4-nano@medium")\n'
        "---\n"
        "<<< role:system >>>\n"
        "S {{ x }}\n"
    )
    p = _write(tmp_path, "tagged.ctx", content)
    b = load_dotctx(str(p), env={"EPISODE_MODEL": "anthropic/claude-sonnet-4@high"})
    assert b.model == "anthropic:claude-sonnet-4"
    assert b.reasoning_effort == "high"


def test_no_frontmatter_is_template_only_with_defaults(tmp_path: Path) -> None:
    p = _write(tmp_path, "sf_plain.ctx", "Summarize {{ text }} briefly.\n")
    b = load_dotctx(str(p))
    assert b.name == "sf_plain"                 # filename stem without .ctx
    assert b.model == "claude-sonnet-4"         # CA default applies
    assert b.temperature is None and b.max_rounds is None
    assert b.system_render is not None and b.user_render is None
    assert get_renderer(b.system_render)({"text": "T"}) == "Summarize T briefly.\n"


def test_frontmatter_without_markers_is_system_template(tmp_path: Path) -> None:
    content = "---\nname: single.plainbody\nmodel: m\n---\nJust a body {{ x }}.\n"
    b = load_dotctx(str(_write(tmp_path, "plainbody.ctx", content)))
    assert b.name == "single.plainbody" and b.model == "m"
    assert b.system_render is not None and b.user_render is None
    assert get_renderer(b.system_render)({"x": "1"}) == "Just a body 1.\n"


def test_unknown_frontmatter_keys_error(tmp_path: Path) -> None:
    content = "---\nmodel: m\nbogus: 1\n---\nbody\n"
    p = _write(tmp_path, "sf_bogus.ctx", content)
    with pytest.raises(ValueError) as ei:
        load_dotctx(str(p))
    assert "bogus" in str(ei.value) and "sf_bogus.ctx" in str(ei.value)


def test_non_ctx_file_errors(tmp_path: Path) -> None:
    p = _write(tmp_path, "prompt.txt", "hello")
    with pytest.raises(ValueError, match=r"must end in \.ctx"):
        load_dotctx(str(p))


def test_missing_path_errors(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_dotctx(str(tmp_path / "nope.ctx"))


def test_directory_named_ctx_still_loads_as_directory(tmp_path: Path) -> None:
    pkg = tmp_path / "sf_dir.ctx"
    pkg.mkdir()
    (pkg / "settings.yaml").write_text("name: single.dirform\nmodel: m\n")
    (pkg / "prompt.j2").write_text("dir body {{ x }}")
    b = load_dotctx(str(pkg))
    assert b.name == "single.dirform"
    assert b.system_render is not None
    assert get_renderer(b.system_render)({"x": "1"}) == "dir body 1"
