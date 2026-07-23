from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Literal, cast

import pytest
from starlette.testclient import TestClient

import julep.server as server
from julep import Budget, arr, call, deploy, human_gate, ident, mcp, register_pure, seq, sub
from julep.app_deploy import ApplicationRelease, PipelineRelease
from julep.execution.effects import WorkerContext
from julep.execution.projection_store import InMemoryExecutionStore
from julep.freeze import McpSnapshot
from julep.dotctx import Reasoner
from julep.dsl import app as agent_app
from julep.registry import Registry
from julep.server.settings import ServerSettings

from conftest import read_snapshot


LOCAL_HEADERS = {"Authorization": "Bearer local-dev"}


def _release(
    flow: Any,
    *,
    snapshot: McpSnapshot | None = None,
    mcp_preflight_policy: Literal["pin", "names", "off"] = "pin",
    max_call_limits: dict[str, int] | None = None,
) -> ApplicationRelease:
    deployment = deploy(flow, snapshot or McpSnapshot())
    return ApplicationRelease(
        application="local-test",
        application_artifact_hash="sha256:" + "a" * 64,
        worker_image="registry.example/local-test@sha256:" + "b" * 64,
        pipelines=(
            PipelineRelease(
                name="main",
                lane="local",
                artifact_hash=deployment.artifact_hash,
                flow_json=deployment.flow_json,
                manifest_json=deployment.manifest_json,
                pinned_pures={},
                bundle_ref=None,
                eval_packages=(),
                max_call_limits=max_call_limits or {},
                mcp_preflight_policy=mcp_preflight_policy,
            ),
        ),
    )


def _continue_twice(value: dict[str, int]) -> Any:
    from julep.continuation import continue_with

    n = value.get("n", 0)
    return continue_with({"n": n + 1}) if n < 2 else {"done": n}


register_pure("tests.local.continue_twice", _continue_twice)


def _publish_and_activate(client: TestClient, release: ApplicationRelease) -> None:
    published = client.post(
        "/v1/releases",
        content=release.manifest_bytes,
        headers={**LOCAL_HEADERS, "Content-Type": "application/json"},
    )
    assert published.status_code == 201, published.text

    activated = client.post(
        "/v1/deployments",
        json={"lane": "local", "release": release.release_hash},
        headers=LOCAL_HEADERS,
    )
    assert activated.status_code == 200, activated.text


def _start(
    client: TestClient,
    *,
    key: str,
    input: Any,
    secrets: dict[str, str] | None = None,
) -> Any:
    body: dict[str, Any] = {"pipeline": "main", "input": input}
    if secrets is not None:
        body["secrets"] = secrets
    return client.post(
        "/v1/runs",
        json=body,
        headers={**LOCAL_HEADERS, "Idempotency-Key": key},
    )


def _wait_for_gates(client: TestClient, run_id: str) -> list[str]:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        response = client.get(f"/v1/runs/{run_id}/gates", headers=LOCAL_HEADERS)
        assert response.status_code == 200, response.text
        gates = response.json()["gates"]
        if gates:
            assert all(isinstance(cid, str) for cid in gates)
            return cast(list[str], gates)
        time.sleep(0.01)
    pytest.fail("local run did not open its human gate")


def _wait_for_result(client: TestClient, run_id: str) -> dict[str, Any]:
    response = client.get(
        f"/v1/runs/{run_id}/result?wait_s=2",
        headers=LOCAL_HEADERS,
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def test_create_local_app_needs_no_postgres_or_temporal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_store(_settings: ServerSettings) -> Any:
        raise AssertionError("local mode must not construct a PostgreSQL store")

    async def unexpected_gateway(_settings: ServerSettings) -> Any:
        raise AssertionError("local mode must not connect to Temporal")

    monkeypatch.setattr(ServerSettings, "build_store", unexpected_store)
    monkeypatch.setattr(ServerSettings, "build_gateway", unexpected_gateway)

    app = server.create_local_app(project_root=tmp_path, host="127.0.0.1")
    assert isinstance(app.state.store, InMemoryExecutionStore)

    with TestClient(app) as client:
        assert client.get("/v1/health").json() == {"status": "ok"}
        ready = client.get("/v1/ready", headers=LOCAL_HEADERS)

    assert ready.status_code == 200, ready.text
    assert ready.json() == {
        "status": "ready",
        "checks": {"store": "ok", "artifacts": "ok", "temporal": "ok"},
    }
    assert (tmp_path / ".julep" / "artifacts").is_dir()


def test_local_dev_key_is_loopback_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="(?i)(loopback|API key)"):
        server.create_local_app(project_root=tmp_path, host="0.0.0.0")


