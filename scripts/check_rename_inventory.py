#!/usr/bin/env python3
"""Reject names retired by the Julep hard cutover."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_INVENTORY_START = "<!-- rename-inventory:start -->"
_INVENTORY_END = "<!-- rename-inventory:end -->"
_MATCH_MODES = frozenset({"prefix", "token"})
_IDENTIFIER_CHARS = "A-Za-z0-9_"
_RESOURCE_NAME_CHARS = frozenset(
    ".-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
)

_SCAN_TARGETS = (
    "julep",
    "tests",
    "scripts",
    "docs",
    "docs-site",
    ".github",
    "examples",
    "infra",
    "tooling",
    ".gitignore",
    "CONTRIBUTING.md",
    "README.md",
    "TODOS.md",
    "pyproject.toml",
)
_EXCLUDED_PATHS = frozenset(
    {
        "docs/rename-inventory.md",
        "scripts/check_rename_inventory.py",
    }
)
_EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "node_modules",
        "wasi_wheels",
    }
)
_BINARY_SUFFIXES = frozenset(
    {
        ".gif",
        ".gz",
        ".ico",
        ".jpeg",
        ".jpg",
        ".pdf",
        ".png",
        ".pyc",
        ".tar",
        ".wasm",
        ".whl",
        ".zip",
    }
)

# These files intentionally retain old names as migration-diagnostic data. The
# exception is category-scoped so unrelated retired names still fail the guard.
_ALLOWED_CATEGORIES_BY_PATH = {
    "julep/_env.py": frozenset({"env", "env-family"}),
    "julep/cli/config.py": frozenset({"config"}),
    "julep/cli/doctor.py": frozenset({"config", "env", "env-family", "state"}),
    "tests/cli/test_config.py": frozenset({"config"}),
    "tests/cli/test_doctor.py": frozenset({"config", "env", "env-family", "state"}),
}
_ALLOWED_RESOURCE_LITERALS_BY_PATH = {
    "tooling/sandbox-k8s/Dockerfile": frozenset({"ca-bundle.crt"}),
    "tooling/sandbox-k8s/setup.sh": frozenset({"ca-bundle.crt", "ca-certificates.crt"}),
}


@dataclass(frozen=True)
class Rename:
    category: str
    match: str
    old: str
    new: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    column: int
    matched: str
    rename: Rename

    def render(self) -> str:
        return (
            f"{self.path}:{self.line}:{self.column}: forbidden {self.matched!r}; "
            f"replace {self.rename.old!r} with {self.rename.new!r} "
            f"[{self.rename.category}]"
        )


def _compile_pattern(old: str, match_mode: str) -> re.Pattern[str]:
    before = rf"(?<![{_IDENTIFIER_CHARS}])" if old[0].isalnum() or old[0] == "_" else ""
    escaped = re.escape(old)
    if match_mode == "prefix":
        return re.compile(before + escaped + rf"[{_IDENTIFIER_CHARS}-]*")
    after = rf"(?![{_IDENTIFIER_CHARS}])" if old[-1].isalnum() or old[-1] == "_" else ""
    return re.compile(before + escaped + after)


def load_inventory(path: Path) -> tuple[Rename, ...]:
    """Parse and validate the machine-readable TSV block in the inventory."""

    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(_INVENTORY_START) + 1
        end = lines.index(_INVENTORY_END, start)
    except ValueError as exc:
        raise ValueError(f"{path}: rename inventory markers are missing") from exc

    renames: list[Rename] = []
    seen_old: set[str] = set()
    for line_number, line in enumerate(lines[start:end], start=start + 1):
        if not line or line.startswith("```") or line == "category\tmatch\told\tnew":
            continue
        parts = line.split("\t")
        if len(parts) != 4:
            raise ValueError(f"{path}:{line_number}: expected four tab-separated columns")
        category, match_mode, old, new = parts
        if not all(parts):
            raise ValueError(f"{path}:{line_number}: inventory columns must not be empty")
        if match_mode not in _MATCH_MODES:
            raise ValueError(
                f"{path}:{line_number}: match mode must be one of {sorted(_MATCH_MODES)!r}"
            )
        if old.casefold() == "ca":
            raise ValueError(f"{path}:{line_number}: refusing to search for the bare token 'ca'")
        if old == new:
            raise ValueError(f"{path}:{line_number}: old and new names must differ")
        if old in seen_old:
            raise ValueError(f"{path}:{line_number}: duplicate old name {old!r}")
        seen_old.add(old)
        renames.append(
            Rename(
                category=category,
                match=match_mode,
                old=old,
                new=new,
                pattern=_compile_pattern(old, match_mode),
            )
        )

    if not renames:
        raise ValueError(f"{path}: rename inventory is empty")
    return tuple(sorted(renames, key=lambda item: len(item.old), reverse=True))


def _is_excluded(relative: Path) -> bool:
    relative_text = relative.as_posix()
    if relative_text in _EXCLUDED_PATHS:
        return True
    if relative.suffix.casefold() in _BINARY_SUFFIXES:
        return True
    if any(part in _EXCLUDED_PARTS for part in relative.parts):
        return True
    return any(part.casefold().startswith("changelog") for part in relative.parts)


def _source_files(root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for target_name in _SCAN_TARGETS:
        target = root / target_name
        if target.is_file():
            candidates: Iterable[Path] = (target,)
        elif target.is_dir():
            candidates = target.rglob("*")
        else:
            candidates = ()
        for candidate in candidates:
            if not candidate.is_file() or candidate in seen:
                continue
            seen.add(candidate)
            relative = candidate.relative_to(root)
            if not _is_excluded(relative):
                yield candidate


def _is_allowed(path: str, rename: Rename, line: str, match: re.Match[str]) -> bool:
    if rename.category in _ALLOWED_CATEGORIES_BY_PATH.get(path, ()):
        return True
    if rename.category != "resource-prefix":
        return False
    suffix = line[match.start() :]
    for literal in _ALLOWED_RESOURCE_LITERALS_BY_PATH.get(path, ()):
        if not suffix.startswith(literal):
            continue
        if len(suffix) == len(literal) or suffix[len(literal)] not in _RESOURCE_NAME_CHARS:
            return True
    return False


def _line_findings(
    path: str,
    line_number: int,
    line: str,
    renames: tuple[Rename, ...],
) -> list[Finding]:
    findings: list[Finding] = []
    occupied: list[tuple[int, int]] = []
    for rename in renames:
        for match in rename.pattern.finditer(line):
            start, end = match.span()
            if any(
                start < occupied_end and occupied_start < end
                for occupied_start, occupied_end in occupied
            ):
                continue
            occupied.append((start, end))
            if not _is_allowed(path, rename, line, match):
                findings.append(
                    Finding(
                        path=path,
                        line=line_number,
                        column=start + 1,
                        matched=match.group(0),
                        rename=rename,
                    )
                )
    return sorted(findings, key=lambda item: item.column)


def find_violations(root: Path, renames: tuple[Rename, ...]) -> tuple[Finding, ...]:
    """Return forbidden old names found in guarded source and documentation."""

    findings: list[Finding] = []
    for path in sorted(_source_files(root)):
        relative = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            findings.extend(_line_findings(relative, line_number, line, renames))
    return tuple(findings)


def check(root: Path, inventory: Path | None = None) -> tuple[Finding, ...]:
    root = root.resolve()
    inventory = inventory or root / "docs" / "rename-inventory.md"
    return find_violations(root, load_inventory(inventory))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the guard script's parent repository)",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        help="inventory path (defaults to docs/rename-inventory.md under --root)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        findings = check(args.root, args.inventory)
    except (OSError, ValueError) as exc:
        print(f"rename inventory guard error: {exc}", file=sys.stderr)
        return 2
    if not findings:
        print("rename inventory guard: clean")
        return 0
    for finding in findings:
        print(finding.render())
    print(f"rename inventory guard: {len(findings)} violation(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
