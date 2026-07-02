"""Task 4: the mem-mcp eval data surface (composable_agents/dotctx_evals.py).

eval.py / eval.yaml load only through the explicit entry points
(``load_ctx_evals`` / ``load_eval_module`` / ``load_eval_config``) — never
during prompt loading. The sys.modules shim tests assert the ``dotctx``
aliases exist only for the duration of a load and never clobber a real
installed ``dotctx``. The llm_utils matrix mirrors mem-mcp's behavior
(fenced JSON, dict responses, nested ``.output`` wrappers).
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any, Optional

import pytest

from composable_agents.dotctx_evals import (
    CtxEvals,
    DatasetSpec,
    EvalConfig,
    EvalModule,
    Expected,
    ExpectedToolCall,
    MockToolConfig,
    ModelSpec,
    Sample,
    Turn,
    all_stop,
    any_stop,
    extract_llm_content,
    load_ctx_evals,
    load_eval_config,
    load_eval_module,
    parse_llm_json,
    stop_after_turns,
    stop_when_non_tool,
    stop_when_terminal_tool,
    strip_markdown_codeblock,
)

# Modeled on mem-mcp's episodic/episode_summary.ctx/eval.py: imports through
# both the `dotctx` top-level re-export and the `dotctx.eval_types` /
# `dotctx.llm_utils` submodules.
EVAL_PY = '''\
"""Fixture eval mirroring mem-mcp's episode_summary eval shape."""

from dotctx import extract_llm_content
from dotctx.eval_types import Sample
from dotctx.llm_utils import parse_llm_json


def sample(limit: int) -> list[Sample]:
    samples = [
        Sample(input={"content": "Alice met Bob."}, name="smoke", tags=["smoke"]),
        Sample(input={"content": "Longer transcript."}, name="long"),
    ]
    return samples if limit == -1 else samples[:limit]


def score(input, output, expected) -> float:
    content = extract_llm_content(output)
    return 1.0 if content else 0.0
