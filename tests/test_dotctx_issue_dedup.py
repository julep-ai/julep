from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("jinja2")

from julep.dotctx import load_dotctx, reasoner_to_flow
from julep.dotctx_rich import load_rich_dotctx
from julep.kinds import Op
from julep.prompt import get_renderer
from julep.registry import DEFAULT_REGISTRY
from conftest import run

EXAMPLE_DIR = Path(__file__).parents[1] / "examples" / "dotctx" / "issue_dedup"


def test_issue_dedup_rich_dotctx_loads_and_lowers_to_agent() -> None:
    rich = load_rich_dotctx(str(EXAMPLE_DIR))
    reasoner = rich.reasoner

    assert reasoner.name == "issue_dedup"
    assert reasoner.model == "anthropic:claude-haiku-4-5-20251001"
    assert reasoner.temperature == 0.1
    assert reasoner.max_rounds == 4
    assert reasoner.require_tool_call is True
    assert reasoner.tools == ("search_similar_posts",)
    assert tuple(grant.name for grant in rich.tool_grants) == reasoner.tools

    schema = reasoner.reply_schema
    assert schema is not None
    assert schema["required"] == ["action", "reason"]
    assert schema["properties"]["action"]["enum"] == ["create", "comment", "upvote"]

    assert reasoner.system_render is not None
    assert reasoner.user_render is not None
    for renderer_name in (reasoner.system_render, reasoner.user_render):
        assert renderer_name in DEFAULT_REGISTRY.renderers
        assert get_renderer(renderer_name)

    assert load_dotctx(str(EXAMPLE_DIR)) == reasoner
    flow = reasoner_to_flow(reasoner)
    assert flow.op == Op.APP
    assert flow.controller == "issue_dedup"
    assert flow.max_rounds == 4
    assert flow.native_tools is True
    assert flow.require_tool_call is True
    assert flow.tools == ["search_similar_posts"]


def test_issue_dedup_driver_runs_keyless_with_fakes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    module_path = EXAMPLE_DIR.parents[1] / "dotctx_issue_dedup.py"
    spec = importlib.util.spec_from_file_location("dotctx_issue_dedup", module_path)
    assert spec is not None and spec.loader is not None
    dotctx_issue_dedup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dotctx_issue_dedup)

    result = run(dotctx_issue_dedup.main())
    assert result["status"] == "done"
    assert result["output"]["action"] == "create"
    assert result["trace"][0]["ref"] == "search_similar_posts"
    assert result["trace"][0]["arguments"] == {
        "query": "Login retries fail after token refresh"
    }
