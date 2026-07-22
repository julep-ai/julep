from __future__ import annotations

from pathlib import Path

import pytest

from julep.cli.config import load_config
from julep.ctx_pipeline import CtxPipelineConfig


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
