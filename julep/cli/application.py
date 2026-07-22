"""Application-level plan/apply/status orchestration for the Julep CLI."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import yaml

from julep import _env
from julep.app import Application, CompiledApplication, load_application_spec
from julep.app_deploy import (
    ApplicationPlan,
    ApplicationRelease,
    HelmLaneReconciler,
    LaneApplyResult,
    LaneObservation,
    ObservedApplicationState,
    build_lane_deployment_config,
    deployment_config_hash,
    lane_release_name,
    plan_application,
    publish_application,
    reconcile_application,
)
from julep.cli.config import JulepConfig, EnvConfig
from julep.artifact_store import artifact_store_from_url
from julep.bundle import bundle_signer_public_key
from julep.ctx_pipeline import pipeline_spec_from_ctx
from julep.freeze import McpSnapshot


@dataclass(frozen=True)
class AppliedApplicationState:
    application: str
    application_artifact_hash: str
    release_hash: str
    worker_image: str
    lanes: tuple[LaneApplyResult, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "application": self.application,
            "applicationArtifactHash": self.application_artifact_hash,
            "releaseHash": self.release_hash,
            "workerImage": self.worker_image,
            "lanes": [
                {
                    "lane": lane.lane,
                    "releaseName": lane.release_name,
                    "taskQueue": lane.task_queue,
                }
                for lane in self.lanes
            ],
        }


def load_application(cfg: JulepConfig) -> Application:
    if cfg.application is None:
        raise ValueError(
            "no application configured; set [tool.julep] application = 'your.module:application'"
        )
    search_paths = [cfg.root]
    for entry in cfg.src:
        path = (cfg.root / entry).resolve()
        search_paths.append(path if path.is_dir() else path.parent)
    for path in reversed(search_paths):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)

    return load_application_spec(cfg.application)


def _synth_application_name(root: Path) -> str:
    raw = re.sub(r"[^a-z0-9-]", "-", root.name.lower()).strip("-")
    if not raw or re.fullmatch(r"[a-z0-9](?:[-a-z0-9_.]{0,61}[a-z0-9])?", raw) is None:
        raise ValueError(
            "cannot derive an application name from the project directory "
            f"{root.name!r}; set [tool.julep] application or rename the directory "
            "to a lowercase Kubernetes label"
        )
    return raw


def resolve_application(cfg: JulepConfig, env: EnvConfig) -> Application:
    env_vars = {**env.vars, **env.worker_environment}
    ctx_specs = [
        pipeline_spec_from_ctx(
            pipeline,
            root=cfg.root,
            env_vars=env_vars,
            agent_round_cap=cfg.agent_round_cap,
            mcp_servers=cfg.mcp_servers,
        )
        for _name, pipeline in sorted(cfg.pipelines.items())
    ]
    if cfg.application is not None:
        base = load_application(cfg)
        base_names = {pipeline.name for pipeline in base.pipelines}
        collisions = sorted(name for name in cfg.pipelines if name in base_names)
        if collisions:
            raise ValueError(
                "ctx pipeline name(s) collide with code pipelines: " + ", ".join(collisions)
            )
        if not ctx_specs:
            return base
        return Application(name=base.name, pipelines=(*base.pipelines, *ctx_specs))
    if not ctx_specs:
        raise ValueError(
            "no application configured; set [tool.julep] application = "
            "'your.module:application' or declare a [tool.julep.pipeline.<name>] with a .ctx"
        )
    return Application(name=_synth_application_name(cfg.root), pipelines=tuple(ctx_specs))


def _snapshot_configured_servers(cfg: JulepConfig) -> McpSnapshot:
    if not cfg.mcp_servers:
        raise ValueError(
            "--mcp-snapshot requires at least one server under "
            "[tool.julep.mcp.servers] or [mcp.servers]"
        )
    from julep.mcp_snapshot import snapshot_servers

    return snapshot_servers(cfg.mcp_servers, allowlist=cfg.mcp_allowlist)


def compile_application(
    cfg: JulepConfig,
    env: EnvConfig,
    *,
    mcp_snapshot: bool = False,
) -> CompiledApplication:
    snapshot_environment = {**env.vars, **env.worker_environment}
    application = resolve_application(cfg, env)
    if not mcp_snapshot:
        return replace(
            application.compile_live(env_vars=snapshot_environment),
            mcp_preflight_policy=cfg.mcp_preflight,
        )

    snapshot = _snapshot_configured_servers(cfg)
    snapshot_overrides = {
        pipeline.name: snapshot
        for pipeline in application.pipelines
        if not pipeline.tools
    }
    return replace(
        application.compile(snapshot_overrides),
        mcp_preflight_policy=cfg.mcp_preflight,
    )


def plan_configured_application(
    cfg: JulepConfig,
    env: EnvConfig,
    *,
    observed: Optional[ObservedApplicationState] = None,
    mcp_snapshot: bool = False,
) -> ApplicationPlan:
    compiled = compile_application(cfg, env, mcp_snapshot=mcp_snapshot)
    _chart, _worker_environment, deployment_config = _resolve_deployment_config(
        cfg,
        env,
        compiled,
    )
    return plan_application(
        compiled,
        observed if observed is not None else observe_application(cfg, env),
        worker_image=env.worker_image,
        desired_deployment_config_hash=deployment_config_hash(deployment_config),
    )


def _resolve_deployment_config(
    cfg: JulepConfig,
    env: EnvConfig,
    compiled: CompiledApplication,
    *,
    require_private_signer: bool = False,
) -> tuple[str, dict[str, str], dict[str, Any]]:
    if env.release_store is None:
        raise ValueError(f"env {env.name!r} requires release_store (normally s3://bucket/prefix)")
    if env.temporal_address is None:
        raise ValueError(f"env {env.name!r} requires temporal_address for lane reconciliation")
    if env.worker_context_factory is None:
        raise ValueError(f"env {env.name!r} requires worker_context_factory=module:attribute")
    if env.payload_encryption_secret is None:
        raise ValueError(
            f"env {env.name!r} requires payload_encryption_secret naming an "
            "existing Kubernetes Secret with keyring and active-key-id keys"
        )
    allowed_signers = [
        value.strip().lower()
        for value in _env.get(
            _env.JULEP_BUNDLE_ALLOWED_SIGNERS,
            "",
            environ=env.worker_environment,
        ).split(",")
        if value.strip()
    ]
    if any(re.fullmatch(r"[0-9a-f]{64}", value) is None for value in allowed_signers):
        raise ValueError(
            "JULEP_BUNDLE_ALLOWED_SIGNERS must contain comma-separated "
            "64-character hexadecimal Ed25519 public keys"
        )
    signing_key = _env.get(_env.JULEP_BUNDLE_SIGNING_KEY)
    if require_private_signer:
        signer = bundle_signer_public_key(signing_key)
        if allowed_signers and signer not in allowed_signers:
            raise ValueError(
                "the JULEP_BUNDLE_SIGNING_KEY public key is not present in the "
                "configured JULEP_BUNDLE_ALLOWED_SIGNERS"
            )
        if not allowed_signers:
            allowed_signers.append(signer)
    elif not allowed_signers:
        if signing_key:
            allowed_signers.append(bundle_signer_public_key(signing_key))
        else:
            raise ValueError(
                "read-only application commands require the non-secret "
                "JULEP_BUNDLE_ALLOWED_SIGNERS worker environment setting"
            )
    worker_environment = {
        **env.worker_environment,
        "JULEP_ARTIFACT_STORE_URL": env.release_store,
        _env.JULEP_BUNDLE_ALLOWED_SIGNERS: ",".join(allowed_signers),
    }
    chart = _resolve_helm_chart(cfg.root, env.helm_chart)
    deployment_config = build_lane_deployment_config(
        chart=chart,
        namespace=env.kubernetes_namespace,
        temporal_address=env.temporal_address,
        temporal_namespace=env.temporal_namespace,
        worker_context_factory=env.worker_context_factory,
        worker_application=cfg.application,
        worker_runtime_declarations_hash=compiled.runtime_declarations_hash,
        worker_service_account=env.worker_service_account,
        worker_priority_class=env.worker_priority_class,
        payload_encryption_secret=env.payload_encryption_secret,
        worker_environment=worker_environment,
        worker_secret_environment=env.worker_secret_environment,
        lanes=tuple(compiled.lanes),
        queue_by_lane=env.queues,
    )
    return chart, worker_environment, deployment_config


def apply_configured_application(
    cfg: JulepConfig,
    env: EnvConfig,
    *,
    publish_only: bool = False,
    mcp_snapshot: bool = False,
) -> tuple[ApplicationRelease, tuple[LaneApplyResult, ...]]:
    if env.worker_image is None:
        raise ValueError(f"env {env.name!r} requires immutable worker_image=repository@sha256:...")
    compiled = compile_application(cfg, env, mcp_snapshot=mcp_snapshot)
    signing_key = _env.get(_env.JULEP_BUNDLE_SIGNING_KEY)
    chart, worker_environment, deployment_config = _resolve_deployment_config(
        cfg,
        env,
        compiled,
        require_private_signer=True,
    )
    assert env.release_store is not None
    store = artifact_store_from_url(env.release_store)
    release = publish_application(
        compiled,
        store,
        worker_image=env.worker_image,
        deployment_config=deployment_config,
        signing_key=signing_key,
    )
    results: tuple[LaneApplyResult, ...] = ()
    if not publish_only:
        assert env.temporal_address is not None
        assert env.worker_context_factory is not None
        assert env.payload_encryption_secret is not None
        reconciler = HelmLaneReconciler(
            chart=chart,
            namespace=env.kubernetes_namespace,
            temporal_address=env.temporal_address,
            temporal_namespace=env.temporal_namespace,
            worker_context_factory=env.worker_context_factory,
            worker_application=cfg.application,
            worker_runtime_declarations_hash=compiled.runtime_declarations_hash,
            worker_service_account=env.worker_service_account,
            worker_priority_class=env.worker_priority_class,
            payload_encryption_secret=env.payload_encryption_secret,
            worker_environment=worker_environment,
            worker_secret_environment=env.worker_secret_environment,
        )
        results = reconcile_application(release, reconciler, queue_by_lane=env.queues)
    if not publish_only:
        write_applied_state(
            cfg.root,
            env.name,
            AppliedApplicationState(
                application=release.application,
                application_artifact_hash=release.application_artifact_hash,
                release_hash=release.release_hash,
                worker_image=release.worker_image,
                lanes=results,
            ),
        )
    return release, results


def application_state_path(root: str | Path, env: str) -> Path:
    return Path(root) / ".julep" / "releases" / f"{env}.json"


def _resolve_helm_chart(root: Path, chart: str) -> str:
    if chart.startswith("oci://"):
        return chart
    path = Path(chart)
    if not path.is_absolute():
        path = root / path
    return str(path)


def write_applied_state(
    root: str | Path,
    env: str,
    state: AppliedApplicationState,
) -> None:
    path = application_state_path(root, env)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_json(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_applied_state(root: str | Path, env: str) -> Optional[AppliedApplicationState]:
    path = application_state_path(root, env)
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"application state must be a JSON object: {path}")
    lanes_raw = raw.get("lanes", [])
    if not isinstance(lanes_raw, list):
        raise ValueError(f"application state lanes must be a list: {path}")
    lanes = tuple(
        LaneApplyResult(
            lane=str(item["lane"]),
            release_name=str(item["releaseName"]),
            task_queue=str(item["taskQueue"]),
        )
        for item in lanes_raw
        if isinstance(item, dict)
    )
    return AppliedApplicationState(
        application=str(raw["application"]),
        application_artifact_hash=str(raw["applicationArtifactHash"]),
        release_hash=str(raw["releaseHash"]),
        worker_image=str(raw["workerImage"]),
        lanes=lanes,
    )


def observe_application(cfg: JulepConfig, env: EnvConfig) -> ObservedApplicationState:
    """Aggregate recorded release, live Helm/KEDA, and Temporal lane state."""

    state = read_applied_state(cfg.root, env.name)
    declared = resolve_application(cfg, env)
    lane_names = sorted({pipeline.lane for pipeline in declared.pipelines})
    recorded_lanes = {lane.lane: lane for lane in (state.lanes if state is not None else ())}
    discovered = _discover_application_deployments(
        declared.name,
        env.kubernetes_namespace,
        preferred_release_names={
            lane: recorded.release_name for lane, recorded in recorded_lanes.items()
        },
    )
    lanes: dict[str, LaneObservation] = {}
    live_release_hashes: set[str] = set()
    live_artifact_hashes: set[str] = set()
    live_worker_images: set[str] = set()
    for lane in lane_names:
        recorded = recorded_lanes.get(lane)
        discovered_deployment = discovered.get(lane)
        discovered_metadata = (
            discovered_deployment.get("metadata")
            if isinstance(discovered_deployment, dict)
            else None
        )
        discovered_name = (
            discovered_metadata.get("name") if isinstance(discovered_metadata, dict) else None
        )
        release_name = (
            str(discovered_name)
            if discovered_name
            else (
                recorded.release_name
                if recorded is not None
                else lane_release_name(declared.name, lane)
            )
        )
        discovered_queue = _deployment_task_queue(discovered_deployment)
        task_queue = discovered_queue or (
            recorded.task_queue if recorded is not None else env.queues.get(lane, lane)
        )
        (
            release_hash,
            artifact_hash,
            worker_image,
            live_deployment_config_hash,
        ) = _deployment_release_metadata(
            release_name,
            env.kubernetes_namespace,
            deployment=discovered_deployment,
        )
        if release_hash:
            live_release_hashes.add(release_hash)
        if artifact_hash:
            live_artifact_hashes.add(artifact_hash)
        if worker_image:
            live_worker_images.add(worker_image)
        helm_ready, helm_detail = _helm_ready(release_name, env.kubernetes_namespace)
        scaled_object, keda_ready, keda_detail = _keda_observation(
            release_name, env.kubernetes_namespace
        )
        live_config_matches_helm, live_config_detail = _live_resources_match_helm(
            release_name,
            env.kubernetes_namespace,
            deployment=discovered_deployment,
            scaled_object=scaled_object,
        )
        worker_ready, worker_detail = _deployment_ready(discovered_deployment)
        backlog, running, runtime_healthy, runtime_detail = _temporal_status(
            env,
            task_queue,
        )
        lanes[lane] = LaneObservation(
            lane=lane,
            release_hash=release_hash,
            helm_ready=helm_ready,
            keda_ready=keda_ready,
            worker_ready=worker_ready,
            temporal_backlog=backlog,
            temporal_running=running,
            runtime_healthy=runtime_healthy,
            worker_image=worker_image,
            deployment_config_hash=live_deployment_config_hash,
            live_config_matches_helm=live_config_matches_helm,
            detail="; ".join(
                detail
                for detail in (
                    helm_detail,
                    worker_detail,
                    keda_detail,
                    live_config_detail,
                    runtime_detail,
                )
                if detail
            ),
        )
    observed_release = (
        next(iter(live_release_hashes))
        if len(live_release_hashes) == 1
        else (
            "mixed:" + ",".join(sorted(live_release_hashes))
            if live_release_hashes
            else (state.release_hash if state is not None else None)
        )
    )
    observed_artifact = (
        next(iter(live_artifact_hashes))
        if len(live_artifact_hashes) == 1
        else (
            "mixed:" + ",".join(sorted(live_artifact_hashes))
            if live_artifact_hashes
            else (state.application_artifact_hash if state is not None else None)
        )
    )
    observed_worker_image = (
        next(iter(live_worker_images))
        if len(live_worker_images) == 1
        else (
            "mixed:" + ",".join(sorted(live_worker_images))
            if live_worker_images
            else (state.worker_image if state is not None else None)
        )
    )
    return ObservedApplicationState(
        application_artifact_hash=observed_artifact,
        release_hash=observed_release,
        recorded_release_hash=(
            next(iter(live_release_hashes))
            if len(live_release_hashes) == 1
            else (state.release_hash if not live_release_hashes and state is not None else None)
        ),
        worker_image=observed_worker_image,
        lanes=lanes,
    )


def _deployment_release_metadata(
    release_name: str,
    namespace: str,
    *,
    deployment: Optional[dict[str, Any]] = None,
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    data = deployment
    if data is None:
        data, _detail = _json_command(
            [
                "kubectl",
                "get",
                "deployment",
                release_name,
                "--namespace",
                namespace,
                "-o",
                "json",
            ]
        )
    if data is None:
        return None, None, None, None
    metadata = data.get("metadata")
    annotations = metadata.get("annotations") if isinstance(metadata, dict) else None
    if not isinstance(annotations, dict):
        annotations = {}
    release_hash = annotations.get("julep.ai/release-hash")
    artifact_hash = annotations.get("julep.ai/application-artifact-hash")
    deployment_config_hash = annotations.get("julep.ai/deployment-config-hash")
    spec = data.get("spec")
    template = spec.get("template") if isinstance(spec, dict) else None
    pod_spec = template.get("spec") if isinstance(template, dict) else None
    containers = pod_spec.get("containers", []) if isinstance(pod_spec, dict) else []
    worker_image: Optional[str] = None
    for container in containers if isinstance(containers, list) else []:
        if isinstance(container, dict) and container.get("name") == "worker":
            image = container.get("image")
            worker_image = str(image) if image else None
            break
    return (
        str(release_hash) if release_hash else None,
        str(artifact_hash) if artifact_hash else None,
        worker_image,
        str(deployment_config_hash) if deployment_config_hash else None,
    )


def _discover_application_deployments(
    application: str,
    namespace: str,
    *,
    preferred_release_names: Optional[Mapping[str, str]] = None,
) -> dict[str, dict[str, Any]]:
    data, _detail = _json_command(
        [
            "kubectl",
            "get",
            "deployments",
            "--namespace",
            namespace,
            "-o",
            "json",
        ]
    )
    items = data.get("items", []) if isinstance(data, dict) else []
    by_lane: dict[str, list[dict[str, Any]]] = {}
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        metadata = item.get("metadata")
        annotations = metadata.get("annotations") if isinstance(metadata, dict) else None
        if not isinstance(annotations, dict):
            continue
        if annotations.get("julep.ai/application") != application:
            continue
        lane = annotations.get("julep.ai/lane")
        if isinstance(lane, str) and lane:
            by_lane.setdefault(lane, []).append(item)

    selected: dict[str, dict[str, Any]] = {}
    for lane, candidates in by_lane.items():
        preferred_name = (preferred_release_names or {}).get(lane)
        preferred = next(
            (
                candidate
                for candidate in candidates
                if _deployment_name(candidate) == preferred_name
            ),
            None,
        )
        selected[lane] = (
            preferred if preferred is not None else max(candidates, key=_deployment_sort_key)
        )
    return selected


def _deployment_name(deployment: dict[str, Any]) -> str:
    metadata = deployment.get("metadata")
    if not isinstance(metadata, dict):
        return ""
    return str(metadata.get("name", ""))


def _deployment_sort_key(deployment: dict[str, Any]) -> tuple[str, str]:
    metadata = deployment.get("metadata")
    if not isinstance(metadata, dict):
        return "", ""
    return str(metadata.get("creationTimestamp", "")), _deployment_name(deployment)


def _deployment_task_queue(deployment: Optional[dict[str, Any]]) -> Optional[str]:
    if not isinstance(deployment, dict):
        return None
    spec = deployment.get("spec")
    template = spec.get("template") if isinstance(spec, dict) else None
    pod_spec = template.get("spec") if isinstance(template, dict) else None
    containers = pod_spec.get("containers", []) if isinstance(pod_spec, dict) else []
    for container in containers if isinstance(containers, list) else []:
        if not isinstance(container, dict) or container.get("name") != "worker":
            continue
        environment = container.get("env", [])
        for entry in environment if isinstance(environment, list) else []:
            if isinstance(entry, dict) and entry.get("name") == "TEMPORAL_TASK_QUEUE":
                value = entry.get("value")
                return str(value) if value else None
    return None


def _deployment_ready(
    deployment: Optional[dict[str, Any]],
) -> tuple[Optional[bool], str]:
    """Report whether the live worker Deployment has completed its rollout."""

    if not isinstance(deployment, dict):
        return None, "deployment=unknown"
    metadata = deployment.get("metadata")
    spec = deployment.get("spec")
    status = deployment.get("status")
    if not isinstance(spec, dict) or not isinstance(status, dict):
        return None, "deployment=unknown"
    desired = _coerce_nonnegative_int(spec.get("replicas", 1))
    if desired is None:
        return None, "deployment=unknown"
    if desired == 0:
        return True, "deployment=scaled-to-zero"
    generation = (
        _coerce_nonnegative_int(metadata.get("generation")) if isinstance(metadata, dict) else None
    )
    observed_generation = _coerce_nonnegative_int(status.get("observedGeneration"))
    updated = _coerce_nonnegative_int(status.get("updatedReplicas", 0))
    available = _coerce_nonnegative_int(status.get("availableReplicas", 0))
    unavailable = _coerce_nonnegative_int(status.get("unavailableReplicas", 0))
    if None in (generation, observed_generation, updated, available, unavailable):
        return None, "deployment=unknown"
    assert generation is not None
    assert observed_generation is not None
    assert updated is not None
    assert available is not None
    assert unavailable is not None
    ready = (
        observed_generation >= generation
        and updated >= desired
        and available >= desired
        and unavailable == 0
    )
    return ready, f"deployment={'ready' if ready else 'not-ready'}"


def _coerce_nonnegative_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None


def _helm_ready(release_name: str, namespace: str) -> tuple[Optional[bool], str]:
    data, detail = _json_command(
        ["helm", "status", release_name, "--namespace", namespace, "-o", "json"]
    )
    if data is None:
        return None, detail
    info = data.get("info")
    status = info.get("status") if isinstance(info, dict) else None
    return status == "deployed", f"helm={status or 'unknown'}"


def _keda_observation(
    release_name: str,
    namespace: str,
) -> tuple[Optional[dict[str, Any]], Optional[bool], str]:
    data, detail = _json_command(
        [
            "kubectl",
            "get",
            "scaledobject",
            f"{release_name}-temporal",
            "--namespace",
            namespace,
            "-o",
            "json",
        ]
    )
    if data is None:
        return None, None, detail
    status = data.get("status")
    conditions = status.get("conditions", []) if isinstance(status, dict) else []
    for condition in conditions if isinstance(conditions, list) else []:
        if isinstance(condition, dict) and condition.get("type") == "Ready":
            ready = str(condition.get("status", "")).lower() == "true"
            return data, ready, f"keda={'ready' if ready else 'not-ready'}"
    return data, None, "keda=unknown"


def _live_resources_match_helm(
    release_name: str,
    namespace: str,
    *,
    deployment: Optional[dict[str, Any]],
    scaled_object: Optional[dict[str, Any]],
) -> tuple[Optional[bool], str]:
    """Compare live lane specs with the manifest stored in the Helm release.

    The release annotation proves which immutable deployment configuration was
    applied. This comparison covers a different failure mode: an out-of-band
    edit leaves that annotation untouched. Kubernetes-managed Deployment
    replicas and all server-populated metadata/status are intentionally
    excluded from the comparison.
    """

    if not isinstance(deployment, dict) or not isinstance(scaled_object, dict):
        return None, "helm-manifest=unknown"
    manifest, detail = _text_command(
        ["helm", "get", "manifest", release_name, "--namespace", namespace]
    )
    if manifest is None:
        return None, f"helm-manifest={detail or 'unavailable'}"
    try:
        documents = [
            document for document in yaml.safe_load_all(manifest) if isinstance(document, dict)
        ]
    except yaml.YAMLError:
        return None, "helm-manifest=invalid-yaml"

    expected_deployment = _manifest_resource(
        documents,
        kind="Deployment",
        name=release_name,
    )
    expected_scaled_object = _manifest_resource(
        documents,
        kind="ScaledObject",
        name=f"{release_name}-temporal",
    )
    if expected_deployment is None or expected_scaled_object is None:
        return None, "helm-manifest=missing-resource"

    deployment_matches = _resource_spec_matches(
        expected_deployment,
        deployment,
        ignored_fields=frozenset({"replicas"}),
    )
    scaled_object_matches = _resource_spec_matches(
        expected_scaled_object,
        scaled_object,
    )
    matches = deployment_matches and scaled_object_matches
    return matches, f"helm-manifest={'clean' if matches else 'drift'}"


def _manifest_resource(
    documents: Sequence[dict[str, Any]],
    *,
    kind: str,
    name: str,
) -> Optional[dict[str, Any]]:
    for document in documents:
        metadata = document.get("metadata")
        if (
            document.get("kind") == kind
            and isinstance(metadata, dict)
            and metadata.get("name") == name
        ):
            return document
    return None


def _resource_spec_matches(
    expected: Mapping[str, Any],
    live: Mapping[str, Any],
    *,
    ignored_fields: frozenset[str] = frozenset(),
) -> bool:
    expected_spec = expected.get("spec")
    live_spec = live.get("spec")
    if not isinstance(expected_spec, dict) or not isinstance(live_spec, dict):
        return False
    expected_fields = {
        key: value for key, value in expected_spec.items() if key not in ignored_fields
    }
    live_fields = {key: value for key, value in live_spec.items() if key not in ignored_fields}
    return _contains_expected(expected_fields, live_fields)


def _contains_expected(expected: Any, live: Any) -> bool:
    """Match rendered Helm fields while ignoring API-defaulted live fields."""

    if isinstance(expected, dict):
        return isinstance(live, dict) and all(
            key in live and _contains_expected(value, live[key]) for key, value in expected.items()
        )
    if isinstance(expected, list):
        if not isinstance(live, list):
            return False
        identity_key = next(
            (
                key
                for key in ("name", "type")
                if expected and all(isinstance(item, dict) and key in item for item in expected)
            ),
            None,
        )
        if identity_key is not None:
            indexed = {
                item.get(identity_key): item
                for item in live
                if isinstance(item, dict) and identity_key in item
            }
            return all(
                item[identity_key] in indexed
                and _contains_expected(item, indexed[item[identity_key]])
                for item in expected
            )
        return len(live) >= len(expected) and all(
            _contains_expected(item, live[index]) for index, item in enumerate(expected)
        )
    return bool(expected == live)


def _temporal_status(
    env: EnvConfig,
    task_queue: str,
) -> tuple[Optional[int], Optional[int], Optional[bool], str]:
    if env.temporal_address is None:
        return None, None, None, "temporal=unconfigured"
    base = [
        "--address",
        env.temporal_address,
        "--namespace",
        env.temporal_namespace,
    ]
    queue_data: dict[str, Optional[dict[str, Any]]] = {}
    queue_details: list[str] = []
    queue_backlogs: list[Optional[int]] = []
    for queue_type in ("workflow", "activity"):
        queue_args = [
            "temporal",
            "task-queue",
            "describe",
            *base,
            "--task-queue",
            task_queue,
            "--task-queue-type",
            queue_type,
        ]
        data, detail = _json_command([*queue_args, "--report-stats", "--output", "json"])
        if data is None and _unsupported_cli_option(detail, "report-stats"):
            # Temporal CLI 0.11 predates --report-stats, but its ordinary JSON
            # response still exposes TaskQueueStatus.BacklogCountHint.
            data, detail = _json_command([*queue_args, "--output", "json"])
        queue_data[queue_type] = data
        queue_backlogs.append(_temporal_queue_backlog(data))
        if detail:
            queue_details.append(f"{queue_type}-queue:{detail}")

    count_args = [
        "temporal",
        "workflow",
        "count",
        *base,
        "--query",
        f'TaskQueue="{task_queue}" AND ExecutionStatus="Running"',
    ]
    count_data, count_detail = _json_command([*count_args, "--output", "json"])
    running = _find_int(count_data, {"count"})
    if count_data is None and _unsupported_cli_option(count_detail, "output"):
        # Temporal CLI 0.11 has no structured-output flag for workflow count;
        # its stable scripting surface is a single ``Total: <n>`` line.
        count_output, count_detail = _text_command(count_args)
        running = _parse_temporal_workflow_count(count_output)
        if count_output is not None and running is None:
            count_detail = "temporal=invalid-workflow-count-output"

    backlog = (
        sum(value for value in queue_backlogs if value is not None)
        if all(value is not None for value in queue_backlogs)
        else None
    )
    healthy: Optional[bool] = None
    queue_reachable = all(data is not None for data in queue_data.values())
    count_reachable = count_data is not None or running is not None
    if queue_reachable and count_reachable:
        healthy = True
    elif queue_reachable or count_reachable:
        healthy = False
    detail = "; ".join([*queue_details, *([count_detail] if count_detail else [])])
    return backlog, running, healthy, detail


def _unsupported_cli_option(detail: str, option: str) -> bool:
    """Recognize option-parser failures across Temporal CLI generations."""

    normalized = option.lstrip("-").lower()
    lowered = detail.lower()
    unsupported = (
        "flag provided but not defined" in lowered
        or "unknown flag" in lowered
        or "unknown option" in lowered
        or "unrecognized option" in lowered
    )
    return unsupported and normalized in lowered


def _parse_temporal_workflow_count(output: Optional[str]) -> Optional[int]:
    if output is None:
        return None
    match = re.search(r"(?mi)^\s*total:\s*([0-9]+)\s*$", output)
    return int(match.group(1)) if match is not None else None


def _temporal_queue_backlog(data: Optional[dict[str, Any]]) -> Optional[int]:
    """Read modern aggregate stats or sum every legacy queue partition."""

    if not isinstance(data, dict):
        return None
    stats = data.get("stats")
    aggregate_keys = {"approximatebacklogcount", "backlogcount"}
    aggregate = _find_int(stats, aggregate_keys)
    if aggregate is not None:
        return aggregate

    task_queues = data.get("taskQueues", data.get("task_queues"))
    if isinstance(task_queues, list) and task_queues:
        hints = [_find_int(partition, {"backlogcounthint"}) for partition in task_queues]
        if all(hint is not None for hint in hints):
            return sum(hint for hint in hints if hint is not None)
        return None

    aggregate = _find_int(data, aggregate_keys)
    if aggregate is not None:
        return aggregate
    return _find_int(data, {"backlogcounthint"})


def _find_int(value: Any, keys: set[str]) -> Optional[int]:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).replace("_", "").lower() in keys:
                found = _coerce_nonnegative_int(item)
                if found is not None:
                    return found
        for item in value.values():
            found = _find_int(item, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_int(item, keys)
            if found is not None:
                return found
    return None


def _json_command(args: Sequence[str]) -> tuple[Optional[dict[str, Any]], str]:
    try:
        proc = subprocess.run(list(args), capture_output=True, text=True, timeout=20)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return None, f"{args[0]}={type(exc).__name__}"
    if proc.returncode != 0:
        detail = proc.stderr.strip().splitlines()
        return None, f"{args[0]}={(detail[-1] if detail else 'unavailable')}"
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, f"{args[0]}=invalid-json"
    if not isinstance(data, dict):
        return None, f"{args[0]}=invalid-response"
    return data, ""


def _text_command(args: Sequence[str]) -> tuple[Optional[str], str]:
    try:
        proc = subprocess.run(list(args), capture_output=True, text=True, timeout=20)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return None, f"{args[0]}={type(exc).__name__}"
    if proc.returncode != 0:
        detail = proc.stderr.strip().splitlines()
        return None, f"{args[0]}={(detail[-1] if detail else 'unavailable')}"
    return proc.stdout, ""


__all__ = [
    "AppliedApplicationState",
    "application_state_path",
    "apply_configured_application",
    "compile_application",
    "load_application",
    "observe_application",
    "plan_configured_application",
    "read_applied_state",
    "resolve_application",
    "write_applied_state",
]
