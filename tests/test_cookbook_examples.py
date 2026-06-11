from __future__ import annotations

import pytest

from composable_agents import blocking, call, check_approval_gates, deploy, seq
from composable_agents.errors import ValidationError
from conftest import run

from examples import (
    cluster_labeling_flow,
    cma_managed_agent,
    email_approval,
    episode_summary_flow,
    research_assistant,
    support_triage,
)


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
    assert result["cost"] == 8.0
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


def test_cma_managed_agent_example_is_keyless_no_op_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The CMA example is the one example that talks to a live service. Without a
    # key it must be a clean, network-free no-op (import-safe + run_demo None).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert cma_managed_agent.run_demo() is None
    # build() is keyless construction only (no network); the agent grants its tools.
    agent = cma_managed_agent.build()
    assert agent._granted == {"get_weather", "to_fahrenheit"}


def test_episode_summary_flow_deploys_clean_and_rolls_up_statuses_in_order() -> None:
    deployment = episode_summary_flow.build()

    assert not blocking(deployment.diagnostics)

    result = run(episode_summary_flow.run_demo())

    assert result.value["counts"] == {"success": 2, "stale_source": 1, "not_found": 1}
    assert [(r["episodeId"], r["status"]) for r in result.value["results"]] == [
        ("ep-1001", "success"),
        ("ep-1002", "success"),
        ("ep-1003", "stale_source"),
        ("ep-9999", "not_found"),
    ]


def test_episode_summary_flow_cas_guard_blocks_stale_write() -> None:
    run(episode_summary_flow.run_demo())

    store = episode_summary_flow._store
    for episode_id in ("ep-1001", "ep-1002"):
        assert store[episode_id]["summary"] is not None
        assert store[episode_id]["oneLiner"] is not None
    # ep-1003 was edited between read and write, so the CAS write must not land.
    assert store["ep-1003"]["summary"] is None
    assert store["ep-1003"]["oneLiner"] is None


def test_cluster_labeling_flow_deploys_clean_and_rolls_up_statuses_in_order() -> None:
    deployment = cluster_labeling_flow.build()

    assert not blocking(deployment.diagnostics)

    result = run(cluster_labeling_flow.run_demo())

    assert result.value["counts"] == {
        "success": 1,
        "stale_snapshot": 1,
        "not_found": 1,
    }
    assert [(r["storeId"], r["status"]) for r in result.value["results"]] == [
        ("store-clean", "success"),
        ("store-stale", "stale_snapshot"),
        ("store-missing", "not_found"),
    ]


def test_cluster_labeling_flow_cas_guard_writes_one_snapshot_or_none() -> None:
    run(cluster_labeling_flow.run_demo())

    store = cluster_labeling_flow._store
    clean_labels = store["store-clean"]["labels"]
    assert sorted(clean_labels) == ["macro-10", "macro-20"]
    assert all(label["label"] for label in clean_labels.values())
    assert all(label["keywords"] for label in clean_labels.values())

    # store-stale was edited after the global snapshot read, so the single
    # CAS-guarded snapshot write must leave the label snapshot untouched.
    assert store["store-stale"]["labels"] == {}


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
