from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("jinja2")

from julep.ctx_pipeline import CtxPipelineConfig, pipeline_spec_from_ctx

FIXTURES = Path(__file__).parent / "fixtures"


def test_pipeline_spec_from_absolute_ctx() -> None:
    spec = pipeline_spec_from_ctx(
        CtxPipelineConfig(
            name="sum",
            ctx=str(FIXTURES / "summarizer.ctx"),
            lane="summary",
        ),
        root=Path("/unused"),
    )
    assert spec.name == "sum"
    assert spec.lane == "summary"
    assert spec.reasoner_names == ("summarizer",)


def test_pipeline_spec_resolves_relative_ctx() -> None:
    spec = pipeline_spec_from_ctx(
        CtxPipelineConfig(name="sum", ctx="summarizer.ctx"),
        root=FIXTURES,
    )
    assert spec.reasoner_names == ("summarizer",)

