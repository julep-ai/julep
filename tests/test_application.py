from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from julep import CapabilityManifest, WorkflowStartOptions, deploy, ident, think
from julep.app import Application, ApplicationDefinitionError, PipelineSpec
from julep.app_deploy import (
    ApplicationReleaseError,
    HelmLaneReconciler,
    LaneObservation,
    ObservedApplicationState,
    build_lane_deployment_config,
    deployment_config_hash,
    lane_release_name,
    plan_application,
    publish_application,
    reconcile_application,
    release_from_bytes,
)
from julep.artifact_store import LocalDirArtifactStore
from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec
from julep.dotctx import Reasoner
from julep.dsl import app as agent_app
from julep.registry import DEFAULT_REGISTRY


def _spec(name: str, *, lane: str = "summary", snapshot: McpSnapshot | None = None):
    return PipelineSpec[dict[str, Any], dict[str, Any]](
        name=name,
        flow=ident(),
        capabilities=CapabilityManifest(),
        lane=lane,
        eval_packages=(f"evals.{name}",),
        snapshot=snapshot,
    )


def _snapshot(version: str) -> McpSnapshot:
    return McpSnapshot(
        servers={
            "memory-tools": McpServerSnapshot(
                server="memory-tools",
                version=version,
                tools={"read_summary": McpToolSpec(input_schema={"type": "object"})},
            )
        }
    )


def test_application_compilation_is_order_deterministic() -> None:
    one = Application("memory", [_spec("one_liner"), _spec("summary")]).compile()
    two = Application("memory", [_spec("summary"), _spec("one_liner")]).compile()

    assert one.artifact_hash == two.artifact_hash
    assert [pipeline.spec.name for pipeline in one.pipelines] == ["one_liner", "summary"]
    assert one.lanes == {"summary": ("one_liner", "summary")}
    assert one.pipelines[0].spec.eval_packages == ("evals.one_liner",)


def test_application_rejects_duplicate_pipeline_declarations() -> None:
    with pytest.raises(ApplicationDefinitionError, match="duplicate pipeline"):
        Application("memory", [_spec("summary"), _spec("summary")])


def test_application_rejects_helm_unsafe_name() -> None:
    with pytest.raises(
        ApplicationDefinitionError,
        match="lowercase Kubernetes label value",
    ):
        Application("foo,bar", [_spec("summary")])


def test_application_rejects_conflicting_cross_pipeline_reasoners() -> None:
    one = Reasoner("shared", "anthropic:model-a")
    two = Reasoner("shared", "anthropic:model-b")

    with pytest.raises(ApplicationDefinitionError, match="conflicting reasoners"):
        Application(
            "memory",
            [
                PipelineSpec("summary", ident(), reasoners=(one,)),
                PipelineSpec("one_liner", ident(), reasoners=(two,)),
            ],
        )


def test_application_preregisters_reasoners_before_sorted_compilation() -> None:
    reasoner = Reasoner("application-order-shared", "anthropic:model-a")
    app = Application(
        "memory",
        [
            PipelineSpec(
                "a_string_reference",
                think(reasoner.name),
                reasoners=(reasoner.name,),
            ),
            PipelineSpec(
                "z_object_declaration",
                ident(),
                reasoners=(reasoner,),
            ),
        ],
    )

    compiled = app.compile()

    assert len(compiled.pipelines) == 2


def test_pipeline_rejects_flow_reasoner_missing_from_declaration() -> None:
    with pytest.raises(ApplicationDefinitionError, match="undeclared reasoners"):
        PipelineSpec("summary", think("missing-from-spec"))


def test_pipeline_requires_declared_app_summarizer() -> None:
    with pytest.raises(
        ApplicationDefinitionError,
        match="app-summary-reasoner",
    ):
        PipelineSpec(
            "summary",
            agent_app("app-controller", summarizer="app-summary-reasoner"),
            reasoners=("app-controller",),
        )