def test_echo_flow_runs_through_publish_activate_and_run_api(tmp_path: Path) -> None:
    app = server.create_local_app(project_root=tmp_path)
    release = _release(ident())
    payload = {"question": "can this run locally?"}

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        started = _start(client, key="local-ident", input=payload)
        assert started.status_code == 201, started.text
        run = started.json()
        assert run["release_hash"] == release.release_hash
        assert run["pipeline"] == "main"
        assert run["temporal_run_id"].startswith("local-")

        finished = _wait_for_result(client, run["run_id"])
        assert finished["run"]["status"] == "completed"
        assert finished["result"] == payload

        events = client.get(
            f"/v1/runs/{run['run_id']}/events",
            headers={**LOCAL_HEADERS, "Accept": "application/json"},
        )
        assert events.status_code == 200, events.text
        rows = events.json()["items"]
        assert any(row["type"] == "Planned" for row in rows)
        assert any(row["type"] == "Did" for row in rows)
        assert rows[-1]["attrs"]["terminal"] is True


def test_local_events_are_visible_while_waiting_for_human_signal(tmp_path: Path) -> None:
    app = server.create_local_app(project_root=tmp_path)
    release = _release(human_gate(prompt="approve local run", timeout_s=None))

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        started = _start(client, key="local-gate", input={"draft": 1})
        assert started.status_code == 201, started.text
        run_id = started.json()["run_id"]
        cid = _wait_for_gates(client, run_id)[0]

        active = client.get(
            f"/v1/runs/{run_id}/events",
            headers={**LOCAL_HEADERS, "Accept": "application/json"},
        )
        assert active.status_code == 200, active.text
        before = active.json()["items"]
        assert before
        assert any(row["type"] == "Planned" for row in before)
        assert not any(row.get("attrs", {}).get("terminal") is True for row in before)

        signal_value = {"approved": True, "reviewer": "local"}
        signaled = client.post(
            f"/v1/runs/{run_id}/signals/human",
            json={"cid": cid, "value": signal_value},
            headers=LOCAL_HEADERS,
        )
        assert signaled.status_code == 200, signaled.text

        finished = _wait_for_result(client, run_id)
        assert finished["run"]["status"] == "completed"
        assert finished["result"] == signal_value

        after = client.get(
            f"/v1/runs/{run_id}/events",
            headers={**LOCAL_HEADERS, "Accept": "application/json"},
        ).json()["items"]
        assert len(after) > len(before)
        assert after[-1]["attrs"]["terminal"] is True


@pytest.mark.parametrize(
    ("operation", "terminal_status"),
    [("cancel", "canceled"), ("terminate", "terminated")],
)
def test_local_blocked_run_can_be_stopped(
    tmp_path: Path,
    operation: str,
    terminal_status: str,
) -> None:
    app = server.create_local_app(project_root=tmp_path)
    release = _release(human_gate(prompt="wait forever", timeout_s=None))

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        started = _start(client, key=f"local-{operation}", input={"pending": True})
        assert started.status_code == 201, started.text
        run_id = started.json()["run_id"]
        _wait_for_gates(client, run_id)

        stopped = client.post(
            f"/v1/runs/{run_id}/{operation}",
            headers=LOCAL_HEADERS,
        )
        assert stopped.status_code == 200, stopped.text

        finished = _wait_for_result(client, run_id)
        assert finished["run"]["status"] == terminal_status
        assert finished["result"] is None


def test_echo_mode_simulates_the_frozen_mcp_surface(tmp_path: Path) -> None:
    app = server.create_local_app(project_root=tmp_path)
    release = _release(call(mcp("srv", "echo")), snapshot=read_snapshot("echo"))
    payload = {"message": "MCP stays offline"}

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        started = _start(client, key="local-mcp", input=payload)
        assert started.status_code == 201, started.text
        finished = _wait_for_result(client, started.json()["run_id"])

    assert finished["run"]["status"] == "completed"
    assert finished["result"] == payload


def test_echo_mode_rejects_run_secrets(tmp_path: Path) -> None:
    app = server.create_local_app(project_root=tmp_path)
    release = _release(call(mcp("srv", "echo")), snapshot=read_snapshot("echo"))

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        response = _start(
            client,
            key="local-secret",
            input={"message": "do not run"},
            secrets={"tracker-token": "test-only-value"},
        )

    assert response.status_code == 400, response.text
    detail = response.json()["detail"].lower()
    assert "local" in detail
    assert "secret" in detail


