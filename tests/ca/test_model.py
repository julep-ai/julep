# tests/ca/test_model.py
from composable_agents.ca.config import load_config
from composable_agents.ca.model import build_module


def test_build_module_merges_tags(sample_module):
    module = build_module(load_config(sample_module))
    names = {a.name for a in module.agents}
    assert names == {"triage", "escalate", "support_bot"}
    assert module.by_name("triage").tags == ["support"]
    assert module.by_name("escalate").tags == []
    assert module.by_name("escalate").calls == ["triage"]