def test_reasoner_declaration_order_does_not_change_application_hash() -> None:
    first_name = "application-order-first"
    second_name = "application-order-second"
    first = Reasoner(first_name, "model-a")
    second = Reasoner(second_name, "model-b")
    existing = {
        first_name: DEFAULT_REGISTRY.reasoners.pop(first_name, None),
        second_name: DEFAULT_REGISTRY.reasoners.pop(second_name, None),
    }
    try:
        one = Application(
            "memory",
            [PipelineSpec("summary", ident(), reasoners=(first, second))],
        ).compile()
        two = Application(
            "memory",
            [PipelineSpec("summary", ident(), reasoners=(second, first))],
        ).compile()

        assert one.artifact_hash == two.artifact_hash
        assert one.pipelines[0].spec.to_declaration_json()["reasoners"] == [
            first_name,
            second_name,
        ]
    finally:
        DEFAULT_REGISTRY.reasoners.pop(first_name, None)
        DEFAULT_REGISTRY.reasoners.pop(second_name, None)
        for name, reasoner in existing.items():
            if reasoner is not None:
                DEFAULT_REGISTRY.reasoners[name] = reasoner


def test_application_runtime_declarations_are_hashed_and_registered() -> None:
    name = "application-worker-runtime"
    one = Application(
        "memory",
        [PipelineSpec("summary", think(name), reasoners=(Reasoner(name, "model-a"),))],
    )
    two = Application(
        "memory",
        [PipelineSpec("summary", think(name), reasoners=(Reasoner(name, "model-b"),))],
    )
    existing = DEFAULT_REGISTRY.reasoners.pop(name, None)
    try:
        assert one.runtime_declarations_hash != two.runtime_declarations_hash

        one.register_runtime_declarations(
            expected_hash=one.runtime_declarations_hash,
        )

        assert DEFAULT_REGISTRY.get_reasoner(name).model == "model-a"
    finally:
        DEFAULT_REGISTRY.reasoners.pop(name, None)
        if existing is not None:
            DEFAULT_REGISTRY.reasoners[name] = existing


def test_application_runtime_declarations_reject_release_drift() -> None:
    name = "application-worker-runtime-drift"
    application = Application(
        "memory",
        [PipelineSpec("summary", think(name), reasoners=(Reasoner(name, "model-a"),))],
    )
    existing = DEFAULT_REGISTRY.reasoners.pop(name, None)
    try:
        with pytest.raises(ApplicationDefinitionError, match="immutable release"):
            application.register_runtime_declarations(
                expected_hash="sha256:" + "0" * 64,
            )
        assert name not in DEFAULT_REGISTRY.reasoners
    finally:
        if existing is not None:
            DEFAULT_REGISTRY.reasoners[name] = existing


def test_application_hashes_and_registers_string_reasoner_declarations() -> None:
    name = "application-worker-string-runtime"
    reasoner = Reasoner(name, "model-a")
    existing = DEFAULT_REGISTRY.reasoners.pop(name, None)
    try:
        DEFAULT_REGISTRY.register_reasoner(reasoner)
        application = Application(
            "memory",
            [PipelineSpec("summary", think(name), reasoners=(name,))],
        )

        compiled = application.compile()

        assert compiled.runtime_declarations_hash == application.runtime_declarations_hash
        assert DEFAULT_REGISTRY.get_reasoner(name) == reasoner
    finally:
        DEFAULT_REGISTRY.reasoners.pop(name, None)
        if existing is not None:
            DEFAULT_REGISTRY.reasoners[name] = existing


def test_application_compile_rejects_missing_reasoner_renderer() -> None:
    name = "application-missing-renderer"
    renderer_name = "application-renderer-does-not-exist"
    existing_reasoner = DEFAULT_REGISTRY.reasoners.pop(name, None)
    existing_renderer = DEFAULT_REGISTRY.renderers.pop(renderer_name, None)
    try:
        application = Application(
            "memory",
            [
                PipelineSpec(
                    "summary",
                    think(name),
                    reasoners=(Reasoner(name, "model-a", system_render=renderer_name),),
                )
            ],
        )

        with pytest.raises(ApplicationDefinitionError, match="unknown renderer"):
            application.compile()
    finally:
        DEFAULT_REGISTRY.reasoners.pop(name, None)
        if existing_reasoner is not None:
            DEFAULT_REGISTRY.reasoners[name] = existing_reasoner
        if existing_renderer is not None:
            DEFAULT_REGISTRY.renderers[renderer_name] = existing_renderer


