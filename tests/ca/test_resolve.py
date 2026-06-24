# tests/ca/test_resolve.py
from composable_agents.ca.config import load_config
from composable_agents.ca.resolve import resolve_agent


def test_resolve_flow_returns_ir_json(sample_module):
    cfg = load_config(sample_module)
    resolved = resolve_agent(cfg, "triage")
    assert resolved.name == "triage"
    assert resolved.ir["op"]  # serialized ir.Node has an "op" key
    assert resolved.error is None


def test_resolve_unknown_agent_reports_error(sample_module):
    cfg = load_config(sample_module)
    resolved = resolve_agent(cfg, "nope")
    assert resolved.error is not None
    assert "nope" in resolved.error
