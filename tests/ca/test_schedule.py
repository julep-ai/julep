from __future__ import annotations

import asyncio
import dataclasses
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from composable_agents import HAVE_TEMPORAL
from composable_agents.ca import cli
from composable_agents.ca.config import CaConfig, EnvConfig, ScheduleConfig, load_config
from composable_agents.ca.ledger import DeployRecord, upsert_records
from composable_agents.ca.schedule import (
    apply_schedules,
    build_schedule,
    fetch_server_schedules,
    remove_schedule,
    schedule_drift,
    schedule_id,
)
from composable_agents.ca.temporal_run import build_flow_start_args, run_on_env


def _cloud_env(tmp_path: Path) -> EnvConfig:
    return EnvConfig(
        name="staging",
        temporal_address="127.0.0.1:7233",
        temporal_namespace="default",
        task_queue="ca-staging-queue",
        cas=str(tmp_path / ".ca" / "cas"),
    )


def _cloud_cfg(tmp_path: Path) -> CaConfig:
    return CaConfig(root=tmp_path, envs={"staging": _cloud_env(tmp_path)})


def _deploy_record(
    tmp_path: Path,
    *,
    agent: str = "rollups.hourly",
    env: str = "staging",
) -> DeployRecord:
    record = DeployRecord(
        agent=agent,
        artifact_hash="sha256:deadbeef",
        flow_json={"name": agent, "nodes": ["load", "summarize"]},
        manifest_json={"agent": agent, "caps": []},
        bundle_ref=[{"path": "rollups.py", "hash": "sha256:bundle"}],
        pinned_pures={"std.init": "sha256:aa", "std.merge": "sha256:bb"},
        deployed_at="2026-07-02T00:00:00+00:00",
    )
    upsert_records(tmp_path, env, [record])
    return record


def test_schedule_parse_defaults(tmp_path: Path) -> None:
    (tmp_path / "ca.toml").write_text(
        '[schedule.hourly-rollup]\ncron = "0 * * * *"\nflow = "rollups.hourly"\n',
        encoding="utf-8",
    )

    cfg = load_config(tmp_path)
    sched = cfg.schedules["hourly-rollup"]

    assert sched.cron == "0 * * * *"
    assert sched.flow == "rollups.hourly"
    assert sched.input is None
    assert sched.env == "local"
    assert sched.paused is False


def test_schedule_parse_full(tmp_path: Path) -> None:
    (tmp_path / "ca.toml").write_text(
        "[schedule.hourly-rollup]\n"
        'cron = "0 * * * *"\n'
        'flow = "rollups.hourly"\n'
        'input = { a = 1, b = "x" }\n'
        'env = "staging"\n'
        "paused = true\n",
        encoding="utf-8",
    )

    sched = load_config(tmp_path).schedules["hourly-rollup"]

    assert sched.input == {"a": 1, "b": "x"}
    assert sched.env == "staging"
    assert sched.paused is True


def test_schedule_parse_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ca.schedule.nightly]\ncron = "0 0 * * *"\nflow = "rollups.nightly"\n',
        encoding="utf-8",
    )

    sched = load_config(tmp_path).schedules["nightly"]

    assert sched.cron == "0 0 * * *"
    assert sched.flow == "rollups.nightly"