def test_live_snapshot_override_is_visible_as_schema_drift() -> None:
    app = Application("memory", [_spec("summary", snapshot=_snapshot("1"))])
    compiled = app.compile({"summary": _snapshot("2")})
    plan = plan_application(compiled, ObservedApplicationState())

    assert compiled.pipelines[0].mcp_schema_drift is True
    assert plan.mcp_schema_drift == {"summary": True}
    assert plan.release_drift == {"summary": "unknown"}
    assert plan.helm_keda_drift == {"summary": "unknown"}
    assert plan.runtime_drift == {"summary": "unknown"}


def test_plan_detects_worker_image_drift() -> None:
    compiled = Application("memory", [_spec("summary")]).compile()
    plan = plan_application(
        compiled,
        ObservedApplicationState(worker_image="registry/memory@sha256:" + "a" * 64),
        worker_image="registry/memory@sha256:" + "b" * 64,
    )

    assert plan.worker_image_drift is True


def test_plan_detects_live_resource_drift_with_unchanged_annotation() -> None:
    compiled = Application("memory", [_spec("summary")]).compile()
    release_hash = "sha256:" + "a" * 64
    config_hash = "sha256:" + "b" * 64
    observed = ObservedApplicationState(
        recorded_release_hash=release_hash,
        lanes={
            "summary": LaneObservation(
                lane="summary",
                release_hash=release_hash,
                deployment_config_hash=config_hash,
                live_config_matches_helm=False,
            )
        },
    )

    plan = plan_application(
        compiled,
        observed,
        desired_deployment_config_hash=config_hash,
    )

    assert plan.deployment_config_drift == {"summary": "drift"}
    assert plan.helm_keda_drift == {"summary": "drift"}


def test_compile_live_uses_explicit_snapshot_source() -> None:
    app = Application(
        "memory",
        [
            PipelineSpec(
                name="summary",
                flow=ident(),
                capabilities=CapabilityManifest(),
                snapshot=_snapshot("1"),
                snapshot_source=lambda _env: _snapshot("2"),
            )
        ],
    )

    compiled = app.compile_live()

    assert compiled.pipelines[0].mcp_schema_drift is True


def test_compile_live_passes_read_only_selected_environment() -> None:
    received: list[dict[str, str]] = []

    def source(environment):
        received.append(dict(environment))
        with pytest.raises(TypeError):
            environment["MCP_URL"] = "mutated"
        return _snapshot("2")

    app = Application(
        "memory",
        [
            PipelineSpec(
                name="summary",
                flow=ident(),
                snapshot=_snapshot("1"),
                snapshot_source=source,
            )
        ],
    )

    app.compile_live(env_vars={"MCP_URL": "https://production.invalid/mcp"})

    assert received == [{"MCP_URL": "https://production.invalid/mcp"}]


def test_application_evals_receive_the_supplied_llm_caller(monkeypatch, tmp_path) -> None:
    caller = object()
    calls: list[tuple[str, object]] = []

    def fake_run(path: str, **kwargs):
        calls.append((path, kwargs["llm_caller"]))
        return path

    monkeypatch.setattr("julep.cli.evalrun.run_eval_sync", fake_run)
    app = Application("memory", [_spec("summary")])

    reports = app.run_evals(caller, root=tmp_path)

    assert reports == {"summary": (str(tmp_path / "evals.summary"),)}
    assert calls == [(str(tmp_path / "evals.summary"), caller)]


