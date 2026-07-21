from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_PRAGMA = re.compile(
    r"<!--\s*julep:doctest\s+(skip|expect-output|raises=[A-Za-z_][A-Za-z0-9_]*)\s*-->"
)
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