'''

# Modeled on mem-mcp's briefs/draft.ctx/eval.yaml (minus the yglu model tag,
# covered separately).
EVAL_YAML = """\
models:
  - id: openai:chat-latest
    tags: [primary]

datasets:
  - file: eval.py
    format: py
    tags: [all]

threshold: 0.70
concurrency: 3

scoring:
  type: expected

agent:
  max_rounds: 1

profiles:
  smoke:
    datasets:
      - file: eval.py
        format: py
        tags: [smoke]
    threshold: 0.65
"""


def _write_eval_py(tmp_path: Path, source: str = EVAL_PY) -> Path:
    path = tmp_path / "eval.py"
    path.write_text(source)
    return path


def _dotctx_keys() -> set[str]:
    return {k for k in sys.modules if k == "dotctx" or k.startswith(("dotctx.", "dotctx_eval_"))}


# --------------------------------------------------------------------------- #
# load_eval_module: the sys.modules shim.
# --------------------------------------------------------------------------- #
def test_load_eval_module_via_shim(tmp_path: Path) -> None:
    em = load_eval_module(str(_write_eval_py(tmp_path)))
    assert isinstance(em, EvalModule)
    samples = em.sample(1)
    assert len(samples) == 1 and samples[0].name == "smoke"
    assert isinstance(samples[0], Sample)          # the shim hands out OUR Sample
    assert em.sample(-1)[1].tags == []
    assert em.score({}, {"content": "hi"}, None) == 1.0
    assert em.score({}, {"content": None}, None) == 0.0
    assert em.source_path == str(tmp_path / "eval.py")


def test_sys_modules_clean_after_load(tmp_path: Path) -> None:
    before = {k: sys.modules[k] for k in _dotctx_keys()}
    load_eval_module(str(_write_eval_py(tmp_path)))
    after = {k: sys.modules[k] for k in _dotctx_keys()}
    assert after == before                        # aliases + eval module restored


def test_shim_removed_even_when_eval_py_raises(tmp_path: Path) -> None:
    path = tmp_path / "eval.py"
    path.write_text("from dotctx.eval_types import Sample\nraise RuntimeError('boom')\n")
    with pytest.raises(ValueError, match=r"Failed to execute eval\.py: boom"):
        load_eval_module(str(path))
    assert not _dotctx_keys()


def test_real_dotctx_is_never_clobbered(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.ModuleType("dotctx")
    fake.extract_llm_content = lambda response: "sentinel"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "dotctx", fake)
    monkeypatch.delitem(sys.modules, "dotctx.eval_types", raising=False)
    monkeypatch.delitem(sys.modules, "dotctx.llm_utils", raising=False)
    path = tmp_path / "eval.py"
    path.write_text(
        "from dotctx import extract_llm_content\n"
        "from dotctx.eval_types import Sample\n"
        "def sample(limit):\n"
        "    return [Sample(input={'via': extract_llm_content(None)})]\n"
        "def score(input, output, expected):\n"
        "    return 1.0\n"
    )
    em = load_eval_module(str(path))
    assert sys.modules["dotctx"] is fake           # the real module stayed put
    assert em.sample(1)[0].input["via"] == "sentinel"
    assert "dotctx.eval_types" not in sys.modules  # the missing name was shimmed + restored


# --------------------------------------------------------------------------- #
# load_eval_module: teaching errors (mem-mcp's message shapes).
# --------------------------------------------------------------------------- #
def test_missing_sample_is_teaching_error(tmp_path: Path) -> None:
    path = tmp_path / "eval.py"
    path.write_text("def score(input, output, expected):\n    return 1.0\n")
    with pytest.raises(ValueError, match=r"missing required 'sample' function.*def sample\(limit"):
        load_eval_module(str(path))


def test_missing_score_is_teaching_error(tmp_path: Path) -> None:
    path = tmp_path / "eval.py"
    path.write_text("def sample(limit):\n    return []\n")
    with pytest.raises(ValueError, match=r"missing required 'score' function.*def score\(input"):
        load_eval_module(str(path))


def test_non_callable_sample_is_teaching_error(tmp_path: Path) -> None:
    path = tmp_path / "eval.py"
    path.write_text("sample = 42\ndef score(input, output, expected):\n    return 1.0\n")
    with pytest.raises(ValueError, match=r"'sample' in eval\.py is not callable"):
        load_eval_module(str(path))


def test_missing_eval_py_is_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"eval\.py not found"):
        load_eval_module(str(tmp_path / "eval.py"))


# --------------------------------------------------------------------------- #
# llm_utils port: the mem-mcp behavior matrix.
# --------------------------------------------------------------------------- #
def test_strip_markdown_codeblock_matrix() -> None:
    assert strip_markdown_codeblock('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert strip_markdown_codeblock("```\nplain\n```") == "plain"
    assert strip_markdown_codeblock("  no fences  ") == "no fences"
    assert strip_markdown_codeblock('```json{"a": 1}```') == '{"a": 1}'  # malformed one-liner


def test_extract_llm_content_matrix() -> None:
    # OpenAI-compatible object: response.choices[0].message.content
    msg = types.SimpleNamespace(content="obj")
    resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])
    assert extract_llm_content(resp) == "obj"
    # Dict shapes: direct content key, then nested choices
    assert extract_llm_content({"content": "direct"}) == "direct"
    assert extract_llm_content({"choices": [{"message": {"content": "nested"}}]}) == "nested"
    # Recursive .output wrapper (eval harness result objects)
    wrapper = types.SimpleNamespace(output={"content": "inner"})
    assert extract_llm_content(wrapper) == "inner"
    assert extract_llm_content(42) is None


def test_parse_llm_json() -> None:
    assert parse_llm_json('```json\n{"k": [1, 2]}\n```') == {"k": [1, 2]}
    assert parse_llm_json('{"k": true}') == {"k": True}
    with pytest.raises(json.JSONDecodeError):
        parse_llm_json("not json")


# --------------------------------------------------------------------------- #
# eval_types port: stop helpers and dataclass defaults.
# --------------------------------------------------------------------------- #
def _turn(tool_calls: list[dict[str, Any]] | None = None, content: Optional[str] = None) -> Turn:
    return Turn(output=None, tool_calls=tool_calls or [], tool_results=[],
                content=content, refusal=None)


def test_stop_helpers() -> None:
    assert stop_after_turns(2)(_turn(), 2)
    assert not stop_after_turns(2)(_turn(), 1)

    term = stop_when_terminal_tool("done", status="ok")
    assert term(_turn([{"name": "done", "args": {"status": "ok"}}]), 1)
    assert not term(_turn([{"name": "done", "args": {"status": "no"}}]), 1)
    assert stop_when_terminal_tool("done")(_turn([{"name": "done"}]), 1)

    non_tool = stop_when_non_tool()
    assert non_tool(_turn(), 1)
    assert not non_tool(_turn([{"name": "t"}], content="x"), 1)
    assert stop_when_non_tool(allow_text_with_tools=False)(_turn([{"name": "t"}], content="x"), 1)

    yes, no = stop_after_turns(1), stop_after_turns(9)
    assert any_stop(yes, no)(_turn(), 1) and not all_stop(yes, no)(_turn(), 1)


def test_sample_defaults_mirror_mem_mcp() -> None:
    s = Sample(input={"k": "v"})
    assert s.expected is None and s.mock_tools == {} and s.tags == [] and s.name is None
    assert s.stop_on(_turn(), 1)                   # default = stop_after_turns(1)
    assert Expected().content is None
    assert ExpectedToolCall(name="t").arguments is None
    m = MockToolConfig()
    assert m.match == [] and m.default is None and m.responses == []


# --------------------------------------------------------------------------- #
# load_eval_config: eval.yaml as data.
# --------------------------------------------------------------------------- #
def test_load_eval_config(tmp_path: Path) -> None:
    path = tmp_path / "eval.yaml"
    path.write_text(EVAL_YAML)
    cfg = load_eval_config(str(path))
    assert isinstance(cfg, EvalConfig)
    assert cfg.models == (ModelSpec(id="openai:chat-latest", tags=("primary",)),)
    assert cfg.datasets == (DatasetSpec(file=str(tmp_path / "eval.py"), format="py", tags=("all",)),)
    assert cfg.threshold == 0.70 and cfg.concurrency == 3
    assert cfg.scoring == {"type": "expected"} and cfg.agent == {"max_rounds": 1}
    # Profiles stay raw data — resolution is a runner concern (Phase 3/4).
    assert cfg.profiles["smoke"]["threshold"] == 0.65
    assert cfg.profiles["smoke"]["datasets"][0]["tags"] == ["smoke"]
    assert cfg.source_path == str(path)


def test_eval_config_defaults_and_shorthand(tmp_path: Path) -> None:
    path = tmp_path / "eval.yml"                   # .yml spelling
    path.write_text("models: [m1]\ndatasets: [cases.jsonl]\n")
    cfg = load_eval_config(str(path))
    assert cfg.models == (ModelSpec(id="m1"),)     # bare-string model
    assert cfg.datasets[0].format == "jsonl"       # format from the file suffix
    assert cfg.threshold == 0.5 and cfg.concurrency == 5
    assert cfg.scoring == {} and cfg.agent == {} and cfg.profiles == {}


def test_eval_config_unknown_key_is_teaching_error(tmp_path: Path) -> None:
    path = tmp_path / "eval.yaml"
    path.write_text("max_rounds: 3\n")
    with pytest.raises(ValueError, match=r"unknown eval\.yaml keys.*max_rounds.*allowed"):
        load_eval_config(str(path))


def test_eval_config_bad_mapping_key_is_teaching_error(tmp_path: Path) -> None:
    path = tmp_path / "eval.yaml"
    path.write_text("scoring: []\n")
    with pytest.raises(ValueError, match=r"scoring.*must be a mapping"):
        load_eval_config(str(path))


def test_eval_config_bad_model_entry_is_teaching_error(tmp_path: Path) -> None:
    path = tmp_path / "eval.yaml"
    path.write_text("models:\n  - tags: [primary]\n")
    with pytest.raises(ValueError, match=r"model.*must be a string or a mapping with an id"):
        load_eval_config(str(path))


def test_eval_config_missing_file_is_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"eval config not found"):
        load_eval_config(str(tmp_path / "eval.yaml"))


def test_eval_config_yglu_env_binding(tmp_path: Path) -> None:
    pytest.importorskip("yglu")
    path = tmp_path / "eval.yaml"
    path.write_text(
        'models:\n  - id: !? $env.get("DRAFT_MODEL", "openai:chat-latest")\n'
        "    tags: [primary]\n"
    )
    cfg = load_eval_config(str(path), env={"DRAFT_MODEL": "anthropic:claude-sonnet-4-6"})
    assert cfg.models[0].id == "anthropic:claude-sonnet-4-6"
    cfg2 = load_eval_config(str(path), env={})     # explicit empty env => defaults
    assert cfg2.models[0].id == "openai:chat-latest"


# --------------------------------------------------------------------------- #
# load_ctx_evals: the one explicit entry point; prompt loading never execs.
# --------------------------------------------------------------------------- #
def test_prompt_load_never_execs_eval_but_load_ctx_evals_does(tmp_path: Path) -> None:
    pytest.importorskip("jinja2")
    from composable_agents.dotctx_rich import load_rich_dotctx

    pkg = tmp_path / "evals-probe.ctx"
    pkg.mkdir()
    (pkg / "settings.yaml").write_text("name: evals.probe.task4\nmodel: m\n")
    marker = tmp_path / "executed.marker"
    (pkg / "eval.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n" + EVAL_PY
    )
    (pkg / "eval.yaml").write_text(EVAL_YAML)

    load_rich_dotctx(str(pkg))
    assert not marker.exists()                     # prompt loading never runs eval.py

    evals = load_ctx_evals(str(pkg))
    assert marker.exists()                         # the explicit entry point does
    assert isinstance(evals, CtxEvals)
    assert evals.eval_module is not None and evals.eval_module.sample(1)[0].name == "smoke"
    assert evals.eval_config is not None and evals.eval_config.threshold == 0.70


def test_load_ctx_evals_empty_dir(tmp_path: Path) -> None:
    pkg = tmp_path / "bare.ctx"
    pkg.mkdir()
    assert load_ctx_evals(str(pkg)) == CtxEvals(eval_module=None, eval_config=None)


def test_load_ctx_evals_requires_directory(tmp_path: Path) -> None:
    single = tmp_path / "one.ctx"
    single.write_text("hello\n")
    with pytest.raises(ValueError, match=r"\.ctx directory"):
        load_ctx_evals(str(single))
