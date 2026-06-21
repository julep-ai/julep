"""Tests for the rich dotctx layout (composable_agents/dotctx_rich.py).

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

from composable_agents.capabilities import ToolGrant
from composable_agents.deploy import _reasoner_identity, _renderer_source_hashes, snapshot_from_listings
from composable_agents.dotctx import load_dotctx
from composable_agents.dotctx_rich import RichDotctx, load_rich_dotctx
from composable_agents.dsl import think
from composable_agents.errors import FreezeError
from composable_agents.execution.llm import complete_reasoner
from composable_agents.freeze import freeze
from composable_agents.prompt import get_renderer
from composable_agents.registry import DEFAULT_REGISTRY
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
    assert b.model == "openai/gpt-5.4-mini@low" # @effort suffix passes through untouched
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
    assert system == "You are a careful research agent.\nPersona: skeptic"
    user = get_renderer(rich.renderer_names["user"])({"question": "why?"})
    assert user == "Question: why?"


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
    assert get_renderer(b.system_render)({"audience": "execs"}) == "Summarize for execs."


def test_load_dotctx_detects_rich_layout() -> None:
    b = load_dotctx(str(FIXTURES / "researcher.ctx"))
    assert b == _rich().reasoner


# --------------------------------------------------------------------------- #
# Rejections.
# --------------------------------------------------------------------------- #
def test_unknown_settings_keys_error(tmp_path: Path) -> None:
    pkg = _write_pkg(
        tmp_path, "weird.ctx",
        "model: m\nreasoning_effort: low\noutput_retries: 0\n",
        {"prompt.j2": "hello"},
    )
    with pytest.raises(ValueError) as ei:
        load_dotctx(str(pkg))
    assert "output_retries" in str(ei.value) and "reasoning_effort" in str(ei.value)


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
    monkeypatch.delitem(sys.modules, "composable_agents.dotctx_rich", raising=False)
    with pytest.raises(ImportError, match=r"composable-agents\[dotctx\]"):
        importlib.import_module("composable_agents.dotctx_rich")


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

    from composable_agents.dotctx import Reasoner, register_reasoner

    register_reasoner(Reasoner(name="plain.norich", model="m", system="s"))
    plain = _reasoner_identity("plain.norich")
    assert "userRender" not in plain and "maxTokens" not in plain and "systemRender" not in plain


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
    assert out == reply
    call = rec.calls[0]
    assert call["max_tokens"] == 800 and call["temperature"] == 0.3
    msgs = call["messages"]
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "You are a careful research agent.\nPersona: skeptic"
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == "Question: why?"


def test_complete_reasoner_keeps_value_as_user_turn_without_user_render() -> None:
    rich = load_rich_dotctx(str(FIXTURES / "summarizer.ctx"))
    rec = Recorder(replies=[FakeCompletion([FakeChoice(FakeMessage(content="done"))])])
    out = run(complete_reasoner(rich.reasoner, {"audience": "execs", "text": "T"}, acompletion=rec))
    assert out == "done"
    msgs = rec.calls[0]["messages"]
    assert msgs[0]["content"] == "Summarize for execs."
    assert msgs[1]["content"] == json.dumps({"audience": "execs", "text": "T"})
