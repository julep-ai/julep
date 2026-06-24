# tests/ca/test_run.py
from composable_agents.ca.config import load_config
from composable_agents.ca.resolve import resolve_agent
from composable_agents.ca.runner import RunOutcome, run_agent_local


def test_run_triage_locally(sample_module):
    cfg = load_config(sample_module)
    resolved = resolve_agent(cfg, "triage")
    outcome = run_agent_local(resolved, "TICKET-1", run_id="run-test-1")
    assert isinstance(outcome, RunOutcome)
    assert outcome.run_id == "run-test-1"
    assert outcome.events, "expected projection events"
    assert outcome.error is None


def test_run_unresolved_agent_surfaces_error():
    from composable_agents.ca.resolve import ResolvedAgent

    bad = ResolvedAgent(name="nope", ir={}, error="agent 'nope' not found")
    outcome = run_agent_local(bad, "X", run_id="run-test-2")
    assert outcome.run_id == "run-test-2"
    assert outcome.error == "agent 'nope' not found"
    assert outcome.events == []
    assert outcome.value is None


def test_run_surfaces_runtime_error_without_crashing(sample_module):
    from composable_agents.ca.resolve import ResolvedAgent

    # An IR dict that cannot be deserialized into a Node must not crash the runner;
    # it must come back as RunOutcome.error.
    broken = ResolvedAgent(name="triage", ir={"not": "a real node"}, error=None)
    outcome = run_agent_local(broken, "X", run_id="run-test-3")
    assert outcome.run_id == "run-test-3"
    assert outcome.error is not None
    assert outcome.value is None
