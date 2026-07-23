# WS2 — Executable Docs in CI + Quick-Win Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the documentation executable in CI — run every runnable fenced `python` block in the getting-started docs against the installed package, and assert claimed outputs — so docs can never again disagree with reality (the `Pipeline`-vs-`Dataflow` class of bug). Land the cheap trust fixes alongside.

**Architecture:** A dependency-free fenced-block extractor walks the doc tree, pulls ```python``` blocks (and an adjacent ```text``` "expected output" block when a block opts in), and a parametrized pytest runs each runnable block in a fresh keyless subprocess. Blocks opt out (`skip`) or declare intent (`expect-output`, `raises=`) via an HTML-comment pragma on the line before the fence. v1 scope: `start/` + `reference/cheatsheet.md`; expand to `guides/` later.

**Tech Stack:** Python 3.12+, pytest (parametrization), stdlib only for the extractor. Docs live in `docs-site/content/docs/**/*.{md,mdx}`.

## Global Constraints

- Python **3.12+**.
- The extractor uses **stdlib only** (no markdown library) — a line state-machine, so it has no new dependency and runs in the core test job.
- Each doc block runs in a **fresh subprocess** with **no API keys** and **no network**; blocks that need a model must use the documented keyless path (`dry_run` + fake reasoners, scripted `llm`, or echo). Illustrative/partial snippets opt out via pragma.
- Gates clean before each commit: `python -m pytest -q`, `uv run mypy --strict composable_agents`, `ruff check composable_agents`.
- **Sequencing:** intended to run *after* WS5, so the executed examples are already in the object-first idiom. The harness is idiom-agnostic, so it also works before WS5.

## File Structure

- **Create** `tests/_docs_runner.py` — the fenced-block extractor (importable helper; its own unit tests). One responsibility: parse a markdown file into an ordered list of `DocBlock` records.
- **Create** `tests/test_docs_runner.py` — unit tests for the extractor.
- **Create** `tests/test_docs_executable.py` — the parametrized executor: collect blocks from the v1 doc set, run each, assert success / expected output / expected exception.
- **Modify** docs that contain blocks needing a pragma or a corrected expected-output:
  `docs-site/content/docs/start/first-flow.md`, `start/first-agent.md`, `guides/authoring-flows.md`, `reference/cheatsheet.md` (+ any block that is illustrative-only).
- **Modify** `docs-site/content/docs/concepts/model.md:188` (broken link) and `docs-site/content/docs/guides/gotchas.md:282` (pip-user install).
- **Create/Modify** `tests/test_version.py` — regression pin for `__version__`.

---

### Task 1: Fenced-block extractor + unit tests

**Files:**
- Create: `tests/_docs_runner.py`
- Create: `tests/test_docs_runner.py`

**Interfaces:**
- Produces (consumed by Task 2):
  - `DocBlock` dataclass: `path: str`, `line: int`, `lang: str`, `code: str`, `directive: str | None` (one of `None`, `"skip"`, `"expect-output"`, or `"raises=<Name>"`), `expected_output: str | None`.
  - `extract_blocks(path: Path) -> list[DocBlock]` — python blocks only, each with its directive (from a `<!-- julep:doctest ... -->` comment on the line immediately before the opening fence) and `expected_output` (the verbatim contents of a ```text``` fence immediately following the python fence, used only when the directive is `expect-output`).

- [ ] **Step 1: Write the failing test** (`tests/test_docs_runner.py`):

