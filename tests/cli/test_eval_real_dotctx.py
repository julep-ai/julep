"""`julep eval` against a REAL installed third-party ``dotctx`` package.

Regression for the shim shadowing a real ``dotctx``: when the package is
importable, the compat shim must not be installed (it lacks ``Context`` and
friends, breaking transitive imports), and the runner must duck-type the real
``dotctx.eval_types.Sample`` instead of rejecting it.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

pytest.importorskip("jinja2")

from julep.cli.evalrun import run_eval
from julep.registry import Registry

# A structurally-identical real dotctx package (proper package with submodules).
_EVAL_TYPES = '''\
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


def stop_after_turns(max_turns):
    def _stop(_last, turn_index):
        return turn_index >= max_turns
    return _stop


def _default_stop_on():
    return stop_after_turns(1)


@dataclass
class Expected:
    content: Optional[str] = None


@dataclass
class MockToolConfig:
    match: list = field(default_factory=list)
    default: Any = None
    responses: list = field(default_factory=list)


@dataclass
class Sample:
    input: dict
    expected: Optional[Expected] = None
    mock_tools: dict = field(default_factory=dict)
    stop_on: Callable = field(default_factory=_default_stop_on)
    expected_calls: Optional[list] = None
    tags: list = field(default_factory=list)
    name: Optional[str] = None
'''

_LLM_UTILS = '''\
def extract_llm_content(response):
    if isinstance(response, dict):
        return response.get("content")
    return None
'''

_CONTEXT = '''\
class Context:
    """The non-eval surface the compat shim lacks."""
'''

_INIT = '''\
from .context import Context
from .eval_types import Expected, MockToolConfig, Sample, stop_after_turns
from .llm_utils import extract_llm_content
'''

# A helper imported by eval.py that touches the real package's non-eval surface
# at import time — the exact transitive path the shim used to break.
_JUDGE_HELPER = '''\
from dotctx import Context

CTX_MARKER = Context.__name__
'''

_EVAL_PY = '''\
from dotctx import extract_llm_content
from dotctx.eval_types import Sample
from judge_helper import CTX_MARKER


def sample(limit=-1):
    samples = [
        Sample(input={"task": f"item {n}", "marker": CTX_MARKER}, name=f"s{n}")
        for n in range(3)
    ]
    return samples if limit is None or limit < 0 else samples[:limit]


def score(inp, output, expected):
    return 1.0 if extract_llm_content(output) else 0.0
'''


def _install_real_dotctx(root: Path) -> None:
    pkg = root / "dotctx"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(_INIT, encoding="utf-8")
    (pkg / "eval_types.py").write_text(_EVAL_TYPES, encoding="utf-8")
    (pkg / "llm_utils.py").write_text(_LLM_UTILS, encoding="utf-8")
    (pkg / "context.py").write_text(_CONTEXT, encoding="utf-8")
    (root / "judge_helper.py").write_text(_JUDGE_HELPER, encoding="utf-8")


def _write_ctx(root: Path) -> Path:
    ctx = root / "case.ctx"
    ctx.mkdir()
    (ctx / "settings.yaml").write_text('model: "openai/gpt-eval@low"\n', encoding="utf-8")
    (ctx / "prompt.j2").write_text(
        "<<< role:system >>>\nHi.\n\n<<< role:user >>>\nT: {{ task | default('', true) }}\n",
        encoding="utf-8",
    )
    (ctx / "eval.py").write_text(_EVAL_PY, encoding="utf-8")
    return ctx


@pytest.fixture
def _clean_dotctx_modules():
    yield
    for name in list(sys.modules):
        if name == "dotctx" or name.startswith("dotctx.") or name == "judge_helper":
            del sys.modules[name]


def test_eval_runs_against_real_installed_dotctx(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    _clean_dotctx_modules: None,
) -> None:
    pkg_root = tmp_path / "site"
    pkg_root.mkdir()
    _install_real_dotctx(pkg_root)
    monkeypatch.syspath_prepend(str(pkg_root))
    ctx = _write_ctx(tmp_path)

    calls: list[str] = []

    async def stub_llm_caller(reasoner, value, contracts, transcript, dispatch, **kwargs):
        calls.append(getattr(reasoner, "name", "?"))
        return "structured reply"

    report = asyncio.run(
        run_eval(str(ctx), llm_caller=stub_llm_caller, registry=Registry())
    )

    # The real package resolved (not the shim), for both eval.py and the
    # transitive `from dotctx import Context` in judge_helper.
    assert "dotctx" in sys.modules
    assert sys.modules["dotctx"].__file__ == str(pkg_root / "dotctx" / "__init__.py")
    assert sys.modules["dotctx.eval_types"].Sample.__module__ == "dotctx.eval_types"

    # All samples loaded (real dotctx.Sample duck-typed) and the caller reached.
    assert report.samples == 3
    assert len(calls) == 3
    assert report.mean == 1.0