def test_publish_release_is_content_addressed_and_round_trips(tmp_path) -> None:
    store = LocalDirArtifactStore(tmp_path / "artifacts")
    reasoner_name = "release-roundtrip-reasoner"
    existing = DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
    compiled = Application(
        "memory",
        [
            PipelineSpec(
                "summary",
                think(reasoner_name),
                reasoners=(Reasoner(reasoner_name, "model-a", system="summarize"),),
                lane="summary",
            )
        ],
    ).compile()
    image = "registry.example/memory@sha256:" + "a" * 64

    try:
        release = publish_application(
            compiled,
            store,
            worker_image=image,
            signing_key="0" * 64,
        )

        digest = release.release_hash.removeprefix("sha256:")
        assert store.has(digest)
        assert release.schema_version == 2
        declarations_ref = release.pipelines[0].runtime_declarations_ref
        assert declarations_ref is not None
        assert store.has(str(declarations_ref["hash"]).removeprefix("sha256:"))
        assert len(store.get(str(declarations_ref["hash"]).removeprefix("sha256:"))) == (
            declarations_ref["size"]
        )
        pipeline_json = release.manifest["pipelines"][0]
        assert pipeline_json["runtimeDeclarationsRef"] == declarations_ref
        assert "runtimeDeclarationsRef" not in pipeline_json["manifestJson"]

        restored = release_from_bytes(store.get(digest))
        assert restored.release_hash == release.release_hash
        assert restored.worker_image == image
        assert restored.schema_version == 2
        assert restored.pipelines[0].runtime_declarations_ref == declarations_ref

        captured: dict[str, Any] = {}

        class Client:
            async def start_workflow(self, workflow, flow_input, **kwargs):
                captured["flow_input"] = flow_input
                captured["kwargs"] = kwargs
                return "handle"

        result = asyncio.run(
            restored.pipelines[0].start(
                Client(),
                session_id="release-roundtrip",
                input={"document": "hello"},
                options=WorkflowStartOptions(require_payload_encryption=False),
            )
        )
        assert result == "handle"
        assert captured["flow_input"].runtime_declarations_ref == declarations_ref
        assert captured["kwargs"]["task_queue"] == restored.pipelines[0].task_queue
    finally:
        DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
        if existing is not None:
            DEFAULT_REGISTRY.reasoners[reasoner_name] = existing


@pytest.mark.parametrize("schema_version", [1, 3, None])
def test_release_parser_requires_schema_version_two(tmp_path, schema_version) -> None:
    release = publish_application(
        Application("memory", [_spec("summary")]).compile(),
        LocalDirArtifactStore(tmp_path / "artifacts"),
        worker_image="registry.example/memory@sha256:" + "a" * 64,
        signing_key="0" * 64,
    )
    payload = json.loads(release.manifest_bytes)
    if schema_version is None:
        payload.pop("schemaVersion")
    else:
        payload["schemaVersion"] = schema_version

    with pytest.raises(
        ApplicationReleaseError,
        match=r"version 2 is required; re-publish with this julep version",
    ):
        release_from_bytes(json.dumps(payload).encode("utf-8"))


def test_published_release_is_deeply_immutable(tmp_path) -> None:
    release = publish_application(
        Application("memory", [_spec("summary")]).compile(),
        LocalDirArtifactStore(tmp_path / "artifacts"),
        worker_image="registry.example/memory@sha256:" + "d" * 64,
        signing_key="0" * 64,
    )
    published_hash = release.release_hash

    with pytest.raises(TypeError, match="immutable"):
        release.pipelines[0].flow_json["op"] = "mutated"
    with pytest.raises(TypeError, match="immutable"):
        release.manifest["application"] = "mutated"

    assert release.release_hash == published_hash


def test_publish_rejects_post_compile_flow_mutation(tmp_path) -> None:
    compiled = Application("memory", [_spec("summary")]).compile()
    compiled.pipelines[0].deployment.flow.id = "mutated-after-compile"

    with pytest.raises(ValueError, match="changed after compilation"):
        publish_application(
            compiled,
            LocalDirArtifactStore(tmp_path / "artifacts"),
            worker_image="registry.example/memory@sha256:" + "e" * 64,
            signing_key="0" * 64,
        )


def test_deployment_integrity_allows_late_binding_unresolved_reasoner() -> None:
    name = "legacy-late-bound-reasoner"
    existing = DEFAULT_REGISTRY.reasoners.pop(name, None)
    try:
        deployment = deploy(agent_app(name), McpSnapshot())
        assert deployment.artifact_components["reasoners"] == {name: {"name": name}}

        DEFAULT_REGISTRY.register_reasoner(Reasoner(name, "model-a"))

        deployment.assert_artifact_integrity()
    finally:
        DEFAULT_REGISTRY.reasoners.pop(name, None)
        if existing is not None:
            DEFAULT_REGISTRY.reasoners[name] = existing


def test_release_rejects_mutable_image_tag(tmp_path) -> None:
    with pytest.raises(ApplicationReleaseError, match="immutable"):
        publish_application(
            Application("memory", [_spec("summary")]).compile(),
            LocalDirArtifactStore(tmp_path),
            worker_image="registry.example/memory:latest",
            signing_key="0" * 64,
        )


