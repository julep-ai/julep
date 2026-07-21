# tests/cli/test_discover.py
from julep.cli.config import load_config
from julep.cli.discover import scan_agents


def test_finds_flow_and_agent(sample_module):
    cfg = load_config(sample_module)
    infos = {a.name: a for a in scan_agents(cfg)}
    assert set(infos) == {"triage", "escalate", "support_bot"}
    assert infos["triage"].kind == "flow"
    assert infos["support_bot"].kind == "agent"
    assert infos["triage"].file.endswith("pkg/agents.py")


def test_extracts_cross_flow_edges(sample_module):
    cfg = load_config(sample_module)
    infos = {a.name: a for a in scan_agents(cfg)}
    # escalate calls triage -> triage is in escalate.calls
    assert "triage" in infos["escalate"].calls
    assert infos["triage"].calls == []  # triage calls only tool/think, not other agents
