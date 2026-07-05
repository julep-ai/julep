from __future__ import annotations

import json

from julep import Diagnostic, arr, ident, register_pure, seq
from julep import explain as explain_diagnostics
from julep import cli


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_explain_groups_blocking_and_warning_diagnostics() -> None:
    rendered = explain_diagnostics(
        [
            Diagnostic("BLOCKED", "node-a", "hard stop"),
            Diagnostic("WARNED", "node-b", "heads up", severity="warning"),
        ]
    )

    assert "Blocking diagnostics" in rendered
    assert "[BLOCKED@node-a]" in rendered
    assert "Warnings" in rendered
    assert "[WARNED@node-b]" in rendered


def test_validate_cli_exits_by_blocking_status(tmp_path, capsys) -> None:
    good = tmp_path / "good.json"
    bad = tmp_path / "bad.json"
    _write_json(good, ident().to_json())
    _write_json(bad, {"op": "arr", "id": "needs-pure"})

    assert cli.main(["validate", str(good)]) == 0
    good_out = capsys.readouterr().out
    assert "No diagnostics" in good_out

    assert cli.main(["validate", str(bad)]) != 0
    bad_out = capsys.readouterr().out
    assert "Blocking diagnostics" in bad_out
    assert "ARR_NO_PURE" in bad_out


def test_graph_cli_emits_dot_with_each_node_id(tmp_path, capsys) -> None:
    flow = seq(ident(), ident())
    path = tmp_path / "flow.json"
    _write_json(path, flow.to_json())

    assert cli.main(["graph", str(path)]) == 0

    out = capsys.readouterr().out
    assert out.startswith("digraph")
    for node in flow.walk():
        assert node.id in out


def test_run_local_cli_uses_stubs_and_prints_cost_by_shape(tmp_path, capsys) -> None:
    register_pure("cli.test.echo", lambda value: value)
    flow = seq(arr("cli.test.echo"), ident())
    flow_path = tmp_path / "flow.json"
    input_path = tmp_path / "input.json"
    _write_json(flow_path, flow.to_json())
    _write_json(input_path, {"value": 7})

    assert cli.main(["run-local", str(flow_path), str(input_path)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["result"] == {"value": 7}
    assert payload["cost_by_shape"]
    assert "Pipeline" in payload["cost_by_shape"]
