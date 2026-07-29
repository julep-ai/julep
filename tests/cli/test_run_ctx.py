from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("jinja2")

from julep.cli.ctxrun import run_ctx_local
from julep.cli.main import main
from julep.cli.runcache import load_run

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


class _FailingFake:
    async def __call__(self, **kwargs: Any) -> _Completion:
        raise RuntimeError("local ctx provider failed")


def test_run_ctx_local_returns_stable_artifact_and_reply() -> None:
    path = str(FIXTURES / "summarizer.ctx")
    first = run_ctx_local(path, {"audience": "engineers"}, acompletion=_SingleShotFake("ok"))
    second = run_ctx_local(path, {"audience": "engineers"}, acompletion=_SingleShotFake("ok"))
    assert first.artifact_hash.startswith("sha256:")
    assert first.artifact_hash == second.artifact_hash
    assert first.reply == "ok"


def test_run_ctx_command_prints_stable_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
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
    assert "artifact-digest sha256:" in first
    assert 'output: "fake reply"' in first
    assert main(args) == 0
    second = capsys.readouterr().out
    first_hash = first.split("artifact-digest ", 1)[1].splitlines()[0]
    second_hash = second.split("artifact-digest ", 1)[1].splitlines()[0]
    assert first_hash == second_hash


def test_run_ctx_missing_path_exits_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["run", str(tmp_path / "missing.ctx")]) == 2


def test_run_ctx_command_persists_projection_for_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "julep.cli.evalrun._resolve_acompletion",
        lambda _value: _SingleShotFake('{"summary":"persisted"}'),
    )
    ctx = str(FIXTURES / "memmcp" / "episode_summary.ctx")

    assert main(["run", ctx, "--input", '{"content":"hello"}', "--run-id", "ctx-r1"]) == 0
    cached = load_run(str(tmp_path), "ctx-r1")
    assert cached is not None
    assert cached["status"] == "done"
    assert cached["events"]

    capsys.readouterr()
    assert main(["trace", "ctx-r1"]) == 0
    assert capsys.readouterr().out.strip()


def test_run_ctx_command_persists_error_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "julep.cli.evalrun._resolve_acompletion", lambda _value: _FailingFake()
    )
    ctx = str(FIXTURES / "memmcp" / "episode_summary.ctx")

    assert main(["run", ctx, "--run-id", "ctx-failed"]) == 1
    cached = load_run(str(tmp_path), "ctx-failed")
    assert cached is not None
    assert cached["status"] == "error"
    assert any(event["type"] == "Failed" for event in cached["events"])