def test_bad_cron_field_count_teaching_error(tmp_path: Path) -> None:
    (tmp_path / "ca.toml").write_text(
        '[schedule.x]\ncron = "0 * * *"\nflow = "f"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="5 or 6"):
        load_config(tmp_path)

    (tmp_path / "ca.toml").write_text(
        '[schedule.x]\ncron = "0 * * * * * *"\nflow = "f"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="5 or 6"):
        load_config(tmp_path)

    (tmp_path / "ca.toml").write_text(
        '[schedule.x]\ncron = "0 * * * *"\nflow = "f"\n',
        encoding="utf-8",
    )
    load_config(tmp_path)

    (tmp_path / "ca.toml").write_text(
        '[schedule.x]\ncron = "0 * * * * 2026"\nflow = "f"\n',
        encoding="utf-8",
    )
    load_config(tmp_path)


def test_bad_cron_token_teaching_error(tmp_path: Path) -> None:
    (tmp_path / "ca.toml").write_text(
        '[schedule.x]\ncron = "0 * * * !!!"\nflow = "f"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not a valid cron token"):
        load_config(tmp_path)


def test_missing_cron_or_flow_teaching_error(tmp_path: Path) -> None:
    (tmp_path / "ca.toml").write_text('[schedule.x]\nflow = "f"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="requires a 'cron'"):
        load_config(tmp_path)

    (tmp_path / "ca.toml").write_text(
        '[schedule.x]\ncron = "* * * * *"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="requires a 'flow'"):
        load_config(tmp_path)


def test_paused_non_bool_teaching_error(tmp_path: Path) -> None:
    (tmp_path / "ca.toml").write_text(
        '[schedule.x]\ncron = "0 * * * *"\nflow = "f"\npaused = "false"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="'paused' must be a boolean"):
        load_config(tmp_path)


def test_env_non_string_teaching_error(tmp_path: Path) -> None:
    (tmp_path / "ca.toml").write_text(
        '[schedule.x]\ncron = "0 * * * *"\nflow = "f"\nenv = 3\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="'env' must be a string"):
        load_config(tmp_path)


def test_schedule_id_shape() -> None:
    assert schedule_id("prod", "hourly") == "ca:prod:hourly"


def test_schedule_drift_matrix() -> None:
    configured = [
        ScheduleConfig(name="aaa", cron="0 * * * *", flow="f", env="staging"),
        ScheduleConfig(name="bbb", cron="15 * * * *", flow="f", env="staging"),
        ScheduleConfig(name="ccc", cron="30 * * * *", flow="f", env="staging"),
    ]
    server = {
        "ca:staging:aaa": {"cron": "0 * * * *", "paused": False},
        "ca:staging:bbb": {"cron": "45 * * * *", "paused": False},
        "ca:staging:orphaned": {"cron": "0 0 * * *", "paused": False},
        "ca:prod:ignored": {"cron": "0 0 * * *", "paused": False},
    }

    rows = schedule_drift("staging", configured, server)

    assert [(row.name, row.state) for row in rows] == [
        ("aaa", "in-sync"),
        ("bbb", "drift"),
        ("ccc", "missing"),
        ("orphaned", "orphan"),
    ]
    assert "server cron" in rows[1].detail
    assert "ca schedule apply" in rows[2].detail
    assert "not in config" in rows[3].detail


def test_build_flow_start_args_primitives(tmp_path: Path) -> None:
    env = _cloud_env(tmp_path)
    record = _deploy_record(tmp_path)

    sa = build_flow_start_args(record, env, {"k": "v"})

    assert sa.flow_json == record.flow_json
    assert sa.manifest_json == record.manifest_json
    assert sa.bundle == record.bundle_ref
    assert sa.pinned_pures == record.pinned_pures
    assert sa.task_queue == env.task_queue
    assert sa.input == {"k": "v"}
    assert sa.session_id == f"ca:{env.name}:{record.agent}"


def test_apply_refuses_undeployed_flow(tmp_path: Path) -> None:
    cfg = _cloud_cfg(tmp_path)
    scheds = [
        ScheduleConfig(
            name="hourly-rollup",
            cron="0 * * * *",
            flow="rollups.hourly",
            env="staging",
        )
    ]

    with pytest.raises(ValueError, match="rollups.hourly.*deploy"):
        apply_schedules(cfg, cfg.envs["staging"], scheds, client=object())


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_apply_creates_then_updates_via_fake_client(tmp_path: Path) -> None:
    from temporalio.client import ScheduleAlreadyRunningError, ScheduleUpdate
    from temporalio.client import ScheduleOverlapPolicy

    cfg = _cloud_cfg(tmp_path)
    env = cfg.envs["staging"]
    record = _deploy_record(tmp_path)
    sched = ScheduleConfig(
        name="hourly-rollup",
        cron="0 * * * *",
        flow=record.agent,
        input={"a": 1},
        env=env.name,
        paused=True,
    )

    class _Handle:
        def __init__(self) -> None:
            self.updates: list[ScheduleUpdate] = []

        async def update(self, updater: Any) -> None:
            updated = updater(object())
            self.updates.append(updated)

    class _FakeClient:
        def __init__(self) -> None:
            self.created: list[tuple[str, Any]] = []
            self.handle = _Handle()
            self.raise_running = False
            self.handles: list[str] = []

        async def create_schedule(self, sid: str, schedule: Any) -> None:
            self.created.append((sid, schedule))
            if self.raise_running:
                raise ScheduleAlreadyRunningError()

        def get_schedule_handle(self, sid: str) -> _Handle:
            self.handles.append(sid)
            return self.handle

    fake = _FakeClient()

    assert apply_schedules(cfg, env, [sched], client=fake) == [("hourly-rollup", "created")]
    sid, obj = fake.created[0]

    assert sid == "ca:staging:hourly-rollup"
    assert obj.spec.cron_expressions == [sched.cron]
    assert obj.policy.overlap == ScheduleOverlapPolicy.SKIP
    assert obj.state.paused is True
    assert obj.state.note == "ca-managed cron=0 * * * *"
    flow_input = obj.action.args[0]
    assert flow_input.flow_json == record.flow_json
    assert flow_input.pinned_pures == record.pinned_pures
    assert flow_input.bundle == record.bundle_ref

    fake.raise_running = True
    assert apply_schedules(cfg, env, [sched], client=fake) == [("hourly-rollup", "updated")]

    assert fake.handles == ["ca:staging:hourly-rollup"]
    assert len(fake.handle.updates) == 1
    updated = fake.handle.updates[0]
    assert isinstance(updated, ScheduleUpdate)
    assert updated.schedule.spec.cron_expressions == [sched.cron]


def test_fetch_server_schedules_fake_client() -> None:
    class _Spec:
        cron_expressions: list[str] = []

    class _State:
        paused = True
        note = "ca-managed cron=0 * * * *"

    class _Sched:
        spec = _Spec()
        state = _State()

    class _Row:
        def __init__(self, sid: str, schedule: Any) -> None:
            self.id = sid
            self.schedule = schedule

    class _AsyncIter:
        def __init__(self, rows: list[Any]) -> None:
            self._rows = list(rows)

        def __aiter__(self) -> "_AsyncIter":
            return self

        async def __anext__(self) -> Any:
            if not self._rows:
                raise StopAsyncIteration
            return self._rows.pop(0)

    class _FakeClient:
        def __init__(self) -> None:
            self.listed = 0

        async def list_schedules(self) -> Any:
            self.listed += 1
            return _AsyncIter([_Row("ca:staging:hourly", _Sched())])

    fake = _FakeClient()
    server = fetch_server_schedules(EnvConfig(name="staging"), client=fake)

    assert fake.listed == 1
    assert server == {"ca:staging:hourly": {"cron": "0 * * * *", "paused": True}}


def test_drift_in_sync_when_server_cron_normalized_to_calendars() -> None:
    """Regression: Temporal returns cron as calendars + empty cron_expressions; the
    note carries the real cron so a just-applied schedule reads as in-sync, not drift."""

    class _Spec:
        cron_expressions: list[str] = []
        calendars = [object()]

    class _State:
        paused = False
        note = "ca-managed cron=0 * * * *"

    class _Sched:
        spec = _Spec()
        state = _State()

    class _Row:
        def __init__(self, sid: str, schedule: Any) -> None:
            self.id = sid
            self.schedule = schedule

    class _AsyncIter:
        def __init__(self, rows: list[Any]) -> None:
            self._rows = list(rows)

        def __aiter__(self) -> "_AsyncIter":
            return self

        async def __anext__(self) -> Any:
            if not self._rows:
                raise StopAsyncIteration
            return self._rows.pop(0)

    class _FakeClient:
        async def list_schedules(self) -> Any:
            return _AsyncIter([_Row("ca:staging:hourly-rollup", _Sched())])

    server = fetch_server_schedules(EnvConfig(name="staging"), client=_FakeClient())
    assert server == {"ca:staging:hourly-rollup": {"cron": "0 * * * *", "paused": False}}

    configured = [
        ScheduleConfig(name="hourly-rollup", cron="0 * * * *", flow="f", env="staging")
    ]
    rows = schedule_drift("staging", configured, server)
    assert [(r.name, r.state) for r in rows] == [("hourly-rollup", "in-sync")]


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_remove_schedule_fake_client() -> None:
    from temporalio.service import RPCError, RPCStatusCode

    env = EnvConfig(name="staging")

    class _OkHandle:
        def __init__(self) -> None:
            self.deleted = False

        async def delete(self) -> None:
            self.deleted = True

    class _RaisingHandle:
        def __init__(self, status: Any) -> None:
            self._status = status

        async def delete(self) -> None:
            raise RPCError("nope", self._status, b"")

    class _Client:
        def __init__(self, handle: Any) -> None:
            self._handle = handle
            self.requested: list[str] = []

        def get_schedule_handle(self, sid: str) -> Any:
            self.requested.append(sid)
            return self._handle

    ok = _Client(_OkHandle())
    assert remove_schedule(env, "hourly", client=ok) is True
    assert ok.requested == ["ca:staging:hourly"]

    missing = _Client(_RaisingHandle(RPCStatusCode.NOT_FOUND))
    assert remove_schedule(env, "hourly", client=missing) is False

    other = _Client(_RaisingHandle(RPCStatusCode.INTERNAL))
    with pytest.raises(RPCError):
        remove_schedule(env, "hourly", client=other)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_builder_equivalence_schedule_matches_run(tmp_path: Path) -> None:
    cfg = _cloud_cfg(tmp_path)
    env = cfg.envs["staging"]
    record = _deploy_record(tmp_path, agent="rollups.hourly")
    sched = ScheduleConfig(
        name="hourly-rollup",
        cron="0 * * * *",
        flow=record.agent,
        input={"k": "v"},
        env=env.name,
    )

    obj = build_schedule(record, env, sched)
    sched_fi = obj.action.args[0]

    class _CapClient:
        def __init__(self) -> None:
            self.captured: Any = None

        async def execute_workflow(
            self,
            workflow: Any,
            arg: Any,
            *,
            id: str,
            task_queue: str,
        ) -> Any:
            self.captured = arg
            return {"ok": True}

    cap = _CapClient()
    run_on_env(cfg, record.agent, env, sched.input, client=cap)
    run_fi = cap.captured

    def canon(value: Any) -> str:
        normalized = replace(value, session_id="X")
        return json.dumps(dataclasses.asdict(normalized), sort_keys=True, default=str)

    assert canon(sched_fi) == canon(run_fi)
    assert sched_fi.pinned_pures == record.pinned_pures
    assert sched_fi.bundle == record.bundle_ref


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_apply_ls_rm_integration(tmp_path: Path) -> None:
    from temporalio.service import RPCError, RPCStatusCode
    from temporalio.testing import WorkflowEnvironment

    try:
        env_ws = asyncio.run(asyncio.wait_for(WorkflowEnvironment.start_local(), timeout=60))
    except Exception as exc:  # noqa: BLE001 - local Temporal binary may be unavailable
        pytest.skip(f"Temporal local server unavailable: {exc}")
    try:
        cfg = _cloud_cfg(tmp_path)
        env = replace(cfg.envs["staging"], temporal_address=env_ws.client.service_client.config.target_host)
        record = _deploy_record(tmp_path)
        sched = ScheduleConfig(
            name="hourly-rollup",
            cron="0 0 1 1 *",
            flow=record.agent,
            env=env.name,
        )

        apply_schedules(cfg, env, [sched], client=env_ws.client)
        handle = env_ws.client.get_schedule_handle(schedule_id(env.name, sched.name))
        asyncio.run(asyncio.wait_for(handle.describe(), timeout=10))

        server = fetch_server_schedules(env, client=env_ws.client)
        sid = schedule_id(env.name, sched.name)
        assert sid in server
        assert server[sid]["paused"] is False
        assert server[sid]["cron"] == sched.cron
        rows = schedule_drift(env.name, [sched], server)
        assert [(r.name, r.state) for r in rows] == [(sched.name, "in-sync")]

        assert remove_schedule(env, sched.name, client=env_ws.client) is True
        with pytest.raises(RPCError) as excinfo:
            asyncio.run(asyncio.wait_for(handle.describe(), timeout=10))
        assert excinfo.value.status == RPCStatusCode.NOT_FOUND
    finally:
        asyncio.run(env_ws.shutdown())


def test_cli_schedule_apply_unknown_env_exits_2(sample_module: Path, capsys: Any, monkeypatch: Any) -> None:
    monkeypatch.chdir(sample_module)

    code = cli.main(["schedule", "apply", "--env", "nope"])
    err = capsys.readouterr().err

    assert code == 2
    assert "unknown env" in err
    assert "nope" in err


def test_cli_schedule_apply_local_no_temporal_exits_2(
    sample_module: Path,
    capsys: Any,
    monkeypatch: Any,
) -> None:
    monkeypatch.chdir(sample_module)

    code = cli.main(["schedule", "apply"])
    err = capsys.readouterr().err

    assert code == 2
    assert "temporal_address" in err
    assert "schedules require a Temporal env" in err


def test_cli_schedule_apply_no_schedules(tmp_path: Path, capsys: Any, monkeypatch: Any) -> None:
    (tmp_path / "ca.toml").write_text(
        '[env.staging]\ntemporal_address = "127.0.0.1:7233"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    code = cli.main(["schedule", "apply", "--env", "staging"])
    out = capsys.readouterr().out

    assert code == 0
    assert "no schedules configured for env 'staging'" in out