def test_deployment_config_changes_release_and_physical_queue(tmp_path) -> None:
    compiled = Application("memory", [_spec("summary")]).compile()
    chart = tmp_path / "chart"
    chart.mkdir()
    (chart / "Chart.yaml").write_text("name: memory\n", encoding="utf-8")

    def publish(queue: str):
        config = build_lane_deployment_config(
            chart=str(chart),
            namespace="memory",
            temporal_address="temporal:7233",
            temporal_namespace="default",
            worker_context_factory="memory.worker:context",
            worker_service_account=None,
            worker_priority_class=None,
            payload_encryption_secret="temporal-payload-codec",
            worker_environment={},
            worker_secret_environment={},
            lanes=("summary",),
            queue_by_lane={"summary": queue},
        )
        return publish_application(
            compiled,
            LocalDirArtifactStore(tmp_path / "artifacts"),
            worker_image="registry.example/memory@sha256:" + "f" * 64,
            deployment_config=config,
            signing_key="0" * 64,
        )

    first = publish("summary-a")
    second = publish("summary-b")

    assert first.release_hash != second.release_hash
    assert first.pipelines[0].task_queue != second.pipelines[0].task_queue


def test_lane_release_names_do_not_collide_after_kubernetes_normalization() -> None:
    release_hash = "sha256:" + "a" * 64

    dotted = lane_release_name("memory", "summary.v2", release_hash=release_hash)
    underscored = lane_release_name("memory", "summary_v2", release_hash=release_hash)

    assert dotted != underscored
    assert len(dotted) <= 53
    assert len(underscored) <= 53


def test_deployment_config_rejects_release_owned_environment_overrides(
    tmp_path,
) -> None:
    chart = tmp_path / "chart"
    chart.mkdir()
    with pytest.raises(ApplicationReleaseError, match="release-owned"):
        build_lane_deployment_config(
            chart=str(chart),
            namespace="memory",
            temporal_address="temporal:7233",
            temporal_namespace="default",
            worker_context_factory="memory.worker:context",
            worker_service_account=None,
            worker_priority_class=None,
            payload_encryption_secret="temporal-payload-codec",
            worker_environment={"TEMPORAL_TASK_QUEUE": "wrong"},
            worker_secret_environment={},
            lanes=("summary",),
        )


def test_deployment_config_requires_payload_encryption_secret(tmp_path) -> None:
    chart = tmp_path / "chart"
    chart.mkdir()

    with pytest.raises(ApplicationReleaseError, match="payload_encryption_secret"):
        build_lane_deployment_config(
            chart=str(chart),
            namespace="memory",
            temporal_address="temporal:7233",
            temporal_namespace="default",
            worker_context_factory="memory.worker:context",
            worker_service_account=None,
            worker_priority_class=None,
            payload_encryption_secret="",
            worker_environment={},
            worker_secret_environment={},
            lanes=("summary",),
        )


@pytest.mark.parametrize(
    ("payload_encryption_secret", "worker_priority_class", "field"),
    [
        (
            "codec,worker.priorityClassName=injected",
            None,
            "payload_encryption_secret",
        ),
        (
            "temporal-payload-codec",
            "workers,payloadEncryption.required=false",
            "worker_priority_class",
        ),
        ("a" * 254, None, "payload_encryption_secret"),
    ],
)
def test_deployment_config_rejects_unsafe_kubernetes_resource_names(
    tmp_path,
    payload_encryption_secret: str,
    worker_priority_class: str | None,
    field: str,
) -> None:
    chart = tmp_path / "chart"
    chart.mkdir()

    with pytest.raises(ApplicationReleaseError, match=field):
        build_lane_deployment_config(
            chart=str(chart),
            namespace="memory",
            temporal_address="temporal:7233",
            temporal_namespace="default",
            worker_context_factory="memory.worker:context",
            worker_service_account=None,
            worker_priority_class=worker_priority_class,
            payload_encryption_secret=payload_encryption_secret,
            worker_environment={},
            worker_secret_environment={},
            lanes=("summary",),
        )


