from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests._docs_runner import DocBlock, extract_blocks

_REPO = Path(__file__).resolve().parents[1]
_DOC_GLOBS = ["docs-site/content/docs/start", "docs-site/content/docs/reference/cheatsheet.md"]


def _collect() -> list[DocBlock]:
    blocks: list[DocBlock] = []
    for entry in _DOC_GLOBS:
        p = _REPO / entry
        files = [p] if p.is_file() else sorted(p.rglob("*.md")) + sorted(p.rglob("*.mdx"))
        for f in files:
            blocks.extend(extract_blocks(f))
    return blocks


_BLOCKS = [b for b in _collect() if b.directive != "skip"]


@pytest.mark.parametrize("block", _BLOCKS, ids=[f"{Path(b.path).name}:{b.line}" for b in _BLOCKS])
def test_doc_block_runs(block: DocBlock) -> None:
    env = {"PATH": __import__("os").environ.get("PATH", "")}  # keyless, no provider env, no network creds
    proc = subprocess.run(
        [sys.executable, "-c", block.code],
        capture_output=True, text=True, cwd=str(_REPO), env=env, timeout=120,
    )
    raises = block.directive or ""
    if raises.startswith("raises="):
        exc = raises.split("=", 1)[1]
        assert proc.returncode != 0 and exc in proc.stderr, (
            f"{block.path}:{block.line} expected {exc}\n{proc.stderr}"
        )
        return
    assert proc.returncode == 0, f"{block.path}:{block.line} failed:\n{proc.stderr}"
    if block.directive == "expect-output" and block.expected_output is not None:
        assert block.expected_output.strip() in proc.stdout, (
            f"{block.path}:{block.line} expected output not found.\n"
            f"--- expected ---\n{block.expected_output}\n--- got ---\n{proc.stdout}"
        )
