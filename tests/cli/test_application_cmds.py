from __future__ import annotations

import copy
import dataclasses
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from julep import Application, PipelineSpec, ident
from julep.cli.main import main
from julep.cli import application as application_module
from julep.cli.config import McpServerConfig, load_config
from julep.app_deploy import LaneApplyResult, deployment_config_hash
from julep.freeze import McpSnapshot


def _scaled_object(release_name: str, task_queue: str) -> dict:
    return {
        "apiVersion": "keda.sh/v1alpha1",
        "kind": "ScaledObject",
        "metadata": {"name": f"{release_name}-temporal"},
        "spec": {
            "scaleTargetRef": {"name": release_name},
            "pollingInterval": 5,
            "cooldownPeriod": 60,
            "minReplicaCount": 0,
            "maxReplicaCount": 4,
            "triggers": [
                {
                    "type": "temporal",
                    "metadata": {
                        "endpoint": "temporal:7233",
                        "namespace": "default",
                        "taskQueue": task_queue,
                        "queueTypes": "workflow,activity",
                        "targetQueueSize": "1",
                        "activationTargetQueueSize": "0",
                    },
                }
            ],
        },
        "status": {"conditions": [{"type": "Ready", "status": "True"}]},
    }


def _helm_manifest(
    deployment: dict,
    scaled_object: dict,
) -> str:
    rendered_deployment = copy.deepcopy(deployment)
    rendered_deployment["apiVersion"] = "apps/v1"
    rendered_deployment["kind"] = "Deployment"
    rendered_deployment.pop("status", None)
    rendered_scaled_object = copy.deepcopy(scaled_object)
    rendered_scaled_object.pop("status", None)
    return yaml.safe_dump_all(
        [rendered_deployment, rendered_scaled_object],
        sort_keys=False,
    )


def _application_project(tmp_path: Path) -> Path:
    chart = tmp_path / "infra" / "helm" / "julep-worker"
    chart.mkdir(parents=True)
    (chart / "Chart.yaml").write_text("name: julep-worker\n", encoding="utf-8")
    (tmp_path / "memory_application.py").write_text(
        """\
from julep import Application, CapabilityManifest, PipelineSpec, ident

application = Application(
    "memory",
    [
        PipelineSpec(
            name="episode_summary",
            flow=ident(),
            capabilities=CapabilityManifest(),
            lane="summary",
            eval_packages=("prompts/episode_summary.ctx",),
        ),
        PipelineSpec(
            name="episode_one_liner",
            flow=ident(),
            capabilities=CapabilityManifest(),
            lane="summary",
            eval_packages=("prompts/episode_one_liner.ctx",),
        ),
    ],
)
""",
        encoding="utf-8",
    )
    release_store = (tmp_path / "releases").as_uri()
    (tmp_path / "pyproject.toml").write_text(
        "[tool.julep]\n"
        'src = ["."]\n'
        'application = "memory_application:application"\n'
        "[tool.julep.env.local]\n"
        'temporal_address = "temporal:7233"\n'
        f'release_store = "{release_store}"\n'
        f'worker_image = "example.invalid/memory@sha256:{"a" * 64}"\n'
        'worker_context_factory = "memory_application:build_context"\n'
        'worker_service_account = "julep-worker"\n'
        'worker_priority_class = "julep-model-worker"\n'
        'payload_encryption_secret = "temporal-payload-codec"\n'
        "[tool.julep.env.local.worker_environment]\n"
        'MEMORY_TOOLS_MCP_URL = "http://memory-tools/mcp"\n'
        "[tool.julep.env.local.worker_secret_environment.MEMORY_TOOLS_JWT_PRIVATE_KEY]\n"
        'secret_name = "memory-tools-jwt"\n'
        'key = "private-key"\n',
        encoding="utf-8",
    )
    return tmp_path


