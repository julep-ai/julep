from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("jinja2")

from julep.dotctx import load_dotctx, reasoner_to_flow
from julep.dotctx_rich import load_rich_dotctx
from julep.ir import ThinkStep
from julep.kinds import Op
from julep.prompt import get_renderer
from julep.registry import DEFAULT_REGISTRY
from conftest import run

EXAMPLE_DIR = Path(__file__).parents[1] / "examples" / "dotctx" / "issue_dedup"


def test_issue_dedup_rich_dotctx_loads_and_lowers_to_feedback() -> None:
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
    assert flow.op == Op.ITER_UP_TO
    assert flow.bound == 4
    assert flow.body is not None
    assert flow.body.op == Op.PRIM
    assert isinstance(flow.body.step, ThinkStep)
    assert flow.body.step.reasoner == "issue_dedup"


def test_issue_dedup_driver_is_keyless_no_op(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from examples import dotctx_issue_dedup

    assert run(dotctx_issue_dedup.main()) is None
