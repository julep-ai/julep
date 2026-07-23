from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from julep.cli.config import EnvConfig, JulepConfig
from julep.cli.dev import (
    DevStackError,
    build_dev_stack_plan,
    render_dev_stack_plan,
    run_dev_stack,
)
from julep.cli.keygen import generate_dev_environment
from julep.cli.main import app


def _source_env() -> dict[str, str]:
    counter = 0

    def random_bytes(_size: int) -> bytes:
        nonlocal counter
        counter += 1
        return bytes([counter]) * 32

    values = generate_dev_environment(random_bytes=random_bytes)
    values["JULEP_EXECUTION_STORE_DSN"] = "postgresql://localhost/julep"
    return values


def _plan(tmp_path: Path, **kwargs: Any):
    source = _source_env()
    cfg = JulepConfig(root=tmp_path, envs={})
    env = EnvConfig(
        name="local",
        release_store=(tmp_path / "artifacts").as_uri(),
        worker_context_factory="project.worker:context",
    )
    return build_dev_stack_plan(
        cfg,
        env,
        api_url="http://127.0.0.1:8600",
        api_key=source["JULEP_API_KEY"],
        source_env=source,
        python="python",
        **kwargs,
    )


def test_build_dev_stack_plan_wires_shared_contract_and_redacts_key(tmp_path: Path) -> None:
    source = _source_env()
    cfg = JulepConfig(root=tmp_path, envs={})
    env = EnvConfig(
        name="local",
        release_store=(tmp_path / "artifacts").as_uri(),
        worker_context_factory="project.worker:context",
    )
    plan = build_dev_stack_plan(
        cfg,
        env,
        api_url="http://127.0.0.1:8600",
        api_key=source["JULEP_API_KEY"],
        source_env=source,
        python="python",
    )
    assert plan.temporal is not None
    assert plan.temporal.argv[-2:] == ("--port", "7233")
    assert plan.api.environment["JULEP_ARTIFACT_STORE_URL"] == env.release_store
    assert plan.worker.environment["WORKER_CONTEXT_FACTORY"] == "project.worker:context"
    assert plan.worker.environment["JULEP_API_URL"] == "http://127.0.0.1:8600"
    assert plan.worker.environment["JULEP_API_KEY"] == source["JULEP_WORKER_API_KEY"]
    assert "JULEP_API_KEY" not in plan.api.environment
    rendered = render_dev_stack_plan(plan)
    assert "--api-key" not in rendered
    assert source["JULEP_API_KEY"] not in rendered


def test_build_dev_stack_plan_rejects_non_admin_key(tmp_path: Path) -> None:
    source = _source_env()
    source["JULEP_API_KEYS"] = "client:" + source["JULEP_API_KEY"] + ":client"
    cfg = JulepConfig(root=tmp_path, envs={})
    env = EnvConfig(
        name="local",
        release_store=(tmp_path / "artifacts").as_uri(),
        worker_context_factory="project.worker:context",
    )
    with pytest.raises(DevStackError, match="admin"):
        build_dev_stack_plan(
            cfg,
            env,
            api_url="http://127.0.0.1:8600",
            api_key=source["JULEP_API_KEY"],
            source_env=source,
        )


def test_build_dev_stack_plan_rejects_non_worker_vault_key(tmp_path: Path) -> None:
    source = _source_env()
    source["JULEP_WORKER_API_KEY"] = source["JULEP_API_KEY"]
    cfg = JulepConfig(root=tmp_path, envs={})
    env = EnvConfig(
        name="local",
        release_store=(tmp_path / "artifacts").as_uri(),
        worker_context_factory="project.worker:context",
    )
    with pytest.raises(DevStackError, match="worker entry"):
        build_dev_stack_plan(
            cfg,
            env,
            api_url="http://127.0.0.1:8600",
            api_key=source["JULEP_API_KEY"],
            source_env=source,
        )


class _Process:
    def __init__(self) -> None:
        self.returncode: int | None = None
        self.environment: dict[str, str] = {}
        self.terminated = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode or 0


def test_run_dev_stack_starts_one_worker_per_queue_and_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path, start_temporal=False)
    processes: list[_Process] = []

    def popen(_argv: Any, *, cwd: Path, env: dict[str, str]) -> _Process:
        assert cwd == tmp_path
        process = _Process()
        process.environment = env
        processes.append(process)
        return process

    calls = 0

    def sleep(_seconds: float) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt

    monkeypatch.setattr("julep.cli.dev.time.sleep", sleep)
    run_dev_stack(
        plan,
        popen=popen,
        publish=lambda _plan: (
            ("summary", "summary-rabc"),
            ("write", "write-rabc"),
        ),
        wait_temporal=lambda *_args, **_kwargs: None,
        wait_api=lambda *_args, **_kwargs: None,
    )
    assert len(processes) == 3  # API + one worker for each lane.
    assert [process.environment.get("TEMPORAL_TASK_QUEUE") for process in processes] == [
        None,
        "summary-rabc",
        "write-rabc",
    ]
    assert all(process.terminated for process in processes)


def _write_project(tmp_path: Path) -> None:
    (tmp_path / "julep.toml").write_text(
        "\n".join(
            (
                "[env.local]",
                f'release_store = "{(tmp_path / "artifacts").as_uri()}"',
                'worker_context_factory = "project.worker:context"',
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_dev_up_cli_dry_run_uses_generated_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_project(tmp_path)
    source = _source_env()
    source["JULEP_EXECUTION_STORE_DSN"] = "postgresql://localhost/julep"
    for name, value in source.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["dev", "up", "--dry-run"])

    assert result.exit_code == 0, result.output
    assert "temporal server start-dev" in result.output
    assert "serve api --migrate" in result.output
    assert "publish  env=local" in result.output
    assert "one per published queue" in result.output
    assert source["JULEP_API_KEY"] not in result.output


def test_dev_up_cli_runs_validated_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_project(tmp_path)
    source = _source_env()
    source["JULEP_EXECUTION_STORE_DSN"] = "postgresql://localhost/julep"
    for name, value in source.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(tmp_path)
    captured: list[Any] = []
    monkeypatch.setattr("julep.cli.dev.run_dev_stack", captured.append)

    result = CliRunner().invoke(
        app,
        ["dev", "up", "--no-start-temporal", "--no-publish", "--no-worker"],
    )

    assert result.exit_code == 0, result.output
    assert len(captured) == 1
    assert captured[0].temporal is None
    assert captured[0].publish_release is False
    assert captured[0].start_workers is False
