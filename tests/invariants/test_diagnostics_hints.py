from __future__ import annotations

from composable_agents.diagnostics import HINTS, explain, hint_for
from composable_agents.validate import Diagnostic


def test_explain_renders_fix_for_known_diagnostic_code() -> None:
    rendered = explain([Diagnostic("APPROVAL_UNGATED", "$.R", "...")])

    assert "- [APPROVAL_UNGATED@$.R] error: ..." in rendered
    assert f"    fix: {HINTS['APPROVAL_UNGATED']}" in rendered


def test_explain_omits_fix_and_help_for_unknown_code_without_hint() -> None:
    rendered = explain([Diagnostic("UNKNOWN_CODE", "$", "m")])

    assert rendered == "Blocking diagnostics:\n- [UNKNOWN_CODE@$] error: m"
    assert "fix:" not in rendered
    assert "help:" not in rendered


def test_explicit_hint_overrides_table_hint() -> None:
    rendered = explain([Diagnostic("CAP_TOOL_DENIED", "$", "m", hint="custom")])

    assert "    fix: custom" in rendered
    assert HINTS["CAP_TOOL_DENIED"] not in rendered


def test_help_renders_only_when_set() -> None:
    without_help = explain([Diagnostic("APPROVAL_UNGATED", "$", "m")])
    with_help = explain([Diagnostic("APPROVAL_UNGATED", "$", "m", help_url="http://x")])

    assert "help:" not in without_help
    assert "    help: http://x" in with_help


def test_hint_for_returns_known_entry_or_none() -> None:
    assert hint_for("APPROVAL_UNGATED") == HINTS["APPROVAL_UNGATED"]
    assert hint_for("UNKNOWN_CODE") is None
