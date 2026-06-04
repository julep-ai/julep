"""User-facing diagnostic formatting."""

from __future__ import annotations

from collections.abc import Iterable

from .validate import Diagnostic


def explain(diagnostics: Iterable[Diagnostic]) -> str:
    """Render diagnostics for CLI output and library consumers.

    Blocking diagnostics are ``severity == "error"``. Other severities are shown
    as warnings so callers can display degradations without treating them as a
    failed compile.
    """
    diags = list(diagnostics)
    if not diags:
        return "No diagnostics."

    blocking = [diag for diag in diags if diag.severity == "error"]
    warnings = [diag for diag in diags if diag.severity != "error"]
    sections: list[str] = []

    if blocking:
        sections.append(_section("Blocking diagnostics", blocking))
    if warnings:
        sections.append(_section("Warnings", warnings))

    return "\n\n".join(sections)


def _section(title: str, diagnostics: list[Diagnostic]) -> str:
    lines = [f"{title}:"]
    for diag in diagnostics:
        lines.append(f"- [{diag.code}@{diag.node_id}] {diag.severity}: {diag.message}")
    return "\n".join(lines)
