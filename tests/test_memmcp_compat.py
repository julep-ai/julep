"""Task 5: real mem-mcp prompt fixtures + the sibling-repo compat sweep.

The fixtures under ``tests/fixtures/memmcp/`` vendor real mem-mcp prompt
content (bodies trimmed, structure exact): ``episode_summary.ctx`` (jinja
comment header, role markers, Input-only schema.pyi, yglu model, eval.py),
``execute.ctx`` (require_tool_call + yglu max_rounds + tools.pyi + eval.yaml),
``cluster_label.ctx`` (``response_format: {type: json_object}`` and a bare
``#`` header line before the first role marker), and ``anchor_choose.ctx``
(mem-mcp's single-file frontmatter format). ``{% include %}`` partials are
trimmed out — CA renders templates without a filesystem loader.

The sweep test loads every ``.ctx`` under the sibling mem-mcp checkout's
``apps/memory-api/prompts`` and is skipped when that repo is absent.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("jinja2")
pytest.importorskip("yglu")  # the vendored settings carry `!?` env expressions

from composable_agents.dotctx import load_dotctx
from composable_agents.dotctx_evals import Sample, load_ctx_evals
from composable_agents.dotctx_rich import load_rich_dotctx
from composable_agents.prompt import get_renderer
from composable_agents.registry import Registry

FIXTURES = Path(__file__).parent / "fixtures" / "memmcp"

_MEM_MCP_REPO = "/home/diwank/github.com/julep-ai/mem-mcp"
_MEM_MCP_PROMPTS = os.path.join(_MEM_MCP_REPO, "apps", "memory-api", "prompts")


# --------------------------------------------------------------------------- #
# episode_summary.ctx: yglu model, role markers, Input-only schema.pyi.
# --------------------------------------------------------------------------- #
def test_episode_summary_loads_canonical_model_and_split() -> None:
    b = load_dotctx(str(FIXTURES / "episode_summary.ctx"), env={})
    assert b.name == "episode_summary"
    assert b.model == "openai:gpt-5.4-nano"     # yglu default; canonicalized
    assert b.reasoning_effort == "medium"       # explicit key (agrees with @suffix)
    assert b.temperature == 0.2
    assert b.reply_schema is None               # Input-only schema.pyi: no reply contract
    assert b.system == "" and b.system_render is not None and b.user_render is not None
    system = get_renderer(b.system_render)({})
    assert system.startswith("You are an episodic summarizer.")
    # Bare <<< / >>> heredoc fences in the user body are content, not markers.
    user = get_renderer(b.user_render)({"content": "Alice met Bob.", "background": ""})
    assert "Alice met Bob." in user and "<<<" in user and ">>>" in user


def test_episode_summary_env_overrides_model() -> None:
    # Fresh registry: same package name, different config than the env={} load.
    rich = load_rich_dotctx(
        str(FIXTURES / "episode_summary.ctx"),
        registry=Registry(),
        env={"SUMMARY_MODEL": "anthropic/claude-sonnet-4@high"},
    )
    assert rich.reasoner.model == "anthropic:claude-sonnet-4"
    assert rich.reasoner.reasoning_effort == "medium"  # explicit key beats @suffix


# --------------------------------------------------------------------------- #
# execute.ctx: require_tool_call, yglu max_rounds, tools.pyi grants.
# --------------------------------------------------------------------------- #
def test_execute_require_tool_call_and_yglu_max_rounds() -> None:
    b = load_dotctx(str(FIXTURES / "execute.ctx"), env={})
    assert b.require_tool_call is True
    assert b.max_rounds == 12                   # yglu default stays int
    assert b.model == "openai:gpt-5.5" and b.reasoning_effort == "low"
    assert b.temperature == 0.3 and b.output_retries == 1
    assert b.tools == ("search_episodes", "create_episodes")
    assert b.system_render is not None and b.user_render is not None


# --------------------------------------------------------------------------- #
# cluster_label.ctx: response_format json_object + bare-# header line.
# --------------------------------------------------------------------------- #
def test_cluster_label_response_format_and_bare_hash_header() -> None:
    b = load_dotctx(str(FIXTURES / "cluster_label.ctx"), env={})
    assert b.response_format == "json_object"
    assert b.max_tokens == 120 and b.temperature == 0.2
    assert b.model == "openai:gpt-5.4-mini" and b.reasoning_effort == "none"
    assert b.reply_schema is None               # Input-only schema.pyi
    # The bare `# AI-ANCHOR` line before the first marker is a comment header:
    # mem-mcp discards pre-marker content, so it must not render.
    system = get_renderer(b.system_render)({})
    assert "AI-ANCHOR" not in system
    assert system.startswith("You label a cluster")
    user = get_renderer(b.user_render)(
        {"member_count": 2, "members": [
            {"source_type": "entity", "name": "Atlas", "content": ""},
            {"source_type": "episode", "name": "rollout review", "content": "notes"},
        ]}
    )
    assert "Cluster size: 2" in user and "[episode] rollout review: notes" in user


# --------------------------------------------------------------------------- #
# anchor_choose.ctx: the single-file frontmatter format.
# --------------------------------------------------------------------------- #
def test_anchor_choose_single_file_frontmatter_and_defaults() -> None:
    b = load_dotctx(str(FIXTURES / "anchor_choose.ctx"), env={})
    assert b.name == "anchor_choose"            # filename stem without .ctx
    assert b.model == "claude-sonnet-4"         # no model key: CA default applies
    assert b.temperature == 0.1 and b.reasoning_effort == "low"
    assert b.max_rounds == 1 and b.output_retries == 1
    system = get_renderer(b.system_render)(
        {"brief_title": "Acme renewal", "brief_kind": "playbook",
         "entity_candidates_json": "[]"}
    )
    assert "Acme renewal" in system
    user = get_renderer(b.user_render)({})
    assert user == "Choose the hidden primary anchor for this brief."


# --------------------------------------------------------------------------- #
# Eval loading is explicit: prompt loading never executes eval.py.
# --------------------------------------------------------------------------- #
def test_prompt_loading_never_executes_eval() -> None:
    # The fixture eval.py imports `dotctx`, which only exists inside the
    # explicit loader's sys.modules shim — executing it during prompt loading
    # would raise. Also assert the shim never leaks out of a prompt load.
    before = {name: sys.modules[name] for name in sys.modules if name.startswith("dotctx")}
    load_rich_dotctx(str(FIXTURES / "episode_summary.ctx"), registry=Registry(), env={})
    after = {name: sys.modules[name] for name in sys.modules if name.startswith("dotctx")}
    assert after == before
    assert not any(name.startswith("dotctx_eval_") for name in sys.modules)


def test_load_ctx_evals_episode_summary_module() -> None:
    evals = load_ctx_evals(str(FIXTURES / "episode_summary.ctx"))
    assert evals.eval_config is None            # no eval.yaml in this package
    assert evals.eval_module is not None
    samples = evals.eval_module.sample(-1)
    assert [s.name for s in samples] == ["meeting_with_context", "empty_background"]
    assert all(isinstance(s, Sample) for s in samples)
    assert samples[0].tags == ["smoke"]

    good = {"choices": [{"message": {"content": json.dumps(
        {"summary": "Alice met Bob at the London office to review the Atlas rollout."}
    )}}]}
    expected = {"must_contain": ["Alice", "Bob", "London", "Atlas", "rollout"],
                "max_words": 150}
    assert evals.eval_module.score(samples[0].input, good, expected) == 1.0
    assert evals.eval_module.score(samples[0].input, {"content": "not json"}, expected) == 0.0
    # The shim is gone again after the explicit load.
    assert "dotctx" not in sys.modules


def test_load_ctx_evals_execute_eval_yaml() -> None:
    evals = load_ctx_evals(str(FIXTURES / "execute.ctx"), env={})
    assert evals.eval_module is None            # no eval.py in this package
    cfg = evals.eval_config
    assert cfg is not None
    assert [m.id for m in cfg.models] == ["openai/gpt-5.5@low"]  # yglu default, raw
    assert cfg.models[0].tags == ("primary",)
    assert cfg.datasets[0].file.endswith("eval.py") and cfg.datasets[0].format == "py"
    assert cfg.threshold == 0.70 and cfg.concurrency == 3
    assert cfg.scoring == {"type": "expected"} and cfg.agent == {"max_rounds": 6}
    assert set(cfg.profiles) == {"smoke"}       # profiles stay raw override data
    assert cfg.profiles["smoke"]["threshold"] == 0.65


# --------------------------------------------------------------------------- #
# Sibling-repo sweep: every real prompt in mem-mcp must load.
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(
    not os.path.isdir(_MEM_MCP_REPO), reason="sibling mem-mcp repo not checked out"
)
def test_sibling_repo_prompts_all_load() -> None:
    ctx_paths = sorted(Path(_MEM_MCP_PROMPTS).rglob("*.ctx"))
    # Directories holding only a stale __pycache__ (leftovers of deleted
    # prompts) carry no settings.yaml and are not loadable packages.
    live = [
        p for p in ctx_paths
        if p.is_file() or any((p / fn).exists() for fn in ("settings.yaml", "settings.yml"))
    ]
    assert len(live) >= 25                      # 28 tracked as of 2026-07-01

    failures: list[str] = []
    for path in live:
        # Fresh registry per package: threads/ and topics/ both ship a
        # `merge_evaluator` with different configs, and register_reasoner
        # (deliberately) rejects same-name re-registration with a different
        # config. Eval modules are NOT loaded here — arbitrary code; the
        # fixture tests above cover eval loading.
        try:
            rich = load_rich_dotctx(str(path), registry=Registry(), env={})
        except Exception as exc:
            failures.append(f"{path.relative_to(_MEM_MCP_PROMPTS)}: {exc}")
            continue
        b = rich.reasoner
        assert b.system == ""                   # templates never live on the Reasoner
        assert "system" in rich.renderer_names  # every mem-mcp prompt has a system body
        assert "@" not in b.model               # effort suffix extracted, never leaks

    assert not failures, "mem-mcp prompts failed to load:\n" + "\n".join(failures)