def test_deployment_config_hashes_packaged_chart_contents(tmp_path) -> None:
    chart = tmp_path / "memory-1.0.0.tgz"
    chart.write_bytes(b"chart-v1")

    def config() -> dict[str, Any]:
        return build_lane_deployment_config(
            chart=str(chart),
            namespace="memory",
            temporal_address="temporal:7233",
            temporal_namespace="default",
            worker_context_factory="memory.worker:context",
            worker_service_account=None,
            worker_priority_class=None,
            payload_encryption_secret="temporal-payload-codec",
            worker_environment={},
            worker_secret_environment={},
            lanes=("summary",),
        )

    first = deployment_config_hash(config())
    chart.write_bytes(b"chart-v2")

    assert deployment_config_hash(config()) != first


def test_deployment_config_rejects_mutable_remote_chart_reference() -> None:
    with pytest.raises(ApplicationReleaseError, match="pinned"):
        build_lane_deployment_config(
            chart="example/memory",
            namespace="memory",
            temporal_address="temporal:7233",
            temporal_namespace="default",
            worker_context_factory="memory.worker:context",
            worker_service_account=None,
            worker_priority_class=None,
            payload_encryption_secret="temporal-payload-codec",
            worker_environment={},
            worker_secret_environment={},
            lanes=("summary",),
        )


def test_reconcile_one_helm_release_per_lane(tmp_path) -> None:
    store = LocalDirArtifactStore(tmp_path / "artifacts")
    compiled = Application(
        "memory",
        [_spec("summary", lane="summary"), _spec("brief", lane="brief-refresh")],
    ).compile()
    queues = {"summary": "memory-summary", "brief-refresh": "memory-brief"}
    worker_environment = {"MEMORY_TOOLS_MCP_URL": "http://memory-tools/mcp"}
    worker_secret_environment = {
        "MEMORY_TOOLS_JWT_PRIVATE_KEY": {
            "secret_name": "memory-tools-jwt",
            "key": "private-key",
        }
    }
    release = publish_application(
        compiled,
        store,
        worker_image="registry.example/memory@sha256:" + "b" * 64,
        deployment_config=build_lane_deployment_config(
            chart="infra/helm/julep-worker",
            namespace="memory",
            temporal_address="temporal:7233",
            temporal_namespace="default",
            worker_context_factory="memory.worker:context",
            worker_application="memory.application:application",
            worker_runtime_declarations_hash=compiled.runtime_declarations_hash,
            worker_service_account="julep-worker",
            worker_priority_class="julep-model-worker",
            payload_encryption_secret="temporal-payload-codec",
            worker_environment=worker_environment,
            worker_secret_environment=worker_secret_environment,
            lanes=tuple(compiled.lanes),
            queue_by_lane=queues,
        ),
        signing_key="0" * 64,
    )
    commands: list[list[str]] = []
    reconciler = HelmLaneReconciler(
        chart="infra/helm/julep-worker",
        namespace="memory",
        temporal_address="temporal:7233",
        worker_context_factory="memory.worker:context",
        payload_encryption_secret="temporal-payload-codec",
        worker_application="memory.application:application",
        worker_runtime_declarations_hash=compiled.runtime_declarations_hash,
        worker_service_account="julep-worker",
        worker_priority_class="julep-model-worker",
        worker_environment=worker_environment,
        worker_secret_environment=worker_secret_environment,
        runner=lambda args: commands.append(list(args)),
    )

    results = reconcile_application(
        release,
        reconciler,
        queue_by_lane=queues,
    )

    assert [result.lane for result in results] == ["brief-refresh", "summary"]
    assert len(commands) == 4
    upgrade_commands = commands[::2]
    smoke_commands = commands[1::2]
    assert all(command[:3] == ["helm", "upgrade", "--install"] for command in upgrade_commands)
    assert all(command[:2] == ["helm", "test"] for command in smoke_commands)
    assert all("--logs" in command for command in smoke_commands)
    assert any(
        item.startswith("temporal.taskQueue=memory-summary-r")
        for command in upgrade_commands
        for item in command
    )
    assert all("-r" in result.release_name for result in results)
    assert all("-r" in result.task_queue for result in results)
    summary_result = next(result for result in results if result.lane == "summary")
    summary_pipeline = next(
        pipeline for pipeline in release.pipelines if pipeline.lane == "summary"
    )
    assert summary_pipeline.task_queue == summary_result.task_queue
    with pytest.raises(ValueError, match="does not match"):
        asyncio.run(
            summary_pipeline.start(
                object(),
                session_id="run-1",
                input={},
                options=WorkflowStartOptions(
                    task_queue="wrong-queue",
                    require_payload_encryption=False,
                ),
            )
        )
    assert all(
        "worker.contextFactory=memory.worker:context" in command for command in upgrade_commands
    )
    assert all(
        "worker.applicationSpec=memory.application:application" in command
        for command in upgrade_commands
    )
    assert all(
        f"worker.runtimeDeclarationsHash={compiled.runtime_declarations_hash}" in command
        for command in upgrade_commands
    )
    assert all("serviceAccount.name=julep-worker" in command for command in upgrade_commands)
    assert all("worker.maxConcurrentActivities=1" in command for command in upgrade_commands)
    assert all(
        "worker.priorityClassName=julep-model-worker" in command for command in upgrade_commands
    )
    assert all("payloadEncryption.enabled=true" in command for command in upgrade_commands)
    assert all("payloadEncryption.required=true" in command for command in upgrade_commands)
    assert all(
        "payloadEncryption.secretName=temporal-payload-codec" in command
        for command in upgrade_commands
    )
    assert all("payloadEncryption.keyringKey=keyring" in command for command in upgrade_commands)
    assert all(
        "payloadEncryption.activeKeyIdKey=active-key-id" in command
        for command in upgrade_commands
    )
    assert release.deployment_config["payloadEncryption"] == {
        "enabled": True,
        "required": True,
        "secretName": "temporal-payload-codec",
        "keyringKey": "keyring",
        "activeKeyIdKey": "active-key-id",
    }
    assert all(
        'worker.environment={"MEMORY_TOOLS_MCP_URL":"http://memory-tools/mcp"}' in command
        for command in upgrade_commands
    )
    assert all(
        'worker.secretEnvironment={"MEMORY_TOOLS_JWT_PRIVATE_KEY":'
        '{"key":"private-key","secretName":"memory-tools-jwt"}}' in command
        for command in upgrade_commands
    )
    assert all("--atomic" in command and "--wait" in command for command in upgrade_commands)