def test_application_config_is_explicit_and_parses_release_fields(tmp_path: Path) -> None:
    root = _application_project(tmp_path)
    cfg = load_config(root)

    assert cfg.application == "memory_application:application"
    assert cfg.envs["local"].release_store == (root / "releases").as_uri()
    assert cfg.envs["local"].worker_image is not None
    assert cfg.envs["local"].helm_chart == "infra/helm/julep-worker"
    assert cfg.envs["local"].worker_context_factory == "memory_application:build_context"
    assert cfg.envs["local"].worker_service_account == "julep-worker"
    assert cfg.envs["local"].worker_priority_class == "julep-model-worker"
    assert cfg.envs["local"].payload_encryption_secret == "temporal-payload-codec"
    assert cfg.envs["local"].worker_environment == {
        "MEMORY_TOOLS_MCP_URL": "http://memory-tools/mcp"
    }
    assert cfg.envs["local"].worker_secret_environment == {
        "MEMORY_TOOLS_JWT_PRIVATE_KEY": {
            "secret_name": "memory-tools-jwt",
            "key": "private-key",
        }
    }


def test_compile_application_uses_selected_environment_for_live_snapshots(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cfg = load_config(_application_project(tmp_path))
    received: list[dict[str, str]] = []

    def snapshot_source(environment):
        received.append(dict(environment))
        return McpSnapshot()

    application = Application(
        "memory",
        [PipelineSpec("episode_summary", ident(), snapshot_source=snapshot_source)],
    )
    monkeypatch.setattr(application_module, "load_application", lambda _cfg: application)
    env = dataclasses.replace(
        cfg.envs["local"],
        vars={"MCP_URL": "https://production.invalid/mcp", "SHARED": "vars"},
        worker_environment={"MCP_AUTH_MODE": "jwt", "SHARED": "worker"},
    )

    application_module.compile_application(cfg, env)

    assert received == [
        {
            "MCP_URL": "https://production.invalid/mcp",
            "MCP_AUTH_MODE": "jwt",
            "SHARED": "worker",
        }
    ]


def test_compile_application_uses_configured_mcp_snapshot_override(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cfg = dataclasses.replace(
        load_config(_application_project(tmp_path)),
        mcp_servers={
            "memory": McpServerConfig(
                url="https://memory.example/mcp",
                auth="secret",
                version="2026.7",
            )
        },
    )
    source_calls: list[dict[str, str]] = []
    application = Application(
        "memory",
        [
            PipelineSpec(
                "episode_summary",
                ident(),
                snapshot_source=lambda environment: (
                    source_calls.append(dict(environment)) or McpSnapshot()
                ),
            )
        ],
    )
    snapshot = McpSnapshot()
    fetched: list[object] = []
    monkeypatch.setattr(application_module, "load_application", lambda _cfg: application)
    monkeypatch.setattr(
        application_module,
        "_snapshot_configured_servers",
        lambda received: fetched.append(received) or snapshot,
    )

    compiled = application_module.compile_application(
        cfg,
        cfg.envs["local"],
        mcp_snapshot=True,
    )

    assert fetched == [cfg]
    assert source_calls == []
    assert len(compiled.pipelines) == 1


def test_configured_mcp_snapshot_requires_a_server(tmp_path: Path) -> None:
    cfg = load_config(_application_project(tmp_path))

    with pytest.raises(ValueError, match=r"--mcp-snapshot.*tool\.julep\.mcp\.servers"):
        application_module._snapshot_configured_servers(cfg)


def test_configured_mcp_snapshot_passes_servers_and_allowlist(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import julep.mcp_snapshot as mcp_snapshot_module

    server = McpServerConfig(url="https://memory.example/mcp", headers={"X-Tenant": "alpha"})
    cfg = dataclasses.replace(
        load_config(_application_project(tmp_path)),
        mcp_servers={"memory": server},
    )
    expected = McpSnapshot()
    received: list[tuple[object, object]] = []

    def fake_snapshot_servers(servers, *, allowlist):
        received.append((servers, allowlist))
        return expected

    monkeypatch.setattr(mcp_snapshot_module, "snapshot_servers", fake_snapshot_servers)

    assert application_module._snapshot_configured_servers(cfg) is expected
    assert received == [
        (
            {"memory": server},
            frozenset({"https://memory.example/mcp"}),
        )
    ]


def test_plan_and_apply_mcp_snapshot_flags_are_threaded(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    main_module = import_module("julep.cli.main")
    received: list[tuple[str, bool]] = []

    def fake_plan(_cfg, _env, *, observed=None, mcp_snapshot=False):
        assert observed is None
        received.append(("plan", mcp_snapshot))
        return SimpleNamespace(to_json=lambda: {"snapshot": mcp_snapshot})

    def fake_apply(_cfg, _env, *, publish_only=False, mcp_snapshot=False):
        assert publish_only is True
        received.append(("apply", mcp_snapshot))
        return SimpleNamespace(release_hash="release", application_artifact_hash="artifact"), ()

    monkeypatch.setattr(main_module, "plan_configured_application", fake_plan)
    monkeypatch.setattr(main_module, "apply_configured_application", fake_apply)

    assert main(["plan", "--mcp-snapshot", "--json"]) == 0
    assert '"snapshot": true' in capsys.readouterr().out
    assert main(["apply", "--env", "local", "--publish-only", "--mcp-snapshot"]) == 0
    assert "release   release" in capsys.readouterr().out
    assert received == [("plan", True), ("apply", True)]


def test_deployment_config_preserves_pinned_oci_chart(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cfg = load_config(_application_project(tmp_path))
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)
    chart = "oci://registry.example/julep/worker@sha256:" + "f" * 64
    env = dataclasses.replace(cfg.envs["local"], helm_chart=chart)
    compiled = application_module.compile_application(cfg, env)

    resolved_chart, _worker_env, deployment_config = application_module._resolve_deployment_config(
        cfg, env, compiled
    )

    assert resolved_chart == chart
    assert deployment_config["chart"] == "oci:sha256:" + "f" * 64


def test_plan_apply_publish_only_and_status_application_path(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    root = _application_project(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)

    assert main(["plan", "--env", "local", "--json"]) == 0
    plan_output = capsys.readouterr().out
    assert '"mcpSchema"' in plan_output
    assert '"helmKeda"' in plan_output
    assert '"runtime"' in plan_output

    assert main(["apply", "--env", "local", "--publish-only"]) == 0
    apply_output = capsys.readouterr().out
    assert "release   sha256:" in apply_output
    assert "traffic   unchanged" in apply_output
    assert not (root / ".julep" / "releases" / "local.json").exists()
    assert any((root / "releases").rglob("*"))

    assert main(["status", "--env", "local"]) == 3
    status_output = capsys.readouterr().out
    assert "application memory" in status_output
    assert "release     -" in status_output


def test_apply_reports_missing_signing_key_without_traceback(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    root = _application_project(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.delenv("JULEP_BUNDLE_SIGNING_KEY", raising=False)

    assert main(["apply", "--env", "local", "--publish-only"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error: bundle signing requires")
    assert "JULEP_BUNDLE_SIGNING_KEY" in captured.err
    assert "Traceback" not in captured.err


def test_application_deployment_requires_explicit_payload_secret(
    tmp_path: Path,
) -> None:
    cfg = load_config(_application_project(tmp_path))
    env = dataclasses.replace(
        cfg.envs["local"],
        payload_encryption_secret=None,
    )
    compiled = application_module.compile_application(cfg, env)

    with pytest.raises(ValueError, match="requires payload_encryption_secret"):
        application_module._resolve_deployment_config(cfg, env, compiled)


def test_temporal_status_degrades_when_only_one_probe_succeeds(monkeypatch, tmp_path: Path) -> None:
    responses = iter(
        [
            ({"stats": {"approximateBacklogCount": 0}}, ""),
            (None, "temporal=permission denied"),
            ({"count": 0}, ""),
        ]
    )
    monkeypatch.setattr(application_module, "_json_command", lambda _args: next(responses))
    env = load_config(_application_project(tmp_path)).envs["local"]
    env = dataclasses.replace(env, temporal_address="temporal:7233")

    _backlog, _running, healthy, detail = application_module._temporal_status(env, "summary")

    assert healthy is False
    assert "permission denied" in detail


def test_temporal_status_uses_modern_json_stats(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_json_command(args):
        calls.append(list(args))
        if args[:3] == ["temporal", "task-queue", "describe"]:
            queue_type = args[args.index("--task-queue-type") + 1]
            return {
                "stats": {"approximateBacklogCount": 3 if queue_type == "workflow" else 1},
                # Modern aggregate stats take precedence over partition hints.
                "taskQueues": [
                    {"backlogCountHint": 40},
                    {"backlogCountHint": 50},
                ],
            }, ""
        if args[:3] == ["temporal", "workflow", "count"]:
            return {"count": "2"}, ""
        raise AssertionError(args)

    monkeypatch.setattr(application_module, "_json_command", fake_json_command)
    monkeypatch.setattr(
        application_module,
        "_text_command",
        lambda _args: (_ for _ in ()).throw(AssertionError("unexpected fallback")),
    )
    env = load_config(_application_project(tmp_path)).envs["local"]
    env = dataclasses.replace(env, temporal_address="temporal:7233")

    backlog, running, healthy, detail = application_module._temporal_status(env, "summary")

    assert (backlog, running, healthy, detail) == (4, 2, True, "")
    assert len(calls) == 3
    assert [call[call.index("--task-queue-type") + 1] for call in calls[:2]] == [
        "workflow",
        "activity",
    ]
    assert all("--report-stats" in call for call in calls[:2])
    assert all(call[-2:] == ["--output", "json"] for call in calls)


def test_temporal_status_falls_back_for_cli_0_11(monkeypatch, tmp_path: Path) -> None:
    json_calls: list[list[str]] = []
    text_calls: list[list[str]] = []

    def fake_json_command(args):
        args = list(args)
        json_calls.append(args)
        if args[:3] == ["temporal", "task-queue", "describe"]:
            if "--report-stats" in args:
                return None, "temporal=flag provided but not defined: -report-stats"
            queue_type = args[args.index("--task-queue-type") + 1]
            return {
                "taskQueues": [
                    {
                        "partition": 0,
                        "backlogCountHint": 3 if queue_type == "workflow" else 2,
                    },
                    {
                        "partition": 1,
                        "backlogCountHint": 4 if queue_type == "workflow" else 1,
                    },
                ],
                "pollers": [],
            }, ""
        if args[:3] == ["temporal", "workflow", "count"]:
            return None, "temporal=flag provided but not defined: -output"
        raise AssertionError(args)

    def fake_text_command(args):
        args = list(args)
        text_calls.append(args)
        return "Total: 5\n", ""

    monkeypatch.setattr(application_module, "_json_command", fake_json_command)
    monkeypatch.setattr(application_module, "_text_command", fake_text_command)
    env = load_config(_application_project(tmp_path)).envs["local"]
    env = dataclasses.replace(env, temporal_address="temporal:7233")

    backlog, running, healthy, detail = application_module._temporal_status(env, "summary")

    assert (backlog, running, healthy, detail) == (10, 5, True, "")
    assert len(json_calls) == 5
    assert "--report-stats" in json_calls[0]
    assert "--report-stats" not in json_calls[1]
    assert "--report-stats" in json_calls[2]
    assert "--report-stats" not in json_calls[3]
    assert text_calls == [
        [
            "temporal",
            "workflow",
            "count",
            "--address",
            "temporal:7233",
            "--namespace",
            "default",
            "--query",
            'TaskQueue="summary" AND ExecutionStatus="Running"',
        ]
    ]


def test_status_prefers_live_release_over_stale_local_state(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    root = _application_project(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)
    cfg = load_config(root)
    env = cfg.envs["local"]
    compiled = application_module.compile_application(cfg, env)
    _chart, _worker_env, deployment_config = application_module._resolve_deployment_config(
        cfg, env, compiled
    )
    release_hash = "sha256:" + "b" * 64
    task_queue = "summary-r" + "b" * 12
    release_name = "memory-summary-rbbbbbbbbbb"
    deployment = {
        "metadata": {
            "name": release_name,
            "creationTimestamp": "2026-07-13T00:00:00Z",
            "annotations": {
                "julep.ai/application": "memory",
                "julep.ai/lane": "summary",
                "julep.ai/release-hash": release_hash,
                "julep.ai/application-artifact-hash": compiled.artifact_hash,
                "julep.ai/deployment-config-hash": deployment_config_hash(deployment_config),
            },
        },
        "spec": {
            "replicas": 0,
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "worker",
                            "image": env.worker_image,
                            "env": [{"name": "TEMPORAL_TASK_QUEUE", "value": task_queue}],
                        }
                    ]
                }
            },
        },
        "status": {},
    }
    scaled_object = _scaled_object(release_name, task_queue)

    stale_state = root / ".julep" / "releases" / "local.json"
    stale_state.parent.mkdir(parents=True)
    stale_state.write_text(
        "{\n"
        '  "application": "memory",\n'
        f'  "applicationArtifactHash": "sha256:{"c" * 64}",\n'
        f'  "releaseHash": "sha256:{"d" * 64}",\n'
        f'  "workerImage": "example.invalid/memory@sha256:{"e" * 64}",\n'
        '  "lanes": []\n'
        "}\n",
        encoding="utf-8",
    )

    deployment_discovery_calls = 0

    def fake_json_command(args):
        nonlocal deployment_discovery_calls
        if args[:3] == ["kubectl", "get", "deployments"]:
            deployment_discovery_calls += 1
            return {"items": [deployment]}, ""
        if args[:2] == ["helm", "status"]:
            return {"info": {"status": "deployed"}}, ""
        if args[:3] == ["kubectl", "get", "scaledobject"]:
            return scaled_object, ""
        if args[:3] == ["temporal", "task-queue", "describe"]:
            return {"stats": {"approximateBacklogCount": 0}}, ""
        if args[:3] == ["temporal", "workflow", "count"]:
            return {"count": 0}, ""
        raise AssertionError(args)

    monkeypatch.setattr(application_module, "_json_command", fake_json_command)
    monkeypatch.setattr(
        application_module,
        "_text_command",
        lambda args: (
            (_helm_manifest(deployment, scaled_object), "")
            if args[:3] == ["helm", "get", "manifest"]
            else (_ for _ in ()).throw(AssertionError(args))
        ),
    )

    assert main(["status", "--env", "local"]) == 0
    output = capsys.readouterr().out
    assert f"release     {release_hash}" in output
    assert "backlog=0" in output
    assert deployment_discovery_calls == 1


def test_status_prefers_recorded_rollback_deployment_over_newer_candidate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = _application_project(tmp_path)
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)
    cfg = load_config(root)
    env = cfg.envs["local"]
    compiled = application_module.compile_application(cfg, env)
    _chart, _worker_env, deployment_config = application_module._resolve_deployment_config(
        cfg, env, compiled
    )
    config_hash = deployment_config_hash(deployment_config)
    rollback_hash = "sha256:" + "a" * 64
    newer_hash = "sha256:" + "b" * 64
    rollback_name = "memory-summary-raaaaaaaaaaaa"
    newer_name = "memory-summary-rbbbbbbbbbbbb"
    rollback_queue = "summary-r" + "a" * 12
    newer_queue = "summary-r" + "b" * 12

    def deployment(name: str, release_hash: str, queue: str, created: str):
        return {
            "metadata": {
                "name": name,
                "creationTimestamp": created,
                "annotations": {
                    "julep.ai/application": "memory",
                    "julep.ai/lane": "summary",
                    "julep.ai/release-hash": release_hash,
                    "julep.ai/application-artifact-hash": compiled.artifact_hash,
                    "julep.ai/deployment-config-hash": config_hash,
                },
            },
            "spec": {
                "replicas": 0,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "worker",
                                "image": env.worker_image,
                                "env": [
                                    {
                                        "name": "TEMPORAL_TASK_QUEUE",
                                        "value": queue,
                                    }
                                ],
                            }
                        ]
                    }
                },
            },
            "status": {},
        }

    application_module.write_applied_state(
        root,
        env.name,
        application_module.AppliedApplicationState(
            application="memory",
            application_artifact_hash=compiled.artifact_hash,
            release_hash=rollback_hash,
            worker_image=env.worker_image,
            lanes=(
                LaneApplyResult(
                    lane="summary",
                    release_name=rollback_name,
                    task_queue=rollback_queue,
                ),
            ),
        ),
    )
    rollback_deployment = deployment(
        rollback_name,
        rollback_hash,
        rollback_queue,
        "2026-07-12T00:00:00Z",
    )
    newer_deployment = deployment(
        newer_name,
        newer_hash,
        newer_queue,
        "2026-07-13T00:00:00Z",
    )
    rollback_scaled_object = _scaled_object(rollback_name, rollback_queue)
    calls: list[list[str]] = []

    def fake_json_command(args):
        args = list(args)
        calls.append(args)
        if args[:3] == ["kubectl", "get", "deployments"]:
            return {"items": [rollback_deployment, newer_deployment]}, ""
        if args[:2] == ["helm", "status"]:
            assert args[2] == rollback_name
            return {"info": {"status": "deployed"}}, ""
        if args[:3] == ["kubectl", "get", "scaledobject"]:
            assert args[3] == f"{rollback_name}-temporal"
            return rollback_scaled_object, ""
        if args[:3] == ["temporal", "task-queue", "describe"]:
            assert rollback_queue in args
            assert newer_queue not in args
            return {"stats": {"approximateBacklogCount": 0}}, ""
        if args[:3] == ["temporal", "workflow", "count"]:
            assert rollback_queue in " ".join(args)
            assert newer_queue not in " ".join(args)
            return {"count": 0}, ""
        raise AssertionError(args)

    monkeypatch.setattr(application_module, "_json_command", fake_json_command)
    monkeypatch.setattr(
        application_module,
        "_text_command",
        lambda args: (
            (_helm_manifest(rollback_deployment, rollback_scaled_object), "")
            if args[:3] == ["helm", "get", "manifest"]
            else (_ for _ in ()).throw(AssertionError(args))
        ),
    )

    observed = application_module.observe_application(cfg, env)

    assert observed.release_hash == rollback_hash
    assert observed.recorded_release_hash == rollback_hash
    assert observed.lanes["summary"].release_hash == rollback_hash
    assert any(call[:3] == ["temporal", "task-queue", "describe"] for call in calls)


def test_deployment_readiness_detects_unavailable_workers() -> None:
    unavailable = {
        "metadata": {"generation": 3},
        "spec": {"replicas": 2},
        "status": {
            "observedGeneration": 3,
            "updatedReplicas": 2,
            "availableReplicas": 1,
            "unavailableReplicas": 1,
        },
    }

    ready, detail = application_module._deployment_ready(unavailable)

    assert ready is False
    assert detail == "deployment=not-ready"


def test_deployment_readiness_accepts_scale_to_zero() -> None:
    ready, detail = application_module._deployment_ready(
        {"metadata": {}, "spec": {"replicas": 0}, "status": {}}
    )

    assert ready is True
    assert detail == "deployment=scaled-to-zero"


def test_live_helm_config_detects_out_of_band_worker_and_keda_edits(
    monkeypatch,
) -> None:
    release_name = "memory-summary-raaaaaaaaaa"
    task_queue = "summary-raaaaaaaaaaaa"
    expected_deployment = {
        "metadata": {"name": release_name},
        "spec": {
            "replicas": 0,
            "selector": {"matchLabels": {"app": "memory"}},
            "template": {
                "metadata": {"labels": {"app": "memory"}},
                "spec": {
                    "serviceAccountName": "memory-worker",
                    "priorityClassName": "julep-model-worker",
                    "containers": [
                        {
                            "name": "worker",
                            "image": "example.invalid/memory@sha256:" + "a" * 64,
                            "env": [
                                {
                                    "name": "TEMPORAL_TASK_QUEUE",
                                    "value": task_queue,
                                },
                                {
                                    "name": "WORKER_MAX_CONCURRENT_ACTIVITIES",
                                    "value": "1",
                                },
                                {
                                    "name": "MEMORY_TOOLS_JWT_PRIVATE_KEY",
                                    "valueFrom": {
                                        "secretKeyRef": {
                                            "name": "memory-tools-jwt",
                                            "key": "private-key",
                                        }
                                    },
                                },
                            ],
                        }
                    ],
                },
            },
        },
    }
    expected_scaled_object = _scaled_object(release_name, task_queue)
    manifest = _helm_manifest(expected_deployment, expected_scaled_object)
    monkeypatch.setattr(
        application_module,
        "_text_command",
        lambda _args: (manifest, ""),
    )

    live_deployment = copy.deepcopy(expected_deployment)
    # KEDA owns replicas; scaling 0 -> 4 is not deployment-config drift.
    live_deployment["spec"]["replicas"] = 4
    live_scaled_object = copy.deepcopy(expected_scaled_object)

    matches, detail = application_module._live_resources_match_helm(
        release_name,
        "memory",
        deployment=live_deployment,
        scaled_object=live_scaled_object,
    )

    assert matches is True
    assert detail == "helm-manifest=clean"

    live_deployment["spec"]["template"]["spec"]["containers"][0]["env"][1]["value"] = "8"
    matches, _detail = application_module._live_resources_match_helm(
        release_name,
        "memory",
        deployment=live_deployment,
        scaled_object=live_scaled_object,
    )
    assert matches is False

    live_deployment = copy.deepcopy(expected_deployment)
    live_scaled_object["spec"]["maxReplicaCount"] = 8
    matches, _detail = application_module._live_resources_match_helm(
        release_name,
        "memory",
        deployment=live_deployment,
        scaled_object=live_scaled_object,
    )
    assert matches is False
