import io
from typing import Any

from composable_agents.ca import cli
from composable_agents.ca import listen as listen_mod


def test_listen_forwards_emits(sample_module, capsys, monkeypatch):
    forwarded: list[tuple[str, dict[str, Any]]] = []

    def fake_post(url: str, payload: dict[str, Any]) -> int:
        forwarded.append((url, payload))
        return 202

    monkeypatch.chdir(sample_module)
    monkeypatch.setattr("sys.stdin", io.StringIO('"TICKET-4"\n'))
    monkeypatch.setattr(listen_mod, "_DEFAULT_POSTER", fake_post)

    code = cli.main(["listen", "triage", "--forward-to", "http://127.0.0.1/events"])
    captured = capsys.readouterr()

    assert code == 0
    assert forwarded
    assert forwarded[0][0] == "http://127.0.0.1/events"
    assert any(payload["kind"] == "emit" for _, payload in forwarded)
    assert "-> POST http://127.0.0.1/events [202]" in captured.out


def test_listen_requires_forward_to(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)

    code = cli.main(["listen", "triage"])
    captured = capsys.readouterr()

    assert code == 2
    assert "Missing option" in captured.err or "--forward-to" in captured.err


def test_listen_help_present(capsys):
    code = cli.main(["--help"])
    out = capsys.readouterr().out
    assert code == 0
    assert "listen" in out

    code = cli.main(["listen", "--help"])
    assert code == 0