def test_configured_context_factory_executes_real_mcp_effect(tmp_path: Path) -> None:
    factory_calls = 0
    effect_calls: list[dict[str, Any]] = []

    async def configured_mcp(
        server_name: str,
        tool_name: str,
        value: Any,
        cid: str,
        principal: dict[str, Any] | None,
        secrets: dict[str, str] | None,
        input_schema_validated: bool,
    ) -> Any:
        effect_calls.append(
            {
                "server": server_name,
                "tool": tool_name,
                "value": value,
                "cid": cid,
                "principal": principal,
                "secrets": secrets,
                "input_schema_validated": input_schema_validated,
            }
        )
        return {"source": "configured-context", "input": value}

    def context_factory() -> WorkerContext:
        nonlocal factory_calls
        factory_calls += 1
        return WorkerContext(mcp_call=configured_mcp)

    app = server.create_local_app(
        project_root=tmp_path,
        context_factory=context_factory,
    )
    release = _release(
        call(mcp("srv", "echo")),
        snapshot=read_snapshot("echo"),
        mcp_preflight_policy="off",
    )
    payload = {"message": "use the configured caller"}

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        started = _start(client, key="configured-context", input=payload)
        assert started.status_code == 201, started.text
        finished = _wait_for_result(client, started.json()["run_id"])

    assert factory_calls == 1
    assert finished["result"] == {
        "source": "configured-context",
        "input": payload,
    }
    assert len(effect_calls) == 1
    assert effect_calls[0]["server"] == "srv"
    assert effect_calls[0]["tool"] == "echo"
    assert effect_calls[0]["value"] == payload
    assert effect_calls[0]["cid"]
    assert effect_calls[0]["principal"] == {"key": "local-dev"}
    assert effect_calls[0]["secrets"] is None
    assert effect_calls[0]["input_schema_validated"] is True


def test_local_control_plane_state_is_ephemeral_but_artifacts_persist(
    tmp_path: Path,
) -> None:
    first_app = server.create_local_app(project_root=tmp_path)
    release = _release(ident())

    with TestClient(first_app) as client:
        _publish_and_activate(client, release)
        started = _start(client, key="before-restart", input={"value": 7})
        assert started.status_code == 201, started.text
        run_id = started.json()["run_id"]
        assert _wait_for_result(client, run_id)["result"] == {"value": 7}

    digest = release.release_hash.removeprefix("sha256:")
    assert first_app.state.artifacts.has(digest)

    second_app = server.create_local_app(project_root=tmp_path)
    assert second_app.state.artifacts.has(digest)
    with TestClient(second_app) as client:
        releases = client.get("/v1/releases", headers=LOCAL_HEADERS)
        assert releases.status_code == 200, releases.text
        assert releases.json()["items"] == []

        missing_run = client.get(f"/v1/runs/{run_id}", headers=LOCAL_HEADERS)
        assert missing_run.status_code == 404


