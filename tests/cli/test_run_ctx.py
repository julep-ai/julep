from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("jinja2")

from julep.cli.ctxrun import run_ctx_local
from julep.cli.main import main

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@dataclass
class _Message:
    content: str
    parsed: Any = None
    tool_calls: Any = None


@dataclass
class _Choice:
    message: _Message


@dataclass
class _Completion:
    choices: list[_Choice]


class _SingleShotFake:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    async def __call__(self, **kwargs: Any) -> _Completion:
        return _Completion([_Choice(_Message(self.reply))])


def test_run_ctx_local_returns_stable_artifact_and_reply() -> None:
    path = str(FIXTURES / "summarizer.ctx")
    first = run_ctx_local(path, {"audience": "engineers"}, acompletion=_SingleShotFake("ok"))
    second = run_ctx_local(path, {"audience": "engineers"}, acompletion=_SingleShotFake("ok"))
    assert first.artifact_hash.startswith("sha256:")
    assert first.artifact_hash == second.artifact_hash
    assert first.reply == "ok"


def test_run_ctx_command_prints_stable_artifact(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "julep.cli.evalrun._resolve_acompletion", lambda _value: _SingleShotFake("fake reply")
    )
    args = [
        "run",
        str(FIXTURES / "summarizer.ctx"),
        "--input",
        '{"audience":"engineers"}',
        "--env",
        "local",
    ]
    assert main(args) == 0
    first = capsys.readouterr().out
    assert "artifact sha256:" in first
    assert 'output: "fake reply"' in first
    assert main(args) == 0
    second = capsys.readouterr().out
    first_hash = first.split("artifact ", 1)[1].splitlines()[0]
    second_hash = second.split("artifact ", 1)[1].splitlines()[0]
    assert first_hash == second_hash


def test_run_ctx_missing_path_exits_two(tmp_path: Path) -> None:
    assert main(["run", str(tmp_path / "missing.ctx")]) == 2

