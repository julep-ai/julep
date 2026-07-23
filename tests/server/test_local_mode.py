from __future__ import annotations

import os
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, cast

import pytest
from starlette.testclient import TestClient

import julep.server as server
from julep import (
    Budget,
    ContextPolicy,
    ContextScope,
    arr,
    call,
    deploy,
    human_gate,
    ident,
    mcp,
    register_pure,
    seq,
    sub,
)
from julep.app_deploy import ApplicationRelease, PipelineRelease
from julep.execution.effects import WorkerContext
from julep.execution.projection_store import InMemoryExecutionStore
from julep.freeze import McpSnapshot
from julep.dotctx import Reasoner
from julep.dsl import app as agent_app
from julep.registry import DEFAULT_REGISTRY, Registry
from julep.server.settings import ServerSettings

from conftest import read_snapshot


LOCAL_HEADERS = {"Authorization": "Bearer local-dev"}
CONFIGURED_HEADERS = {"Authorization": "Bearer configured-token"}


def _configure_context_auth(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.julep.server]
api_keys = ["configured-local:configured-token:admin"]
""".strip(),
        encoding="utf-8",
    )


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


def _publish_and_activate(
    client: TestClient,
    release: ApplicationRelease,
    *,
    headers: dict[str, str] = LOCAL_HEADERS,
) -> None:
    published = client.post(
        "/v1/releases",
        content=release.manifest_bytes,
        headers={**headers, "Content-Type": "application/json"},
    )
    assert published.status_code == 201, published.text

    activated = client.post(
        "/v1/deployments",
        json={"lane": "local", "release": release.release_hash},
        headers=headers,
    )
    assert activated.status_code == 200, activated.text


def _start(
    client: TestClient,
    *,
    key: str,
    input: Any,
    secrets: dict[str, str] | None = None,
    headers: dict[str, str] = LOCAL_HEADERS,
) -> Any:
    body: dict[str, Any] = {"pipeline": "main", "input": input}
    if secrets is not None:
        body["secrets"] = secrets
    return client.post(
        "/v1/runs",
        json=body,
        headers={**headers, "Idempotency-Key": key},
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


def _wait_for_result(
    client: TestClient,
    run_id: str,
    *,
    headers: dict[str, str] = LOCAL_HEADERS,
) -> dict[str, Any]:
    response = client.get(
        f"/v1/runs/{run_id}/result?wait_s=2",
        headers=headers,
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


def test_configured_context_requires_explicit_api_keys(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="explicitly configured API keys"):
        server.create_local_app(
            project_root=tmp_path,
            context_factory=lambda: WorkerContext(),
        )


def test_local_app_lifespans_reject_overlap_without_stealing_process_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    monkeypatch.setenv("JULEP_ARTIFACT_STORE_URL", "file:///before-local")
    first_app = server.create_local_app(project_root=first_root)
    second_app = server.create_local_app(project_root=second_root)

    with TestClient(first_app) as first_client:
        assert (
            os.environ["JULEP_ARTIFACT_STORE_URL"] == (first_root / ".julep" / "artifacts").as_uri()
        )
        with pytest.raises(RuntimeError, match="only one local Julep app lifespan"):
            with TestClient(second_app):
                pass
        assert (
            os.environ["JULEP_ARTIFACT_STORE_URL"] == (first_root / ".julep" / "artifacts").as_uri()
        )
        assert first_client.get("/v1/ready", headers=LOCAL_HEADERS).status_code == 200

    assert os.environ["JULEP_ARTIFACT_STORE_URL"] == "file:///before-local"
    with TestClient(second_app) as second_client:
        assert second_client.get("/v1/ready", headers=LOCAL_HEADERS).status_code == 200
        assert (
            os.environ["JULEP_ARTIFACT_STORE_URL"]
            == (second_root / ".julep" / "artifacts").as_uri()
        )
    assert os.environ["JULEP_ARTIFACT_STORE_URL"] == "file:///before-local"


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


def test_terminal_local_run_does_not_retain_raw_projection_values(
    tmp_path: Path,
) -> None:
    app = server.create_local_app(project_root=tmp_path)
    release = _release(ident())
    secret = "raw-local-secret-value"

    with TestClient(app) as client:
        _publish_and_activate(client, release)
        started = _start(
            client,
            key="local-projection-scrub",
            input={"api_key": secret},
        )
        assert started.status_code == 201, started.text
        finished = _wait_for_result(client, started.json()["run_id"])
        assert finished["result"] == {"api_key": "[REDACTED]"}

        gateway = app.state.gateway
        record = gateway._runs[started.json()["workflow_id"]]
        assert record.projection is not None
        assert vars(record.projection.values)["_values"] == {}
        projection_json = [event.to_json() for event in record.projection.events()]
        assert secret not in repr(projection_json)
        assert all("valueRef" not in event for event in projection_json)


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
    _configure_context_auth(tmp_path)
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
        _publish_and_activate(client, release, headers=CONFIGURED_HEADERS)
        started = _start(
            client,
            key="configured-context",
            input=payload,
            headers=CONFIGURED_HEADERS,
        )
        assert started.status_code == 201, started.text
        finished = _wait_for_result(
            client,
            started.json()["run_id"],
            headers=CONFIGURED_HEADERS,
        )

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
    assert effect_calls[0]["principal"] == {"key": "configured-local"}
    assert effect_calls[0]["secrets"] is None
    assert effect_calls[0]["input_schema_validated"] is True


def test_configured_context_surfaces_typed_preflight_refusal(tmp_path: Path) -> None:
    _configure_context_auth(tmp_path)
    app = server.create_local_app(
        project_root=tmp_path,
        context_factory=WorkerContext,
    )
    release = _release(ident(), mcp_preflight_policy="off")

    with TestClient(app) as client:
        _publish_and_activate(client, release, headers=CONFIGURED_HEADERS)
        started = _start(
            client,
            key="configured-unused-secret",
            input={"message": "preflight first"},
            secrets={"unused": "must-not-leak"},
            headers=CONFIGURED_HEADERS,
        )
        assert started.status_code == 201, started.text
        finished = _wait_for_result(
            client,
            started.json()["run_id"],
            headers=CONFIGURED_HEADERS,
        )

    assert finished["run"]["status"] == "failed"
    error = finished["run"]["error"]
    assert error.startswith("invalid_run_secret_binding: ")
    assert '"error": "invalid_run_secret_binding"' in error
    assert '"names": ["unused"]' in error
    assert "must-not-leak" not in error


def test_configured_context_scrubs_operator_secret_from_preflight_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from julep.secrets import register_secret_value

    operator_secret = "local-operator-value:/must-not-leak"
    register_secret_value(operator_secret)

    async def failing_preflight(_payload: Any) -> dict[str, Any]:
        raise RuntimeError(f"preflight echoed {operator_secret}")

    monkeypatch.setattr("julep.server.local.preflight_mcp", failing_preflight)
    _configure_context_auth(tmp_path)
    app = server.create_local_app(
        project_root=tmp_path,
        context_factory=WorkerContext,
    )
    release = _release(ident(), mcp_preflight_policy="off")

    with TestClient(app) as client:
        _publish_and_activate(client, release, headers=CONFIGURED_HEADERS)
        started = _start(
            client,
            key="configured-preflight-operator-secret",
            input={"message": "preflight first"},
            headers=CONFIGURED_HEADERS,
        )
        assert started.status_code == 201, started.text
        finished = _wait_for_result(
            client,
            started.json()["run_id"],
            headers=CONFIGURED_HEADERS,
        )

    assert finished["run"]["status"] == "failed"
    error = finished["run"]["error"]
    assert error.startswith("RuntimeError: preflight echoed ")
    assert operator_secret not in error


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
    _configure_context_auth(tmp_path)
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
        _publish_and_activate(client, release, headers=CONFIGURED_HEADERS)
        started = _start(
            client,
            key="subflow-continuation",
            input={"n": 0},
            headers=CONFIGURED_HEADERS,
        )
        assert started.status_code == 201, started.text
        finished = _wait_for_result(
            client,
            started.json()["run_id"],
            headers=CONFIGURED_HEADERS,
        )

    assert finished["run"]["status"] == "completed"
    assert finished["result"] == {"done": 2}


def test_configured_app_can_reenter_its_lifespan(tmp_path: Path) -> None:
    _configure_context_auth(tmp_path)
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
        _publish_and_activate(first, release, headers=CONFIGURED_HEADERS)
        started = _start(
            first,
            key="first-lifespan",
            input={"run": 1},
            headers=CONFIGURED_HEADERS,
        )
        assert _wait_for_result(
            first,
            started.json()["run_id"],
            headers=CONFIGURED_HEADERS,
        )["result"] == {"run": 1}

    with TestClient(app) as second:
        started = _start(
            second,
            key="second-lifespan",
            input={"run": 2},
            headers=CONFIGURED_HEADERS,
        )
        assert _wait_for_result(
            second,
            started.json()["run_id"],
            headers=CONFIGURED_HEADERS,
        )["result"] == {"run": 2}

    assert factory_calls == 2


def test_failed_context_startup_is_transactional(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_context_auth(tmp_path)
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
        ready = client.get("/v1/ready", headers=CONFIGURED_HEADERS)
        assert ready.status_code == 200, ready.text

    assert factory_calls == 2
    assert os.environ["JULEP_ARTIFACT_STORE_URL"] == "file:///before-local"


def test_configured_agent_inherits_parent_max_calls(tmp_path: Path) -> None:
    _configure_context_auth(tmp_path)
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
        _publish_and_activate(client, release, headers=CONFIGURED_HEADERS)
        started = _start(
            client,
            key="agent-max-calls",
            input={"value": 1},
            headers=CONFIGURED_HEADERS,
        )
        assert started.status_code == 201, started.text
        finished = _wait_for_result(
            client,
            started.json()["run_id"],
            headers=CONFIGURED_HEADERS,
        )

    assert finished["run"]["status"] == "failed"
    assert finished["result"] is None
    assert "AgentTerminalError: agent terminated with denied" in finished["run"]["error"]
    assert effect_calls == 1


def test_local_api_runs_transcript_scoped_native_tool_agent(tmp_path: Path) -> None:
    _configure_context_auth(tmp_path)
    registry = Registry()
    system_renderer = "tests/local-scoped/system"
    user_renderer = "tests/local-scoped/user"

    def render_system(context: Mapping[str, Any]) -> str:
        assert "trace" not in context
        return f"Category: {context['category']}"

    def render_user(context: Mapping[str, Any]) -> str:
        assert "trace" not in context
        return f"Investigate {context['category']}: {context['value']}"

    DEFAULT_REGISTRY.register_renderer(
        system_renderer, render_system, source="system/category"
    )
    DEFAULT_REGISTRY.register_renderer(
        user_renderer, render_user, source="user/category/value"
    )
    registry.register_reasoner(
        Reasoner(
            "local.scoped-agent",
            "test:model",
            system_render=system_renderer,
            user_render=user_renderer,
        )
    )
    model_calls: list[dict[str, Any]] = []

    async def configured_mcp(
        _server: str,
        _tool: str,
        value: Any,
        _cid: str,
        _principal: dict[str, Any] | None,
        _secrets: dict[str, str] | None,
        _input_schema_validated: bool,
    ) -> Any:
        return {"echo": value["value"]}

    async def configured_llm(
        reasoner: Reasoner,
        value: Any,
        _principal: dict[str, Any] | None,
        transcript: Any,
        _dispatch: Any,
        **kwargs: Any,
    ) -> Any:
        model_calls.append(
            {
                "value": value,
                "system": reasoner.system,
                "transcript": transcript,
                "tools": kwargs.get("tools"),
            }
        )
        if len(model_calls) == 1:
            return {
                "tool_calls": [
                    {
                        "id": "echo-1",
                        "tool": "echo",
                        "input": {"value": value["input"]["value"]},
                    }
                ]
            }
        return {
            "done": True,
            "output": {"answer": transcript[-1]["content"]["echo"]},
        }

    def context_factory() -> WorkerContext:
        return WorkerContext(
            mcp_call=configured_mcp,
            llm=configured_llm,
            registry=registry,
        )

    flow = agent_app(
        "local.scoped-agent",
        tools=["echo"],
        tool_aliases={"echo": "srv/echo"},
        max_rounds=3,
        ctx=ContextPolicy(
            scope=ContextScope.WHOLE_SESSION,
            max_tokens=500,
        ),
        native_tools=True,
    )
    app = server.create_local_app(
        project_root=tmp_path,
        context_factory=context_factory,
    )
    release = _release(
        flow,
        snapshot=read_snapshot("echo"),
        mcp_preflight_policy="off",
    )
    original = {"category": "memory", "value": "hello"}

    with TestClient(app) as client:
        _publish_and_activate(client, release, headers=CONFIGURED_HEADERS)
        started = _start(
            client,
            key="transcript-native-agent",
            input=original,
            headers=CONFIGURED_HEADERS,
        )
        finished = _wait_for_result(
            client,
            started.json()["run_id"],
            headers=CONFIGURED_HEADERS,
        )

    assert finished["run"]["status"] == "completed", finished["run"].get("error")
    assert finished["result"]["status"] == "done"
    assert model_calls[0]["tools"][0]["function"]["name"] == "echo"
    assert [call["system"] for call in model_calls] == [
        "Category: memory",
        "Category: memory",
    ]
    assert model_calls[0]["transcript"] == [
        {"role": "user", "content": "Investigate memory: hello"}
    ]
    assert model_calls[1]["value"]["input"] == original
    assert model_calls[1]["value"]["trace"][0]["decision"] == "call"
    assert model_calls[1]["transcript"][0] == {
        "role": "user",
        "content": "Investigate memory: hello",
    }
    assert model_calls[1]["transcript"][-1] == {
        "role": "tool",
        "ref": {"kind": "native", "name": "echo"},
        "tool_call_id": "echo-1",
        "content": {"echo": "hello"},
    }
    assert finished["result"]["output"] == {"answer": "hello"}


def test_local_api_maps_agent_controller_error_to_failed_run_and_scrubs(
    tmp_path: Path,
) -> None:
    from julep.secrets import register_secret_value

    _configure_context_auth(tmp_path)
    secret = "operator-agent-error:/must-not-leak"
    register_secret_value(secret)
    registry = Registry()
    registry.register_reasoner(Reasoner("local.failing-agent", "test:model"))

    async def configured_llm(
        _reasoner: Reasoner,
        _value: Any,
        _principal: dict[str, Any] | None,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        return {"done": False, "reason": f"controller echoed {secret}"}

    app = server.create_local_app(
        project_root=tmp_path,
        context_factory=lambda: WorkerContext(llm=configured_llm, registry=registry),
    )
    release = _release(agent_app("local.failing-agent", max_rounds=2))

    with TestClient(app) as client:
        _publish_and_activate(client, release, headers=CONFIGURED_HEADERS)
        started = _start(
            client,
            key="agent-controller-error",
            input={"task": "fail"},
            headers=CONFIGURED_HEADERS,
        )
        finished = _wait_for_result(
            client,
            started.json()["run_id"],
            headers=CONFIGURED_HEADERS,
        )
        events = client.get(
            f"/v1/runs/{started.json()['run_id']}/events",
            headers={**CONFIGURED_HEADERS, "Accept": "application/json"},
        ).json()["items"]

    assert finished["run"]["status"] == "failed"
    assert finished["result"] is None
    assert "AgentTerminalError" in finished["run"]["error"]
    assert secret not in repr(finished)
    assert secret not in repr(events)
    assert any(event["type"] == "Failed" for event in events)


def test_local_effects_agent_preserves_native_count_and_uses_wire_alias_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import asyncio

    from julep import agent_loop
    from julep.execution import effects
    from julep.execution.policy import ExecutionPolicy
    from julep.projection import InMemoryProjection, ProjectionEmitter
    from julep.server.local import _LocalEffectsEnv

    captured: dict[str, Any] = {}

    async def resolve_agent_spec(_input: Any) -> dict[str, Any]:
        return {}

    async def drive_agent_loop(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "status": "done",
            "output": "ok",
            "callCounts": {"search": 1, "srv/search": 1},
        }

    async def gate(value: Any, _cid: str, _timeout_s: int | None) -> Any:
        return value

    monkeypatch.setattr(effects, "resolveAgentSpec", resolve_agent_spec)
    monkeypatch.setattr(agent_loop, "drive_agent_loop", drive_agent_loop)
    counts = {"search": 1}
    env = _LocalEffectsEnv(
        manifest={},
        emitter=ProjectionEmitter(InMemoryProjection()),
        session_id="local-alias",
        manifest_json={},
        policy=ExecutionPolicy(),
        gate=gate,
        max_calls={"search": 10, "srv/search": 1},
        principal=None,
        secrets=None,
        runtime_declarations_ref=None,
        root_run_id="local-alias",
        segment_seq=0,
        call_counts=counts,
    )

    result = asyncio.run(
        env.run_agent(
            "controller",
            {},
            "cid",
            {
                "tools": ["search"],
                "toolAliases": {"search": "srv/search"},
                "toolContracts": {"search": {}},
            },
        )
    )

    assert captured["contracts"]["search"]["maxCalls"] == 1
    assert captured["state"].call_counts == {"search": 1}
    assert result["output"] == "ok"
    assert counts == {"search": 1, "srv/search": 1}
