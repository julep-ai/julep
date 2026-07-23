"""Tests for the rich dotctx layout (julep/dotctx_rich.py).

The fixture packages under ``tests/fixtures/`` mirror mem-mcp's production
layout: a system+user message bundle with schema.pyi/tools.pyi (researcher.ctx)
and a single-template package (summarizer.ctx). Both carry eval files the
loader must ignore.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pytest
import yaml

pytest.importorskip("jinja2")

from julep.capabilities import ToolGrant
from julep.deploy import _reasoner_identity, _renderer_source_hashes, snapshot_from_listings
from julep.dotctx import load_dotctx
from julep.dotctx_rich import RichDotctx, load_rich_dotctx
from julep.dsl import think
from julep.errors import FreezeError
from julep.execution.llm import complete_reasoner
from julep.freeze import freeze
from julep.prompt import get_renderer
from julep.registry import DEFAULT_REGISTRY
from conftest import run

FIXTURES = Path(__file__).parent / "fixtures"


def _rich() -> RichDotctx:
    return load_rich_dotctx(str(FIXTURES / "researcher.ctx"))


def _write_pkg(root: Path, name: str, settings: str, files: dict[str, str]) -> Path:
    pkg = root / name
    pkg.mkdir(parents=True)
    (pkg / "settings.yaml").write_text(settings)
    for rel, body in files.items():
        full = pkg / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(body)
    return pkg


# --------------------------------------------------------------------------- #
# Minimal layout regression: settings-only packages load exactly as before.
# --------------------------------------------------------------------------- #
def test_minimal_layout_unchanged(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "planner",
        "name: planner.minimal\nmodel: m\nsystem: literal\nmax_rounds: 2\n", {},
    )
    b = load_dotctx(str(pkg))
    assert b.system == "literal"
    assert b.system_render is None and b.user_render is None
    assert b.max_rounds == 2 and b.max_tokens is None


# --------------------------------------------------------------------------- #
# Rich load: bundle, schema.pyi, tools.pyi.
# --------------------------------------------------------------------------- #
def test_rich_bundle_loads_reasoner_with_renderers() -> None:
    rich = _rich()
    b = rich.reasoner
    assert b.name == "researcher"               # directory name minus .ctx
    assert b.system == ""                       # templates never live on the Reasoner
    assert b.model == "openai:gpt-5.4-mini"     # canonicalized; @effort suffix extracted
    assert b.reasoning_effort == "low"
    assert b.temperature == 0.3 and b.max_rounds == 4 and b.max_tokens == 800
    assert b.system_render == rich.renderer_names["system"]
    assert b.user_render == rich.renderer_names["user"]
    # loading again is a no-op (same reasoner, same renderers)
    again = _rich()
    assert again.reasoner == b and again.renderer_names == rich.renderer_names


def test_renderer_names_pin_template_content() -> None:
    rich = _rich()
    raw = yaml.safe_load((FIXTURES / "researcher.ctx/messages/00_system.yml").read_text())
    digest = hashlib.sha256(raw["content"].encode("utf-8")).hexdigest()[:12]
    assert rich.renderer_names["system"] == f"dotctx/researcher/system@v{digest}"
    assert rich.renderer_names["user"].startswith("dotctx/researcher/user@v")
    for name in rich.renderer_names.values():
        assert DEFAULT_REGISTRY.renderer_source_hash_of(name).startswith("renderer:")


def test_renderers_render_from_context_only() -> None:
    rich = _rich()
    system = get_renderer(rich.renderer_names["system"])({"persona": "skeptic"})
    assert system == "You are a careful research agent.\nPersona: skeptic\n"
    user = get_renderer(rich.renderer_names["user"])({"question": "why?"})
    assert user == "Question: why?\n"


def test_missing_context_variable_names_package_and_variable() -> None:
    rich = _rich()
    with pytest.raises(ValueError, match=r"researcher.*system template.*persona"):
        get_renderer(rich.renderer_names["system"])({"question": "no persona here"})


def test_schema_pyi_output_becomes_reply_schema() -> None:
    schema = _rich().reasoner.reply_schema
    assert schema is not None
    assert schema["type"] == "object"
    assert schema["required"] == ["findings", "summary"]
    finding = schema["properties"]["findings"]["items"]
    assert finding["properties"]["claim"] == {"type": "string"}
    assert finding["required"] == ["claim", "confidence"]
    assert schema["properties"]["stance"]["enum"] == ["support", "refute", "unclear"]
    assert schema["properties"]["stance"]["default"] == "unclear"
    assert schema["properties"]["caveats"] == {"anyOf": [{"type": "string"}, {"type": "null"}]}


def test_tools_pyi_grants_keys_and_expectations() -> None:
    rich = _rich()
    assert rich.reasoner.tools == ("memory/search_notes", "memory/create_note")
    assert [g.name for g in rich.tool_grants] == list(rich.reasoner.tools)
    assert all(isinstance(g, ToolGrant) for g in rich.tool_grants)

    search = rich.expected_tool_schemas["memory/search_notes"]
    assert search["required"] == ["cues"]
    assert search["properties"]["limit"]["default"] == 20
    assert search["properties"]["cues"]["description"] == "2-4 short search cues."

    note_item = rich.expected_tool_schemas["memory/create_note"]["properties"]["notes"]["items"]
    assert note_item["required"] == ["content"]   # NotRequired importance stays optional

    exp = DEFAULT_REGISTRY.tool_expectations["memory/create_note"]
    assert exp.ctx_path.endswith("researcher.ctx")


def test_single_template_package() -> None:
    rich = load_rich_dotctx(str(FIXTURES / "summarizer.ctx"))
    b = rich.reasoner
    assert b.name == "summarizer" and b.system == ""
    assert b.system_render is not None and b.user_render is None
    assert b.reply_schema is None and b.tools == () and b.max_tokens == 256
    assert get_renderer(b.system_render)({"audience": "execs"}) == "Summarize for execs.\n"


def test_load_dotctx_detects_rich_layout() -> None:
    b = load_dotctx(str(FIXTURES / "researcher.ctx"))
    assert b == _rich().reasoner


def test_rich_dotctx_reasoner_lands_in_supplied_registry(tmp_path: Path) -> None:
    # An isolated Registry must receive the reasoner alongside its renderers and
    # tool expectations. Regression for the WS5 migration that hardcoded
    # DEFAULT_REGISTRY.register_reasoner here, splitting the reasoner away from
    # the renderer names it points at (Codex PR#9, P2).
    from julep.registry import Registry

    pkg = _write_pkg(
        tmp_path, "iso.ctx", "name: iso.reasoner\nmodel: iso-model\n",
        {"prompt.j2": "hello {{ x }}"},
    )
    reg = Registry()
    rich = load_rich_dotctx(str(pkg), registry=reg)

    assert "iso.reasoner" in reg.reasoners
    assert reg.get_reasoner("iso.reasoner") is rich.reasoner
    # the reasoner's renderer resolves from the SAME registry it was loaded into
    assert rich.reasoner.system_render in reg.renderers
    # nothing leaked into the global default registry
    assert "iso.reasoner" not in DEFAULT_REGISTRY.reasoners


# --------------------------------------------------------------------------- #
# Role-marker splitting: <<< role:... >>> in prompt.j2 (mem-mcp single-file
# multi-message format). Real shape mirrors episode_summary.ctx/prompt.j2:
# jinja-comment header, a system section, then a user section whose body uses
# bare <<< / >>> heredoc delimiters that must NOT be treated as markers.
# --------------------------------------------------------------------------- #
_ROLE_MARKER_PROMPT = (
    "{# AI-ANCHOR: prompt: episode summary prompt #}\n"
    "<<< role:system >>>\n"
    "You are an episodic summarizer.\n"
    "Persona: {{ persona }}\n"
    "\n"
    "<<< role:user >>>\n"
    "Input\n"
    "<<<\n"
    "{{ question }}\n"
    ">>>\n"
)


def test_role_markers_split_prompt_into_system_and_user(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers.ctx", "name: markers.split\nmodel: m\n",
        {"prompt.j2": _ROLE_MARKER_PROMPT},
    )
    rich = load_rich_dotctx(str(pkg))
    b = rich.reasoner
    assert b.system_render is not None and b.user_render is not None
    assert set(rich.renderer_names) == {"system", "user"}
    # jinja comment header is preserved in the system source (hash covers it)
    # but renders to nothing; section bodies are stripped like mem-mcp does.
    system = get_renderer(b.system_render)({"persona": "skeptic"})
    assert system == "You are an episodic summarizer.\nPersona: skeptic"
    user = get_renderer(b.user_render)({"question": "why?"})
    assert user == "Input\n<<<\nwhy?\n>>>"


def test_role_markers_render_with_strict_undefined(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers_strict.ctx", "name: markers.strict\nmodel: m\n",
        {"prompt.j2": _ROLE_MARKER_PROMPT},
    )
    rich = load_rich_dotctx(str(pkg))
    with pytest.raises(ValueError, match=r"markers\.strict.*user template.*question"):
        get_renderer(rich.renderer_names["user"])({"persona": "no question here"})


def test_role_markers_tight_spacing_matches(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers_tight.ctx", "name: markers.tight\nmodel: m\n",
        {"prompt.j2": "<<<role:system>>>\nS {{ x }}\n<<<role:user>>>\nU {{ y }}\n"},
    )
    rich = load_rich_dotctx(str(pkg))
    assert get_renderer(rich.renderer_names["system"])({"x": "1"}) == "S 1"
    assert get_renderer(rich.renderer_names["user"])({"y": "2"}) == "U 2"


def test_role_markers_uppercase_role_matches_reference_lowering(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers_upper.ctx", "name: markers.upper\nmodel: m\n",
        {"prompt.j2": "<<< role:SYSTEM >>>\nS {{ x }}\n<<< role:USER >>>\nU {{ y }}\n"},
    )
    rich = load_rich_dotctx(str(pkg))
    assert get_renderer(rich.renderer_names["system"])({"x": "1"}) == "S 1"
    assert get_renderer(rich.renderer_names["user"])({"y": "2"}) == "U 2"


def test_role_markers_system_only(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers_sysonly.ctx", "name: markers.sysonly\nmodel: m\n",
        {"prompt.j2": "<<< role:system >>>\nJust a system prompt.\n"},
    )
    b = load_rich_dotctx(str(pkg)).reasoner
    assert b.system_render is not None and b.user_render is None
    assert get_renderer(b.system_render)({}) == "Just a system prompt."


def test_role_markers_unknown_role_errors(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers_badrole.ctx", "name: markers.badrole\nmodel: m\n",
        {"prompt.j2": "<<< role:system >>>\ns\n<<< role:assistant >>>\na\n"},
    )
    with pytest.raises(ValueError, match=r"prompt\.j2.*'assistant'"):
        load_rich_dotctx(str(pkg))


def test_role_markers_duplicate_system_errors(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers_dupsys.ctx", "name: markers.dupsys\nmodel: m\n",
        {"prompt.j2": "<<< role:system >>>\na\n<<< role:system >>>\nb\n"},
    )
    with pytest.raises(ValueError, match=r"prompt\.j2.*'system'"):
        load_rich_dotctx(str(pkg))


def test_role_markers_user_before_system_errors(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers_userfirst.ctx", "name: markers.userfirst\nmodel: m\n",
        {"prompt.j2": "<<< role:user >>>\nu\n<<< role:system >>>\ns\n"},
    )
    with pytest.raises(ValueError, match=r"prompt\.j2.*'user'"):
        load_rich_dotctx(str(pkg))


def test_role_markers_third_section_errors(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers_three.ctx", "name: markers.three\nmodel: m\n",
        {"prompt.j2": "<<< role:system >>>\ns\n<<< role:user >>>\nu\n<<< role:user >>>\nu2\n"},
    )
    with pytest.raises(ValueError, match=r"prompt\.j2.*'user'"):
        load_rich_dotctx(str(pkg))


def test_role_markers_leading_noncomment_text_errors(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "markers_leading.ctx", "name: markers.leading\nmodel: m\n",
        {"prompt.j2": "stray prose\n<<< role:system >>>\ns\n"},
    )
    with pytest.raises(ValueError, match=r"prompt\.j2.*before the first"):
        load_rich_dotctx(str(pkg))


def test_role_markers_leading_hash_comment_lines_dropped(tmp_path: Path) -> None:
    # mem-mcp's clustering/cluster_label.ctx opens with a bare `# AI-ANCHOR`
    # line before the first marker; mem-mcp discards pre-marker content, so
    # such comment headers load but never render (unlike Jinja comments they
    # would otherwise render as visible text). Real prose still errors.
    pkg = _write_pkg(
        tmp_path, "markers_hash.ctx", "name: markers.hash\nmodel: m\n",
        {"prompt.j2": "# AI-ANCHOR: prompt: header\n{# kept #}\n<<< role:system >>>\nS {{ x }}\n"},
    )
    rich = load_rich_dotctx(str(pkg))
    assert get_renderer(rich.renderer_names["system"])({"x": "1"}) == "S 1"


def test_memmcp_pure_filters_render(tmp_path: Path) -> None:
    # mem-mcp's dotctx registers custom Jinja filters (filters.py); the pure
    # ones are ported 1:1 — briefs/draft.ctx alone uses `to_json` 20+ times.
    pkg = _write_pkg(
        tmp_path, "filters.ctx", "name: markers.filters\nmodel: m\n",
        {"prompt.j2": "<<< role:system >>>\n{{ data | to_json }}\n{{ items | numbered_list }}\n"
                      "{{ note | as_xml('note') }}"},
    )
    rich = load_rich_dotctx(str(pkg))
    out = get_renderer(rich.renderer_names["system"])(
        {"data": {"k": "v"}, "items": ["a", "b"], "note": "x < y"}
    )
    assert out == '{"k": "v"}\n1. a\n2. b\n<note>x &lt; y</note>'


def test_memmcp_includes_and_file_filters_render_from_shared_root(tmp_path: Path) -> None:
    # mem-mcp's prompt_loader pins base_dir to the shared prompts root so prompt
    # families can include `partials/...` and import sibling YAML data.
    partials = tmp_path / "partials"
    partials.mkdir()
    (partials / "project_preamble.j2").write_text("Project: {{ project }}\n")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "facts.yaml").write_text("items:\n  - alpha\n  - beta\n")
    pkg = _write_pkg(
        tmp_path, "filefilters.ctx", "name: markers.filefilters\nmodel: m\n",
        {
            "prompt.j2": (
                "<<< role:system >>>\n"
                "{% include 'partials/project_preamble.j2' %}"
                "{% set facts = 'data/facts.yaml' | import_yaml %}"
                "{{ facts['items'] | bulleted_list }}\n"
                "{{ 'partials/project_preamble.j2' | import_text | trim }}"
            )
        },
    )
    rich = load_rich_dotctx(str(pkg))
    assert get_renderer(rich.renderer_names["system"])({"project": "Atlas"}) == (
        "Project: Atlas\n- alpha\n- beta\nProject: {{ project }}"
    )


def test_dependency_edits_after_load_do_not_change_render(tmp_path: Path) -> None:
    # The renderer identity hashes include/import deps at load; rendering must
    # use that same captured snapshot, or an on-disk edit after load would
    # change the prompt behind an unchanged hash (codex PR #12 P1).
    partials = tmp_path / "partials"
    partials.mkdir()
    (partials / "preamble.j2").write_text("Project: {{ project }}\n")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "facts.yaml").write_text("items:\n  - alpha\n")
    pkg = _write_pkg(
        tmp_path, "snapshot.ctx", "name: markers.snapshot\nmodel: m\n",
        {
            "prompt.j2": (
                "<<< role:system >>>\n"
                "{% include 'partials/preamble.j2' %}"
                "{% set facts = 'data/facts.yaml' | import_yaml %}"
                "{{ facts['items'] | bulleted_list }}"
            )
        },
    )
    rich = load_rich_dotctx(str(pkg))
    render = get_renderer(rich.renderer_names["system"])
    before = render({"project": "Atlas"})

    (partials / "preamble.j2").write_text("EDITED {{ project }}\n")
    (data_dir / "facts.yaml").write_text("items:\n  - edited\n")

    assert render({"project": "Atlas"}) == before == "Project: Atlas\n- alpha"


def test_dynamic_include_rejected_at_load(tmp_path: Path) -> None:
    # A non-literal include target can't be snapshotted or hashed, so it would
    # reopen the live-filesystem drift hole; refuse it loudly at load.
    pkg = _write_pkg(
        tmp_path, "dynamic.ctx", "name: markers.dynamic\nmodel: m\n",
        {"prompt.j2": "<<< role:system >>>\n{% include which %}"},
    )
    with pytest.raises(ValueError, match="dynamic"):
        load_rich_dotctx(str(pkg))


def test_variable_path_import_filter_is_render_time_error(tmp_path: Path) -> None:
    # Only literal '<path>' | import_yaml/import_text args are captured into
    # the snapshot; a variable path must not silently read the live filesystem.
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "facts.yaml").write_text("items: []\n")
    pkg = _write_pkg(
        tmp_path, "varpath.ctx", "name: markers.varpath\nmodel: m\n",
        {"prompt.j2": "<<< role:system >>>\n{% set p = 'data' + '/facts.yaml' %}{{ p | import_yaml }}"},
    )
    rich = load_rich_dotctx(str(pkg))
    with pytest.raises(ValueError, match="captured"):
        get_renderer(rich.renderer_names["system"])({})


def test_included_file_changes_renderer_name_and_hash(tmp_path: Path) -> None:
    from julep.registry import Registry

    partials = tmp_path / "partials"
    partials.mkdir()
    partial = partials / "project_preamble.j2"
    partial.write_text("Project one\n")
    pkg = _write_pkg(
        tmp_path, "hashdeps.ctx", "name: markers.hashdeps\nmodel: m\n",
        {"prompt.j2": "<<< role:system >>>\n{% include 'partials/project_preamble.j2' %}"},
    )
    reg1 = Registry()
    first = load_rich_dotctx(str(pkg), registry=reg1)
    first_name = first.renderer_names["system"]
    first_hash = reg1.renderer_source_hash_of(first_name)

    partial.write_text("Project two\n")
    reg2 = Registry()
    second = load_rich_dotctx(str(pkg), registry=reg2)
    second_name = second.renderer_names["system"]
    assert second_name != first_name
    assert reg2.renderer_source_hash_of(second_name) != first_hash


def test_prompt_without_role_markers_stays_whole_system_template(tmp_path: Path) -> None:
    # Bare <<< / >>> lines (no role:) are content, not markers: the whole file
    # remains the system template exactly as before.
    pkg = _write_pkg(
        tmp_path, "markers_none.ctx", "name: markers.none\nmodel: m\n",
        {"prompt.j2": "Input\n<<<\n{{ text }}\n>>>\n"},
    )
    b = load_rich_dotctx(str(pkg)).reasoner
    assert b.user_render is None
    assert b.system_render is not None
    assert get_renderer(b.system_render)({"text": "T"}) == "Input\n<<<\nT\n>>>\n"


# --------------------------------------------------------------------------- #
# require_tool_call / response_format settings + numeric-string coercion
# (mem-mcp census: require_tool_call in 5 prompts, response_format always
# {type: json_object}; record/execute.ctx sources max_rounds from $env).
# --------------------------------------------------------------------------- #
def test_require_tool_call_and_response_format_load(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "rtc.ctx",
        "name: rich.rtc\nmodel: m\nrequire_tool_call: true\n"
        "response_format:\n  type: json_object\n",
        {"prompt.j2": "hello"},
    )
    b = load_dotctx(str(pkg))
    assert b.require_tool_call is True
    assert b.response_format == "json_object"


def test_response_format_bad_shape_is_teaching_error(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "rtc_bad.ctx", "name: rich.rtcbad\nmodel: m\nresponse_format: json\n",
        {"prompt.j2": "hello"},
    )
    with pytest.raises(ValueError, match=r"type: json_object"):
        load_dotctx(str(pkg))


def test_yglu_numeric_string_setting_coerces(tmp_path: Path) -> None:
    pytest.importorskip("yglu")
    pkg = _write_pkg(
        tmp_path, "rounds.ctx",
        'name: rich.rounds\nmodel: m\nmax_rounds: !? $env.get("MAX_ROUNDS", 12)\n',
        {"prompt.j2": "hello"},
    )
    # env vars are strings; the yglu default stays an int — both land as int.
    assert load_dotctx(str(pkg), env={"MAX_ROUNDS": "9"}).max_rounds == 9


def test_yglu_numeric_string_default_stays_int(tmp_path: Path) -> None:
    pytest.importorskip("yglu")
    pkg = _write_pkg(
        tmp_path, "rounds_def.ctx",
        'name: rich.rounds_def\nmodel: m\nmax_rounds: !? $env.get("MAX_ROUNDS", 12)\n',
        {"prompt.j2": "hello"},
    )
    assert load_dotctx(str(pkg), env={}).max_rounds == 12


def test_non_numeric_string_setting_errors(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "rounds_bad.ctx",
        'name: rich.rounds_bad\nmodel: m\nmax_rounds: "many"\n',
        {"prompt.j2": "hello"},
    )
    with pytest.raises(ValueError, match="max_rounds"):
        load_dotctx(str(pkg))


def test_explicit_zero_rich_settings_do_not_fall_through_to_camel_case(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "zero.ctx",
        "name: rich.zero\nmodel: m\nmax_rounds: 0\nmaxRounds: 12\n"
        "max_tokens: 0\nmaxTokens: 120\noutput_retries: 0\noutputRetries: 2\n"
        "temperature: 0\n",
        {"prompt.j2": "hello"},
    )
    b = load_dotctx(str(pkg))
    assert b.max_rounds == 0
    assert b.max_tokens == 0
    assert b.output_retries == 0
    assert b.temperature == 0.0


# --------------------------------------------------------------------------- #
# Rejections.
# --------------------------------------------------------------------------- #
def test_unknown_settings_keys_error(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "weird.ctx",
        "model: m\ntop_p: 0.9\nstop: []\n",
        {"prompt.j2": "hello"},
    )
    with pytest.raises(ValueError) as ei:
        load_dotctx(str(pkg))
    assert "top_p" in str(ei.value) and "stop" in str(ei.value)


def test_bundle_rejects_extra_roles(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "fewshot.ctx", "model: m\n",
        {
            "messages/00_system.yml": "role: system\ncontent: s\n",
            "messages/01_user.yml": "role: user\ncontent: u\n",
            "messages/02_assistant.yml": "role: assistant\ncontent: a\n",
        },
    )
    with pytest.raises(ValueError, match="02_assistant"):
        load_dotctx(str(pkg))


def test_bundle_rejects_wrong_role_order(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "usersfirst.ctx", "model: m\n",
        {
            "messages/00_user.yml": "role: user\ncontent: u\n",
            "messages/01_system.yml": "role: system\ncontent: s\n",
        },
    )
    with pytest.raises(ValueError, match="00_user"):
        load_dotctx(str(pkg))


def test_both_prompt_forms_rejected(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "twoforms.ctx", "model: m\n",
        {"prompt.j2": "p", "messages/00_system.yml": "role: system\ncontent: s\n"},
    )
    with pytest.raises(ValueError, match="both prompt.j2 and messages"):
        load_dotctx(str(pkg))


def test_missing_jinja2_is_a_hard_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "jinja2", None)  # makes `import jinja2` raise
    monkeypatch.delitem(sys.modules, "julep.dotctx_rich", raising=False)
    with pytest.raises(ImportError, match=r"julep\[dotctx\]"):
        importlib.import_module("julep.dotctx_rich")


# --------------------------------------------------------------------------- #
# Renderer drift: a prompt edit changes the renderer name AND its source hash.
# --------------------------------------------------------------------------- #
def test_template_edit_moves_renderer_name_and_hash(tmp_path: Path) -> None:
    a = _write_pkg(tmp_path, "drift_a.ctx", "name: drift.a\nmodel: m\n",
                   {"prompt.j2": "version one {{ x }}"})
    b = _write_pkg(tmp_path, "drift_b.ctx", "name: drift.b\nmodel: m\n",
                   {"prompt.j2": "version two {{ x }}"})
    ra, rb = load_rich_dotctx(str(a)), load_rich_dotctx(str(b))
    na, nb = ra.reasoner.system_render, rb.reasoner.system_render
    assert na is not None and nb is not None and na != nb
    assert DEFAULT_REGISTRY.renderer_source_hash_of(na) != DEFAULT_REGISTRY.renderer_source_hash_of(nb)


# --------------------------------------------------------------------------- #
# Deploy artifact: conditional keys only; renderer hashes cover user_render.
# --------------------------------------------------------------------------- #
def test_reasoner_identity_adds_new_keys_only_when_present() -> None:
    rich = _rich()
    ident = _reasoner_identity("researcher")
    assert ident["systemRender"] == rich.reasoner.system_render
    assert ident["userRender"] == rich.reasoner.user_render
    assert ident["maxTokens"] == 800

    from julep.dotctx import Reasoner
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="plain.norich", model="m", system="s"))
    plain = _reasoner_identity("plain.norich")
    assert "userRender" not in plain and "maxTokens" not in plain and "systemRender" not in plain
    assert "requireToolCall" not in plain and "responseFormat" not in plain


def test_reasoner_identity_records_require_tool_call_and_response_format(
    tmp_path: Path,
) -> None:
    _write_pkg(
        tmp_path, "rtc_ident.ctx",
        "name: rich.rtc_ident\nmodel: m\nrequire_tool_call: true\n"
        "response_format:\n  type: json_object\n",
        {"prompt.j2": "hello"},
    )
    load_dotctx(str(tmp_path / "rtc_ident.ctx"))
    ident = _reasoner_identity("rich.rtc_ident")
    assert ident["requireToolCall"] is True
    assert ident["responseFormat"] == "json_object"


def test_renderer_source_hashes_cover_both_roles() -> None:
    rich = _rich()
    hashes = _renderer_source_hashes(think("researcher"))
    assert set(hashes) == set(rich.renderer_names.values())
    assert all(h.startswith("renderer:") for h in hashes.values())


# --------------------------------------------------------------------------- #
# Freeze: TOOL_SCHEMA_DRIFT against the recorded tools.pyi expectations.
# --------------------------------------------------------------------------- #
def _memory_snapshot(schemas: dict[str, dict[str, Any]]):
    tools = {
        key.split("/", 1)[1]: {
            "inputSchema": schema,
            "annotations": {"readOnlyHint": True, "idempotentHint": True},
        }
        for key, schema in schemas.items()
    }
    return snapshot_from_listings({"memory": tools})


def test_freeze_passes_when_served_schemas_match() -> None:
    rich = _rich()
    snap = _memory_snapshot(dict(rich.expected_tool_schemas))
    fr = freeze(think("researcher"), snap)
    assert fr.flow is not None


def test_freeze_raises_tool_schema_drift_on_mismatch() -> None:
    rich = _rich()
    served = {k: dict(v) for k, v in rich.expected_tool_schemas.items()}
    served["memory/search_notes"] = {"type": "object", "properties": {}}  # drifted
    with pytest.raises(FreezeError) as ei:
        freeze(think("researcher"), _memory_snapshot(served))
    msg = str(ei.value)
    assert "TOOL_SCHEMA_DRIFT" in msg
    assert "memory/search_notes" in msg and "'memory'" in msg
    assert "researcher.ctx" in msg


def test_freeze_tolerates_closed_object_markers_from_served_schemas() -> None:
    # Signature-derived servers (FastMCP, official-SDK function tools) always
    # emit additionalProperties: false; tools.pyi cannot express it. The drift
    # gate must treat open-vs-closed as equal — everything else still drifts.
    rich = _rich()
    served = {}
    for key, schema in rich.expected_tool_schemas.items():
        closed = json.loads(json.dumps(schema))
        closed["additionalProperties"] = False
        for prop in closed.get("properties", {}).values():
            if isinstance(prop, dict) and prop.get("type") == "object":
                prop["additionalProperties"] = False
        served[key] = closed
    fr = freeze(think("researcher"), _memory_snapshot(served))
    assert fr.flow is not None


def test_freeze_still_drifts_when_closed_served_schema_differs() -> None:
    rich = _rich()
    served = {k: dict(v) for k, v in rich.expected_tool_schemas.items()}
    served["memory/search_notes"] = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    with pytest.raises(FreezeError, match="TOOL_SCHEMA_DRIFT"):
        freeze(think("researcher"), _memory_snapshot(served))


# --------------------------------------------------------------------------- #
# LLM caller: rendered user turn + max_tokens forwarding.
# --------------------------------------------------------------------------- #
@dataclass
class FakeMessage:
    content: Optional[str] = None
    parsed: Any = None


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]


@dataclass
class Recorder:
    replies: list[FakeCompletion]
    calls: list[dict[str, Any]] = field(default_factory=list)
    _i: int = 0

    async def __call__(self, **kwargs: Any) -> FakeCompletion:
        self.calls.append(kwargs)
        reply = self.replies[self._i]
        self._i += 1
        return reply


def test_complete_reasoner_uses_rendered_user_turn_and_max_tokens() -> None:
    rich = _rich()
    reply = {"findings": [], "summary": "s"}
    rec = Recorder(replies=[FakeCompletion([FakeChoice(FakeMessage(content=json.dumps(reply)))])])
    out = run(complete_reasoner(
        rich.reasoner, {"persona": "skeptic", "question": "why?"}, acompletion=rec,
    ))
    assert out.reply == reply
    call = rec.calls[0]
    assert call["max_tokens"] == 800
    # The @low effort survives rendering, so thinking is on and temperature
    # is suppressed (mirrors the sync path's reasoning/temperature rule).
    assert call["reasoning_effort"] == "low"
    assert "temperature" not in call
    msgs = call["messages"]
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "You are a careful research agent.\nPersona: skeptic\n"
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == "Question: why?\n"


def test_complete_reasoner_keeps_value_as_user_turn_without_user_render() -> None:
    rich = load_rich_dotctx(str(FIXTURES / "summarizer.ctx"))
    rec = Recorder(replies=[FakeCompletion([FakeChoice(FakeMessage(content="done"))])])
    out = run(complete_reasoner(rich.reasoner, {"audience": "execs", "text": "T"}, acompletion=rec))
    assert out.reply == "done"
    msgs = rec.calls[0]["messages"]
    assert msgs[0]["content"] == "Summarize for execs.\n"
    assert msgs[1]["content"] == json.dumps({"audience": "execs", "text": "T"})


# --------------------------------------------------------------------------- #
# Transcript rounds: opening ask renders through the template; no trailing
# template turn; loop feedback rides the reserved key as a user turn.
# --------------------------------------------------------------------------- #
def _transcript_fixture() -> list[dict[str, Any]]:
    return [
        {"role": "user", "content": {"persona": "skeptic", "question": "why?"}},
        {
            "role": "assistant",
            "content": {"call": "memory/search_notes"},
            "tool_call_id": "call-1",
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "search_notes", "arguments": "{}"},
                }
            ],
        },
        {"role": "tool", "content": [{"note": "n1"}], "tool_call_id": "call-1"},
    ]


def test_transcript_round_renders_opening_ask_and_skips_trailing_turn() -> None:
    from julep.agent_loop import FEEDBACK_KEY  # noqa: F401 (contract under test)

    rich = _rich()
    reply = {"findings": [], "summary": "s"}
    rec = Recorder(replies=[FakeCompletion([FakeChoice(FakeMessage(content=json.dumps(reply)))])])
    run(complete_reasoner(
        rich.reasoner,
        {"input": {"persona": "skeptic", "question": "why?"}, "trace": []},
        acompletion=rec,
        transcript=_transcript_fixture(),
    ))
    messages = rec.calls[0]["messages"]
    user_turns = [m for m in messages if m["role"] == "user"]
    # Exactly one user turn: the opening ask, template-rendered (not raw JSON).
    assert len(user_turns) == 1
    assert "why?" in user_turns[0]["content"]
    assert not user_turns[0]["content"].lstrip().startswith("{")
    # Tool turns survive as native tool messages.
    assert any(m["role"] == "tool" for m in messages)
    assert messages[-1]["role"] == "tool"


def test_transcript_round_delivers_loop_feedback_as_user_turn() -> None:
    from julep.agent_loop import FEEDBACK_KEY

    rich = _rich()
    reply = {"findings": [], "summary": "s"}
    rec = Recorder(replies=[FakeCompletion([FakeChoice(FakeMessage(content=json.dumps(reply)))])])
    feedback = {"error": "final output failed JSON-Schema validation: boom"}
    run(complete_reasoner(
        rich.reasoner,
        {
            "input": {"persona": "skeptic", "question": "why?"},
            "trace": [],
            FEEDBACK_KEY: feedback,
        },
        acompletion=rec,
        transcript=_transcript_fixture(),
    ))
    messages = rec.calls[0]["messages"]
    assert messages[-1]["role"] == "user"
    assert "failed JSON-Schema validation" in messages[-1]["content"]
    # The feedback key never leaks into the rendered opening ask.
    opening = [m for m in messages if m["role"] == "user"][0]
    assert FEEDBACK_KEY not in opening["content"]
