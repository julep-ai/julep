"""User-facing diagnostic formatting."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

from .validate import Diagnostic

HINTS: dict[str, str] = {
    "APPROVAL_UNGATED": (
        "Put a human_gate() before this call so every path to it is dominated by approval — "
        "e.g. seq(human_gate(), call(...))."
    ),
    "CAP_TOOL_DENIED": "Add this tool to the capability manifest's tools: allow-list, or remove the call.",
    "CAP_APP_TOOL_DENIED": "Grant the tool in the manifest tools: list, or drop it from app(tools=[...]).",
    "CAP_APP_APPROVAL_TOOL": (
        "Agents can't call approval-required/dangerous tools. Remove it from app(tools=...) "
        "and ESCALATE, or gate it behind human_gate() in a non-agent flow."
    ),
    "UNKNOWN_PURE": (
        "Register the pure with @pure('name') / register_pure(...) before deploy; "
        "pure names are content-addressed."
    ),
    "CAP_VERSION_PIN": (
        "Bump the mcp_servers: version pin to match the frozen server version, or re-pin the snapshot."
    ),
    "CAP_MODEL_DENIED": (
        "Add the reasoner to the manifest reasoners: allow-list, or drop the reasoners: section to leave reasoners unconstrained."
    ),
    "CAP_MODEL_ID_DENIED": "Add the reasoner's resolved model to the manifest models: allow-list.",
    "CAP_SUBFLOW_DENIED": "Grant the sub-flow in the manifest subflows: list.",
    "CAP_APP_SUBFLOW_DENIED": "Grant the sub-flow in the manifest subflows: list.",
    "CAP_SERVER_DENIED": "Grant the MCP server in the manifest mcp_servers:.",
    "CAP_MEMORY_DENIED": "Grant this context scope in the manifest memory:.",
}


def hint_for(code: str) -> Optional[str]:
    return HINTS.get(code)


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
        if diag.source is not None:
            pointer = f"    --> {diag.source.file}:{diag.source.line}"
            if diag.source.text:
                pointer += f"  ({diag.source.text})"
            lines.append(pointer)
        hint = diag.hint or hint_for(diag.code)
        if hint:
            lines.append(f"    fix: {hint}")
        if diag.help_url:
            lines.append(f"    help: {diag.help_url}")
    return "\n".join(lines)
