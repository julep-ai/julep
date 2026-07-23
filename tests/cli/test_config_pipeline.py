from __future__ import annotations

from pathlib import Path

import pytest

from julep.cli.config import load_config
from julep.ctx_pipeline import CtxPipelineConfig
from julep.execution.policy import ExecutionPolicy


def test_ctx_pipeline_config_parses(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """\
[tool.julep.pipeline.foo]
ctx = "prompts/foo.ctx"
lane = "summary"

[tool.julep.pipeline.foo.env]
MODEL = "small"
""",
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.pipelines["foo"] == CtxPipelineConfig(
        name="foo",
        ctx="prompts/foo.ctx",
        lane="summary",
        env={"MODEL": "small"},
    )


def test_ctx_pipeline_unknown_key_has_hint(tmp_path: Path) -> None:
    (tmp_path / "julep.toml").write_text(
        '[pipeline.foo]\nctx = "foo.ctx"\nlan = "summary"\n', encoding="utf-8"
    )
    with pytest.raises(ValueError, match=r"unknown key 'lan'.*did you mean 'lane'"):
        load_config(tmp_path)


@pytest.mark.parametrize("ctx", ["", "   "])
def test_ctx_pipeline_requires_nonempty_ctx(tmp_path: Path, ctx: str) -> None:
    (tmp_path / "julep.toml").write_text(
        f'[pipeline.foo]\nctx = "{ctx}"\n', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="pipeline 'foo'.*ctx"):
        load_config(tmp_path)


def test_julep_toml_overlays_pipeline_per_name(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.julep.pipeline.foo]\nctx = "base.ctx"\nlane = "base"\n',
        encoding="utf-8",
    )
    (tmp_path / "julep.toml").write_text(
        '[pipeline.foo]\nlane = "override"\n', encoding="utf-8"
    )
    pipeline = load_config(tmp_path).pipelines["foo"]
    assert pipeline.ctx == "base.ctx"
    assert pipeline.lane == "override"


def test_pipeline_without_policy_is_none(tmp_path: Path) -> None:
    (tmp_path / "julep.toml").write_text(
        '[pipeline.foo]\nctx = "foo.ctx"\n', encoding="utf-8"
    )
    assert load_config(tmp_path).pipelines["foo"].policy is None


def test_pipeline_policy_parses_onto_execution_policy(tmp_path: Path) -> None:
    (tmp_path / "julep.toml").write_text(
        """\
[pipeline.episode_summary]
ctx = "episode_summary.ctx"
lane = "summary"

[pipeline.episode_summary.policy]
reasoner_max_attempts = 1
reasoner_timeout_s = 300
""",
        encoding="utf-8",
    )
    policy = load_config(tmp_path).pipelines["episode_summary"].policy
    assert policy == ExecutionPolicy(reasoner_max_attempts=1, reasoner_timeout_s=300)


def test_pipeline_policy_rejects_unknown_key(tmp_path: Path) -> None:
    (tmp_path / "julep.toml").write_text(
        '[pipeline.foo]\nctx = "foo.ctx"\n\n[pipeline.foo.policy]\nreasoner_max_attempt = 1\n',
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match=r"unknown key 'reasoner_max_attempt' in pipeline 'foo' policy.*did you mean",
    ):
        load_config(tmp_path)


@pytest.mark.parametrize(
    "line",
    ['reasoner_max_attempts = "x"', "reasoner_max_attempts = 0", "reasoner_max_attempts = true"],
)
def test_pipeline_policy_rejects_bad_value(tmp_path: Path, line: str) -> None:
    (tmp_path / "julep.toml").write_text(
        f'[pipeline.foo]\nctx = "foo.ctx"\n\n[pipeline.foo.policy]\n{line}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"policy 'reasoner_max_attempts' must be an integer"):
        load_config(tmp_path)


def test_pipeline_tool_bindings_agent_cap_and_mcp_preflight_parse(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """\
[tool.julep]
agent_round_cap = 19

[tool.julep.mcp]
preflight = "names"

[tool.julep.pipeline.issue_dedup]
ctx = "issue_dedup.ctx"

[tool.julep.pipeline.issue_dedup.tools]
search_similar_posts = "tracker:search-similar-posts"
""",
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.agent_round_cap == 19
    assert cfg.mcp_preflight == "names"
    assert cfg.pipelines["issue_dedup"].tools == {
        "search_similar_posts": "tracker:search-similar-posts"
    }
