from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("jinja2")

from julep.cli.main import main


def _write_eval_ctx(root: Path) -> Path:
    ctx = root / "case.ctx"
    ctx.mkdir()
    (ctx / "settings.yaml").write_text('model: "openai/gpt-test"\n', encoding="utf-8")
    (ctx / "prompt.j2").write_text(
        "<<< role:system >>>\nTest.\n\n<<< role:user >>>\n{{ task }}\n",
        encoding="utf-8",
    )
    (ctx / "eval.yaml").write_text(
        "threshold: 0.5\n\ndatasets:\n  - file: eval.py\n    format: py\n",
        encoding="utf-8",
    )
    (ctx / "eval.py").write_text(
        """\
from dotctx.eval_types import Sample

def sample(limit=-1):
    return [Sample(name="caller", input={"task": "x"}, expected="good")]

def score(_input, output, expected):
    return 1.0 if output.get("content") == expected else 0.0
""",
        encoding="utf-8",
    )
    return ctx


def test_eval_llm_caller_flag_config_default_and_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ctx = _write_eval_ctx(tmp_path)
    (tmp_path / "callers.py").write_text(
        """\
async def good(reasoner, value, principal, transcript, dispatch):
    return "good"

async def bad(reasoner, value, principal, transcript, dispatch):
    return "bad"
""",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    assert main(["eval", str(ctx), "--llm-caller", "callers:good"]) == 0
    assert "PASS" in capsys.readouterr().out

    (tmp_path / "pyproject.toml").write_text(
        '[tool.julep]\nllm_caller = "callers:good"\n', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    assert main(["eval", str(ctx)]) == 0
    assert "PASS" in capsys.readouterr().out

    (tmp_path / "pyproject.toml").write_text(
        '[tool.julep]\nllm_caller = "callers:bad"\n', encoding="utf-8"
    )
    assert main(["eval", str(ctx), "--llm-caller", "callers:good"]) == 0
    assert "PASS" in capsys.readouterr().out


def test_bad_eval_llm_caller_is_setup_error(tmp_path: Path) -> None:
    ctx = _write_eval_ctx(tmp_path)
    assert main(["eval", str(ctx), "--llm-caller", "missing_module:caller"]) == 4

