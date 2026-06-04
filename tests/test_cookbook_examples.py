from __future__ import annotations

from composable_agents import blocking, call, check_approval_gates, deploy, seq
from composable_agents.errors import ValidationError
from conftest import run

from examples import email_approval, research_assistant, support_triage


def _blocking_codes(diagnostics) -> list[str]:
    return [diag.code for diag in blocking(diagnostics)]


def test_support_triage_runs_keyless_and_denies_ungranted_tool() -> None:
    result = support_triage.run_demo()

    assert result["status"] == "done"
    assert result["output"] == {
        "priority": "high",
        "queue": "billing",
        "reply": "Use the billing retry runbook and refund duplicate charge if confirmed.",
    }
    assert result["trace"] == [
        {"decision": "call", "ref": "search_kb", "cost": 1.0},
        {"decision": "call", "ref": "classify_priority", "cost": 1.0},
    ]

    denied = support_triage.run_ungranted_tool_demo()

    assert denied["status"] == "denied"
    assert "not granted" in denied["reason"]


def test_research_assistant_runs_keyless_with_budget_and_denies_ungranted_tool() -> None:
    result = research_assistant.run_demo()

    assert result["status"] == "done"
    assert result["output"] == {
        "answer": "Use Postgres advisory locks; pair them with a visibility timeout.",
        "sources": ["ops-note:advisory-locks", "runbook:visibility-timeouts"],
    }
    assert result["spentUsd"] == 8.0
    assert result["trace"] == [
        {"decision": "call", "ref": "web_search", "cost": 1.0},
        {"decision": "call", "ref": "web_search", "cost": 1.0},
    ]

    denied = research_assistant.run_ungranted_tool_demo()

    assert denied["status"] == "denied"
    assert "not granted" in denied["reason"]


def test_email_approval_runs_keyless_after_gate_and_rejects_ungated_send() -> None:
    deployment = email_approval.build()

    assert not blocking(deployment.diagnostics)

    sent: list[dict] = []
    result = run(email_approval.run_demo(sent=sent))

    assert result.value["status"] == "sent"
    assert result.value["to"] == "customer@example.com"
    assert result.value["approved_by"] == "cookbook-reviewer"
    assert sent == [result.value]

    broken = seq(
        call(email_approval.TOOL_DRAFT_EMAIL),
        call(email_approval.TOOL_SEND_EMAIL),
    )
    denied = deploy(
        broken,
        email_approval.snapshot(),
        capabilities=email_approval.capabilities(),
        strict=False,
    )

    assert "APPROVAL_UNGATED" in _blocking_codes(
        check_approval_gates(denied.flow, denied.manifest, denied.capabilities)
    )
    assert "APPROVAL_UNGATED" in _blocking_codes(denied.diagnostics)


def test_email_approval_strict_deploy_rejects_ungated_send() -> None:
    broken = seq(
        call(email_approval.TOOL_DRAFT_EMAIL),
        call(email_approval.TOOL_SEND_EMAIL),
    )

    try:
        deploy(
            broken,
            email_approval.snapshot(),
            capabilities=email_approval.capabilities(),
        )
    except ValidationError as exc:
        assert "APPROVAL_UNGATED" in _blocking_codes(exc.diagnostics)
    else:  # pragma: no cover
        raise AssertionError("strict deploy unexpectedly accepted an ungated send")