def test_reconcile_rejects_publish_only_release_without_worker_image(tmp_path) -> None:
    compiled = Application("memory", [_spec("summary")]).compile()
    release = publish_application(
        compiled,
        LocalDirArtifactStore(tmp_path / "artifacts"),
        worker_image=None,
        signing_key="0" * 64,
    )
    reconciler = HelmLaneReconciler(
        chart="infra/helm/julep-worker",
        namespace="memory",
        temporal_address="temporal:7233",
        worker_context_factory="memory.worker:context",
        payload_encryption_secret="temporal-payload-codec",
        runner=lambda _args: None,
    )

    with pytest.raises(ApplicationReleaseError, match="requires a worker image"):
        reconcile_application(release, reconciler)


def test_helm_environment_preserves_comma_values(tmp_path) -> None:
    compiled = Application("memory", [_spec("summary")]).compile()
    chart = tmp_path / "chart"
    chart.mkdir()
    worker_environment = {"JULEP_BUNDLE_ALLOWED_SIGNERS": "aa,bb"}
    release = publish_application(
        compiled,
        LocalDirArtifactStore(tmp_path / "artifacts"),
        worker_image="registry.example/memory@sha256:" + "c" * 64,
        deployment_config=build_lane_deployment_config(
            chart=str(chart),
            namespace="memory",
            temporal_address="temporal:7233",
            temporal_namespace="default",
            worker_context_factory="memory.worker:context",
            worker_service_account=None,
            worker_priority_class=None,
            payload_encryption_secret="temporal-payload-codec",
            worker_environment=worker_environment,
            worker_secret_environment={},
            lanes=tuple(compiled.lanes),
        ),
        signing_key="0" * 64,
    )
    commands: list[list[str]] = []
    reconciler = HelmLaneReconciler(
        chart=str(chart),
        namespace="memory",
        temporal_address="temporal:7233",
        worker_context_factory="memory.worker:context",
        payload_encryption_secret="temporal-payload-codec",
        worker_priority_class=None,
        worker_environment=worker_environment,
        runner=lambda args: commands.append(list(args)),
    )

    reconcile_application(release, reconciler)

    assert 'worker.environment={"JULEP_BUNDLE_ALLOWED_SIGNERS":"aa,bb"}' in commands[0]
    assert "payloadEncryption.secretName=temporal-payload-codec" in commands[0]
    assert "worker.priorityClassName=" in commands[0]
