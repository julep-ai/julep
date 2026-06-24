import io

from composable_agents.ca import cli
from composable_agents.ca.chat import render_event
from composable_agents.session import SessionEvent


def test_chat_streams_events_and_exits_clean(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    monkeypatch.setattr("sys.stdin", io.StringIO('"TICKET-1"\n"TICKET-2"\n'))

    code = cli.main(["chat", "triage"])
    captured = capsys.readouterr()

    assert code == 0
    assert captured.out.count("<- ") >= 2
    assert "TICKET-1" in captured.out
    assert "TICKET-2" in captured.out
    assert "[closed]" in captured.out
    assert captured.out.index("<- ") < captured.out.index("[closed]")


def test_chat_unknown_agent_exit_2(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)

    code = cli.main(["chat", "nope"])
    captured = capsys.readouterr()

    assert code == 2
    assert "error:" in captured.err
    assert "not found" in captured.err


def test_chat_help_lists_command(capsys):
    code = cli.main(["--help"])
    out = capsys.readouterr().out
    assert code == 0
    assert "chat" in out

    code = cli.main(["chat", "--help"])
    assert code == 0


def test_render_event():
    assert render_event(SessionEvent.turn_started()) is None
    assert render_event(SessionEvent.turn_done()) is None
    assert render_event(SessionEvent.emit("out", 1, {"answer": "ok"})) == '<- {"answer": "ok"}'
    assert render_event(SessionEvent.error("bad", fatal=True)) == "error: bad"
    assert render_event(SessionEvent.closed()) == "[closed]"
    assert render_event(SessionEvent.closed("done")) == "[closed] done"