def test_configured_api_keys_replace_loopback_local_dev_fallback(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.julep.server]
api_keys = ["custom:custom-token:admin"]
""".strip(),
        encoding="utf-8",
    )
    app = server.create_local_app(project_root=tmp_path, host="0.0.0.0")

    with TestClient(app) as client:
        fallback = client.get("/v1/ready", headers=LOCAL_HEADERS)
        configured = client.get(
            "/v1/ready",
            headers={"Authorization": "Bearer custom-token"},
        )

    assert fallback.status_code == 401
    assert configured.status_code == 200, configured.text


def test_echo_continuations_cannot_reset_max_calls(tmp_path: Path) -> None:
    app = server.create_local_app(project_root=tmp_path)
    flow = seq(call(mcp("srv", "echo")), arr("std.continue_with"))
    release = _release(
        flow,
        snapshot=read_snapshot("echo"),
        max_call_limits={"srv/echo": 1},
    )

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        started = _start(client, key="continuation-max-calls", input={"n": 0})
        assert started.status_code == 201, started.text
        finished = _wait_for_result(client, started.json()["run_id"])

    assert finished["run"]["status"] == "failed"
    assert "maxCalls=1" in finished["run"]["error"]


def test_configured_subflow_continuations_settle_locally(tmp_path: Path) -> None:
    child = arr("tests.local.continue_twice")

    def context_factory() -> WorkerContext:
        return WorkerContext(
            subflows={
                "child": {
                    "flowJson": child.to_json(),
                    "manifestJson": {},
                    "pinnedPures": {},
                }
            }
        )

    app = server.create_local_app(
        project_root=tmp_path,
        context_factory=context_factory,
    )
    release = _release(sub("child"), snapshot=McpSnapshot())

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        started = _start(client, key="subflow-continuation", input={"n": 0})
        assert started.status_code == 201, started.text
        finished = _wait_for_result(client, started.json()["run_id"])

    assert finished["run"]["status"] == "completed"
    assert finished["result"] == {"done": 2}


def test_configured_app_can_reenter_its_lifespan(tmp_path: Path) -> None:
    factory_calls = 0

    async def configured_mcp(
        _server: str,
        _tool: str,
        value: Any,
        _cid: str,
        _principal: dict[str, Any] | None,
        _secrets: dict[str, str] | None,
        _input_schema_validated: bool,
    ) -> Any:
        return value

    def context_factory() -> WorkerContext:
        nonlocal factory_calls
        factory_calls += 1
        return WorkerContext(mcp_call=configured_mcp)

    app = server.create_local_app(
        project_root=tmp_path,
        context_factory=context_factory,
    )
    release = _release(
        call(mcp("srv", "echo")),
        snapshot=read_snapshot("echo"),
        mcp_preflight_policy="off",
    )
    with TestClient(app) as first:
        _publish_and_activate(first, release)
        started = _start(first, key="first-lifespan", input={"run": 1})
        assert _wait_for_result(first, started.json()["run_id"])["result"] == {
            "run": 1
        }

    with TestClient(app) as second:
        started = _start(second, key="second-lifespan", input={"run": 2})
        assert _wait_for_result(second, started.json()["run_id"])["result"] == {
            "run": 2
        }

    assert factory_calls == 2


def test_failed_context_startup_is_transactional(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory_calls = 0

    def context_factory() -> WorkerContext:
        nonlocal factory_calls
        factory_calls += 1
        if factory_calls == 1:
            raise RuntimeError("factory unavailable")
        return WorkerContext()

    monkeypatch.setenv("JULEP_ARTIFACT_STORE_URL", "file:///before-local")
    app = server.create_local_app(
        project_root=tmp_path,
        context_factory=context_factory,
    )

    with pytest.raises(RuntimeError, match="factory unavailable"):
        with TestClient(app):
            pass
    assert os.environ["JULEP_ARTIFACT_STORE_URL"] == "file:///before-local"

    with TestClient(app) as client:
        ready = client.get("/v1/ready", headers=LOCAL_HEADERS)
        assert ready.status_code == 200, ready.text

    assert factory_calls == 2
    assert os.environ["JULEP_ARTIFACT_STORE_URL"] == "file:///before-local"


def test_configured_agent_inherits_parent_max_calls(tmp_path: Path) -> None:
    effect_calls = 0
    registry = Registry()
    registry.register_reasoner(Reasoner("local.agent", "test:model"))

    async def configured_mcp(
        _server: str,
        _tool: str,
        value: Any,
        _cid: str,
        _principal: dict[str, Any] | None,
        _secrets: dict[str, str] | None,
        _input_schema_validated: bool,
    ) -> Any:
        nonlocal effect_calls
        effect_calls += 1
        return value

    async def configured_llm(
        _reasoner: Reasoner,
        value: Any,
        _principal: dict[str, Any] | None,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        return {"tool": "srv/echo", "input": value["input"]}

    def context_factory() -> WorkerContext:
        return WorkerContext(
            mcp_call=configured_mcp,
            llm=configured_llm,
            registry=registry,
        )

    flow = seq(
        call(mcp("srv", "echo")),
        agent_app(
            "local.agent",
            tools=["srv/echo"],
            budget=Budget(cost=1000),
        ),
    )
    app = server.create_local_app(
        project_root=tmp_path,
        context_factory=context_factory,
    )
    release = _release(
        flow,
        snapshot=read_snapshot("echo"),
        mcp_preflight_policy="off",
        max_call_limits={"srv/echo": 1},
    )

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        started = _start(client, key="agent-max-calls", input={"value": 1})
        assert started.status_code == 201, started.text
        finished = _wait_for_result(client, started.json()["run_id"])

    assert finished["run"]["status"] == "completed"
    assert finished["result"]["status"] == "denied"
    assert finished["result"]["reason"] == "tool 'srv/echo' exceeded maxCalls=1"
    assert effect_calls == 1