```python
from pathlib import Path

from tests._docs_runner import extract_blocks


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "doc.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_extracts_plain_python_block(tmp_path: Path) -> None:
    doc = _write(tmp_path, "intro\n\n```python\nprint(1)\n```\n\nmore\n")
    blocks = extract_blocks(doc)
    assert len(blocks) == 1
    assert blocks[0].lang == "python"
    assert blocks[0].code == "print(1)\n"
    assert blocks[0].directive is None
    assert blocks[0].expected_output is None


def test_skip_directive(tmp_path: Path) -> None:
    doc = _write(tmp_path, "<!-- julep:doctest skip -->\n```python\nbad(\n```\n")
    assert extract_blocks(doc)[0].directive == "skip"


def test_expect_output_captures_following_text_block(tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        "<!-- julep:doctest expect-output -->\n```python\nprint('Dataflow')\n```\n\n```text\nDataflow\n```\n",
    )
    b = extract_blocks(doc)[0]
    assert b.directive == "expect-output"
    assert b.expected_output == "Dataflow\n"


def test_raises_directive(tmp_path: Path) -> None:
    doc = _write(tmp_path, "<!-- julep:doctest raises=DefineError -->\n```python\nboom()\n```\n")
    assert extract_blocks(doc)[0].directive == "raises=DefineError"
```

- [ ] **Step 2: Run to confirm failure**

Run: `python -m pytest tests/test_docs_runner.py -v`
Expected: FAIL (`ModuleNotFoundError: tests._docs_runner`).

- [ ] **Step 3: Implement the extractor** (`tests/_docs_runner.py`):

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_PRAGMA = re.compile(r"<!--\s*julep:doctest\s+(skip|expect-output|raises=[A-Za-z_][A-Za-z0-9_]*)\s*-->")
_FENCE = re.compile(r"^```([A-Za-z0-9_-]*)\s*$")


@dataclass(frozen=True)
class DocBlock:
    path: str
    line: int
    lang: str
    code: str
    directive: str | None
    expected_output: str | None


def extract_blocks(path: Path) -> list[DocBlock]:
    """Return the python fenced blocks in `path`, with their doctest directive
    and (for expect-output) the immediately-following ```text``` block."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    blocks: list[DocBlock] = []
    i = 0
    pending_directive: str | None = None
    while i < len(lines):
        pragma = _PRAGMA.search(lines[i])
        if pragma:
            pending_directive = pragma.group(1)
            i += 1
            continue
        fence = _FENCE.match(lines[i])
        if fence and fence.group(1) == "python":
            start = i
            body: list[str] = []
            i += 1
            while i < len(lines) and not _FENCE.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # consume closing fence
            directive = pending_directive
            pending_directive = None
            expected: str | None = None
            if directive == "expect-output":
                expected = _next_text_block(lines, i)
            blocks.append(
                DocBlock(
                    path=str(path),
                    line=start + 1,
                    lang="python",
                    code="".join(body),
                    directive=directive,
                    expected_output=expected,
                )
            )
            continue
        # any non-pragma, non-python-fence line clears a dangling directive
        if lines[i].strip():
            pending_directive = None
        i += 1
    return blocks


def _next_text_block(lines: list[str], idx: int) -> str | None:
    """The contents of the next ```text``` fence at/after idx, skipping blanks."""
    j = idx
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j < len(lines):
        fence = _FENCE.match(lines[j])
        if fence and fence.group(1) == "text":
            body: list[str] = []
            j += 1
            while j < len(lines) and not _FENCE.match(lines[j]):
                body.append(lines[j])
                j += 1
            return "".join(body)
    return None
```

- [ ] **Step 4: Run tests + gates**

Run: `python -m pytest tests/test_docs_runner.py -v && ruff check tests/_docs_runner.py`
Expected: PASS / clean.

- [ ] **Step 5: Commit**

```bash
git add tests/_docs_runner.py tests/test_docs_runner.py
git commit -m "test(docs): add dependency-free fenced-block extractor for executable docs"
```

---

### Task 2: Run the getting-started doc blocks; fix the stale shape claim

**Files:**
- Create: `tests/test_docs_executable.py`
- Modify: `docs-site/content/docs/start/first-flow.md` (shape claim + pragmas), `start/first-agent.md`, `guides/authoring-flows.md` (shape claim + the intentional "define-time errors" snippet), `reference/cheatsheet.md` (illustrative blocks).

**Interfaces:** consumes `extract_blocks` / `DocBlock` from Task 1.

- [ ] **Step 1: Write the executor test** (`tests/test_docs_executable.py`):

```python
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
```

- [ ] **Step 2: Tag the doc blocks.** Walk the v1 docs and add a pragma line immediately above each fence that is not a standalone runnable script:
  - `start/first-flow.md`: the complete quickstart block → `<!-- julep:doctest expect-output -->` (its following ```text``` block is the expected stdout). The small inspection snippets (`deployment.surface_shape` etc., lines ~157-163, 181-183) are partial → `<!-- julep:doctest skip -->`.
  - `guides/authoring-flows.md`: the "These are define-time errors" snippet (the `if hit:` / `for item in xs:` example) → `<!-- julep:doctest skip -->` (it is intentionally illegal and not a full program); the full quickstart block → `expect-output`.
  - `start/first-agent.md` and `cheatsheet.md`: tag any partial/illustrative block `skip`; leave full runnable blocks untagged (default = must run clean).

- [ ] **Step 3: Run the executor — watch it RED on the stale shape**

Run: `python -m pytest tests/test_docs_executable.py -v`
Expected: FAIL on `first-flow.md` (and `authoring-flows.md`) — the `expect-output` block prints `Dataflow` but the ```text``` block claims `Pipeline`.

- [ ] **Step 4: Fix the stale claim.** In `start/first-flow.md` change the expected-output `Pipeline` → `Dataflow` (line ~84) and the comment `# "Pipeline"` (line ~182) → `# "Dataflow"`; in `guides/authoring-flows.md` change the expected `Pipeline` (line ~99) → `Dataflow`. (Verified against current main: the canonical flow's `surface_shape.value` is `Dataflow` because `hit | answer` introduces a dataflow join.)

- [ ] **Step 5: Re-run — GREEN**

Run: `python -m pytest tests/test_docs_executable.py -v`
Expected: PASS (every collected block runs; the expect-output blocks match).

- [ ] **Step 6: Gates + commit**

```bash
git add tests/test_docs_executable.py docs-site/content/docs/start docs-site/content/docs/guides/authoring-flows.md docs-site/content/docs/reference/cheatsheet.md
ruff check tests/test_docs_executable.py
git commit -m "test(docs): execute getting-started blocks in CI; fix stale Pipeline->Dataflow claim"
```

---

### Task 3: Quick-win trust fixes (link, install, version pin)

**Files:**
- Modify: `docs-site/content/docs/concepts/model.md:188`
- Modify: `docs-site/content/docs/guides/gotchas.md:282`
- Create: `tests/test_version.py`

**Interfaces:** none (independent fixes).

- [ ] **Step 1: Fix the broken link.** `concepts/model.md:188` currently reads:

```
[the session design specsuperpowers/specs/2026-06-23-upgradeable-sessions-design.md.
```

Replace with a well-formed link to the Sessions guide (the public doc), e.g.:

```
[the Sessions guide](/docs/guides/sessions).
```

- [ ] **Step 2: Fix the pip-user install in gotchas.** `gotchas.md:282` shows `pip install -e '.[cli]'` under "Prerequisites" — a source-checkout command a pip user can't run. Add the pip-user form alongside it:

```bash
pip install 'composable-agents[cli]'   # from PyPI
pip install -e '.[cli]'                 # from a source checkout (contributors)
```

(Leave the `[temporal]` line at ~290 similarly annotated if it has the same issue.)

- [ ] **Step 3: Write the `__version__` regression pin** (`tests/test_version.py`):

```python
from importlib.metadata import version


def test_version_matches_distribution_metadata() -> None:
    import composable_agents

    # __version__ must be derived from the installed distribution, never a hardcoded
    # constant (the stale-wheel bug reported 0.1.0 against a 1.0.0rc1 distribution).
    assert composable_agents.__version__ == version("composable-agents")
    assert composable_agents.__version__ != "0.1.0"
```

- [ ] **Step 4: Run + gates**

Run: `python -m pytest tests/test_version.py -v`
Expected: PASS (current main already derives `__version__` from `importlib.metadata`; this pins it against regression and against a stale-wheel hardcode).

> Note: the `dist/` wheel that reported `0.1.0` is stale (built before the metadata-derivation fix). Rebuilding/publishing from current main resolves the artifact; the test above guards the code path.

- [ ] **Step 5: Commit**

```bash
git add docs-site/content/docs/concepts/model.md docs-site/content/docs/guides/gotchas.md tests/test_version.py
git commit -m "docs+test: fix broken sessions link + pip-user install; pin __version__ to dist metadata"
```

---

## Self-review

- **Spec coverage (§5 of the design):** doc-block execution harness over `start/` + `cheatsheet` → Tasks 1-2; stale `Pipeline`→`Dataflow` → Task 2 Steps 3-4 (and now CI-locked); broken link → Task 3 Step 1; pip-user install → Task 3 Step 2; `__version__` regression → Task 3 Step 3 (reframed: code is already correct on main; the test pins it and the stale `dist/` wheel is a rebuild, noted in Task 3 Step 4).
- **Placeholder scan:** the doc-tagging in Task 2 Step 2 lists specific files/lines and the rule (full runnable → default; partial/illegal → `skip`; output-asserting → `expect-output`); no "add appropriate tags" hand-waving. All code blocks are complete.
- **Type consistency:** `DocBlock`/`extract_blocks` defined in Task 1 are consumed with the same field names (`code`, `directive`, `expected_output`, `path`, `line`) in Task 2's executor.
