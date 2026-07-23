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



def _write_transcript_agent(tmp_path: Path, *, context: str = "whole_session") -> Path:
    pkg = tmp_path / "looper.ctx"
    pkg.mkdir()
    (pkg / "settings.yaml").write_text(
        f"name: looper\nmodel: test:model\nagent: true\ncontext: {context}\n"
    )
    (pkg / "prompt.j2").write_text(
        "<<< role:system >>>\nYou answer questions.\n"
        "<<< role:user >>>\n{{ question }}\n"
    )
    return pkg


def test_transcript_scope_requires_context_max_tokens(tmp_path: Path) -> None:
    pkg = _write_transcript_agent(tmp_path)
    with pytest.raises(ValueError, match="no implicit transcript budget"):
        pipeline_spec_from_ctx(
            CtxPipelineConfig(name="looper", ctx=str(pkg)),
            root=tmp_path,
        )


def test_transcript_scope_budget_reaches_flow_ctx(tmp_path: Path) -> None:
    pkg = _write_transcript_agent(tmp_path)
    spec = pipeline_spec_from_ctx(
        CtxPipelineConfig(name="looper", ctx=str(pkg), context_max_tokens=8000),
        root=tmp_path,
    )
    ctx_json = spec.flow.to_json().get("ctx")
    assert ctx_json is not None
    assert ctx_json["scope"] == "whole_session"
    assert ctx_json["maxTokens"] == 8000


def test_context_max_tokens_rejected_for_local_scope(tmp_path: Path) -> None:
    pkg = tmp_path / "plain.ctx"
    pkg.mkdir()
    (pkg / "settings.yaml").write_text("name: plain\nmodel: test:model\n")
    (pkg / "prompt.j2").write_text(
        "<<< role:system >>>\nYou answer questions.\n"
        "<<< role:user >>>\n{{ question }}\n"
    )
    with pytest.raises(ValueError, match="only applies to summary/whole_session"):
        pipeline_spec_from_ctx(
            CtxPipelineConfig(name="plain", ctx=str(pkg), context_max_tokens=8000),
            root=tmp_path,
        )
