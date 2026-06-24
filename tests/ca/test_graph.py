# tests/ca/test_graph.py
from composable_agents.ca import cli


def test_graph_emits_dot_with_edge(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = cli.main(["graph"])
    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("digraph")
    assert '"triage" -> "escalate"' in out  # edge: callee -> caller


def test_graph_respects_selector(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = cli.main(["graph", "triage"])
    out = capsys.readouterr().out
    assert '"triage"' in out and "support_bot" not in out
