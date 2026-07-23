"""Tests for `julep run --env` routing (julep.cli.temporal_run).

Two paths:

* ``local`` env routes to the existing in-memory runner (resolve_agent +
  run_agent_local) and returns a RunOutcome carrying projection events. No
  Temporal involved.
* a non-local (cloud) env loads the *deployed* DeployRecord from the committed
  ledger and replays it via ``run_flow`` against that env's Temporal.

INTEGRATION-PENDING: the cloud path is NOT exercised against a live Temporal
here. ``temporalio`` is not even installed in this environment. Instead we
inject a fake async client whose ``execute_workflow`` records the args
``run_flow`` passes it and returns a canned result. This proves the plumbing
(deployed flow_json + the env's task_queue reach ``run_flow``) without a
broker; an end-to-end run against a real Temporal cluster is integration-pending.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from julep.cli.config import JulepConfig, EnvConfig, load_config
from julep.cli.ledger import DeployRecord, upsert_records
from julep.cli.runner import RunOutcome
from julep.cli.temporal_run import connect_temporal_client, run_on_env


# --------------------------------------------------------------------------- #
# local path
# --------------------------------------------------------------------------- #
def test_local_env_routes_to_in_memory_runner(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    local = cfg.envs["local"]
    assert local.temporal_address is None

    outcome = run_on_env(cfg, "triage", local, "TICKET-1")

    assert isinstance(outcome, RunOutcome)
    assert outcome.events, "expected projection events from the local runner"
    assert outcome.error is None


def test_local_env_surfaces_resolution_error(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    local = cfg.envs["local"]

    outcome = run_on_env(cfg, "does_not_exist", local, "X")

    assert isinstance(outcome, RunOutcome)
    assert outcome.error is not None


# --------------------------------------------------------------------------- #
# cloud path (fake client; integration-pending — see module docstring)
# --------------------------------------------------------------------------- #
@dataclass
class _Captured:
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class _FakeClient:
    """Stand-in for a connected ``temporalio.client.Client``.

    ``run_flow`` awaits ``client.execute_workflow(...)``; we record exactly what
    it was handed and return a canned result, so no broker is needed.
    """

    def __init__(self, result: Any) -> None:
        self._result = result
        self.calls: list[_Captured] = []

    async def execute_workflow(self, *args: Any, **kwargs: Any) -> Any:
        self.calls.append(_Captured(args=args, kwargs=kwargs))
        return self._result


def _cloud_cfg(tmp_path: Path) -> JulepConfig:
    return JulepConfig(
        root=tmp_path,
        envs={
            "staging": EnvConfig(
                name="staging",
                temporal_address="temporal.staging:7233",
                temporal_namespace="staging-ns",
                task_queue="julep-staging-queue",
                artifacts=str(tmp_path / ".julep" / "artifacts"),
            )
        },
    )


def _deploy_triage(tmp_path: Path) -> dict[str, Any]:
    flow_json: dict[str, Any] = {"name": "triage", "nodes": ["lookup", "think"]}
    manifest_json: dict[str, Any] = {"agent": "triage", "caps": []}
    bundle_ref = [{"path": "triage.py", "hash": "sha256:deadbeef"}]
    rec = DeployRecord(
        agent="triage",
        artifact_hash="sha256:deadbeef",
        flow_json=flow_json,
        manifest_json=manifest_json,
        bundle_ref=bundle_ref,
        deployed_at="2026-06-23T00:00:00+00:00",
    )
    upsert_records(tmp_path, "staging", [rec])
    return {"flow_json": flow_json, "manifest_json": manifest_json, "bundle_ref": bundle_ref}


def test_cloud_env_replays_deployed_flow_via_run_flow(tmp_path: Path) -> None:
    cfg = _cloud_cfg(tmp_path)
    deployed = _deploy_triage(tmp_path)

    fake = _FakeClient(result={"output": "ok"})
    captured: dict[str, Any] = {}

    def _spy_run_flow(client: Any, flow_json: Any, manifest_json: Any, **kwargs: Any) -> Any:
        captured["client"] = client
        captured["flow_json"] = flow_json
        captured["manifest_json"] = manifest_json
        captured["kwargs"] = kwargs

        async def _call() -> Any:
            return await client.execute_workflow(
                "FlowWorkflow.run",
                flow_json,
                id=kwargs["session_id"],
                task_queue=kwargs["task_queue"],
            )

        return _call()

    result = run_on_env(
        cfg,
        "triage",
        cfg.envs["staging"],
        {"ticket": "T-9"},
        client=fake,
        run_flow=_spy_run_flow,
    )

    # run_flow received the *deployed* IR + the env's task_queue.
    assert captured["client"] is fake
    assert captured["flow_json"] == deployed["flow_json"]
    assert captured["manifest_json"] == deployed["manifest_json"]
    assert captured["kwargs"]["task_queue"] == "julep-staging-queue"
    assert captured["kwargs"]["bundle"] == deployed["bundle_ref"]
    assert captured["kwargs"]["input"] == {"ticket": "T-9"}
    assert isinstance(captured["kwargs"]["session_id"], str) and captured["kwargs"]["session_id"]

    # the fake client actually ran and its result is returned to the caller.
    assert result == {"output": "ok"}
    assert fake.calls and fake.calls[0].kwargs["task_queue"] == "julep-staging-queue"


def test_cloud_env_rejects_oversized_run_secret_map_before_start(tmp_path: Path) -> None:
    cfg = _cloud_cfg(tmp_path)
    _deploy_triage(tmp_path)
    called = False

    def unexpected_start(*_args: Any, **_kwargs: Any) -> Any:
        nonlocal called
        called = True
        return None

    with pytest.raises(ValueError, match="32 entries"):
        run_on_env(
            cfg,
            "triage",
            cfg.envs["staging"],
            None,
            client=_FakeClient(result=None),
            run_flow=unexpected_start,
            secrets={f"secret-{index}": "x" for index in range(33)},
        )
    assert called is False


def test_cloud_replay_passes_pinned_pures_from_ledger(tmp_path: Path) -> None:
    cfg = _cloud_cfg(tmp_path)
    flow_json: dict[str, Any] = {"name": "triage", "nodes": ["lookup"]}
    rec = DeployRecord(
        agent="triage",
        artifact_hash="sha256:deadbeef",
        flow_json=flow_json,
        manifest_json={"agent": "triage"},
        bundle_ref=None,
        pinned_pures={"std.init": "sha256:aa", "std.merge": "sha256:bb"},
        deployed_at="2026-06-23T00:00:00+00:00",
    )
    upsert_records(tmp_path, "staging", [rec])

    captured: dict[str, Any] = {}

    def _spy_run_flow(client: Any, flow_json: Any, manifest_json: Any, **kwargs: Any) -> Any:
        captured["kwargs"] = kwargs
        return {"output": "ok"}

    run_on_env(
        cfg,
        "triage",
        cfg.envs["staging"],
        None,
        client=_FakeClient(result=None),
        run_flow=_spy_run_flow,
    )

    # The deploy-time pinned pure hashes reach run_flow so worker-side pure
    # drift is detected on replay.
    assert captured["kwargs"]["pinned_pures"] == {"std.init": "sha256:aa", "std.merge": "sha256:bb"}


def test_non_local_env_without_temporal_address_raises(tmp_path: Path) -> None:
    """A non-'local' env missing temporal_address must NOT silently run source."""
    cfg = JulepConfig(
        root=tmp_path,
        envs={"staging": EnvConfig(name="staging", temporal_address=None)},
    )

    with pytest.raises(ValueError, match="temporal_address"):
        run_on_env(
            cfg,
            "triage",
            cfg.envs["staging"],
            None,
            run_flow=lambda *a, **k: None,  # must never be reached
        )


def test_connect_temporal_client_required_encryption_rejects_missing_keys(
    monkeypatch,
) -> None:
    monkeypatch.setenv("TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED", "true")
    monkeypatch.delenv("TEMPORAL_PAYLOAD_KEYS", raising=False)
    monkeypatch.delenv("TEMPORAL_PAYLOAD_KEY_ID", raising=False)

    with pytest.raises(ValueError, match="payload encryption is required"):
        connect_temporal_client(
            EnvConfig(name="staging", temporal_address="temporal:7233")
        )


def test_cloud_env_errors_when_agent_not_deployed(tmp_path: Path) -> None:
    cfg = _cloud_cfg(tmp_path)
    fake = _FakeClient(result=None)

    with pytest.raises(Exception) as excinfo:
        run_on_env(
            cfg,
            "triage",  # never deployed to staging
            cfg.envs["staging"],
            None,
            client=fake,
            run_flow=lambda *a, **k: None,  # must never be reached
        )

    msg = str(excinfo.value).lower()
    assert "triage" in msg
    assert "deploy" in msg or "not" in msg
    assert not fake.calls, "run_flow must not be invoked for an undeployed agent"
