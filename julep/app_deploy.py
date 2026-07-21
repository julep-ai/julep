"""Immutable application releases and lane reconciliation.

Release manifests are content-addressed objects stored through the same CAS
interface as Julep bundles.  Publishing and reconciling are separate operations:
publishing makes a release available, while a lane reconciler installs inactive
worker capacity.  Neither operation mutates an application's traffic route.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from functools import cached_property
from pathlib import Path
from typing import Any, Optional, Protocol

from . import _env
from .app import CompiledApplication
from .cas import CASStore
from .deploy import WorkflowStartOptions, _start_temporal_workflow
from .ir import canonical_json

_IMAGE_DIGEST = re.compile(r"^(?P<repository>[^@\s]+)@(?P<digest>sha256:[0-9a-f]{64})$")
_OCI_CHART_DIGEST = re.compile(r"^oci://[^\s@]+@sha256:[0-9a-f]{64}$")
_K8S_NAME = re.compile(r"[^a-z0-9-]+")
_K8S_DNS_SUBDOMAIN = re.compile(
    r"^[a-z0-9](?:[-a-z0-9]*[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[-a-z0-9]*[a-z0-9])?)*$"
)
_K8S_DNS_SUBDOMAIN_MAX_LENGTH = 253
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_WORKER_MAX_CONCURRENT_ACTIVITIES = 1
_RELEASE_SCHEMA_VERSION = 2
_PAYLOAD_KEYRING_KEY = "keyring"
_PAYLOAD_ACTIVE_KEY_ID_KEY = "active-key-id"
_RESERVED_WORKER_ENVIRONMENT = frozenset(
    {
        _env.JULEP_WORKER_BUILD_ID,
        _env.JULEP_WORKER_VERSIONING,
        "TEMPORAL_ADDRESS",
        "TEMPORAL_NAMESPACE",
        "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED",
        "TEMPORAL_PAYLOAD_KEYS",
        "TEMPORAL_PAYLOAD_KEY_ID",
        "TEMPORAL_TASK_QUEUE",
        "WORKER_APPLICATION",
        "WORKER_CONTEXT_FACTORY",
        "WORKER_GRACEFUL_SHUTDOWN_S",
        "WORKER_HEALTH_PORT",
        "WORKER_MAX_CONCURRENT_ACTIVITIES",
        "WORKER_RUNTIME_DECLARATIONS_HASH",
    }
)


class ApplicationReleaseError(RuntimeError):
    pass


def _release_schema_error(version: Any) -> ApplicationReleaseError:
    return ApplicationReleaseError(
        f"unsupported application release schema version {version!r}; "
        f"version {_RELEASE_SCHEMA_VERSION} is required; "
        "re-publish with this julep version"
    )


class _FrozenJsonDict(dict[str, Any]):
    """A JSON-compatible mapping that rejects mutation at every nesting level."""

    @staticmethod
    def _immutable(*_args: Any, **_kwargs: Any) -> None:
        raise TypeError("published application release data is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable  # type: ignore[assignment]
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable  # type: ignore[assignment]


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _FrozenJsonDict({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw_json(item) for item in value]
    return value


def _normalize_runtime_declarations_ref(value: Any) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {"hash", "size"}:
        raise ApplicationReleaseError(
            "runtime declarations ref must contain exactly 'hash' and 'size'"
        )
    digest = value.get("hash")
    size = value.get("size")
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
        raise ApplicationReleaseError(
            "runtime declarations ref hash must be sha256:<64 lowercase hex>"
        )
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ApplicationReleaseError("runtime declarations ref size must be a non-negative integer")
    return {"hash": digest, "size": size}


@dataclass(frozen=True)
class PipelineRelease:
    name: str
    lane: str
    artifact_hash: str
    flow_json: dict[str, Any]
    manifest_json: dict[str, Any]
    pinned_pures: dict[str, str]
    bundle_ref: Optional[list[dict[str, str]]]
    eval_packages: tuple[str, ...]
    runtime_declarations_ref: Optional[dict[str, Any]] = None
    max_call_limits: Mapping[str, int] = field(default_factory=dict)
    task_queue: Optional[str] = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "flow_json", _freeze_json(self.flow_json))
        object.__setattr__(self, "manifest_json", _freeze_json(self.manifest_json))
        object.__setattr__(self, "pinned_pures", _freeze_json(self.pinned_pures))
        object.__setattr__(
            self,
            "bundle_ref",
            _freeze_json(self.bundle_ref) if self.bundle_ref is not None else None,
        )
        object.__setattr__(self, "eval_packages", tuple(self.eval_packages))
        object.__setattr__(
            self,
            "runtime_declarations_ref",
            _freeze_json(_normalize_runtime_declarations_ref(self.runtime_declarations_ref))
            if self.runtime_declarations_ref is not None
            else None,
        )
        object.__setattr__(self, "max_call_limits", _freeze_json(self.max_call_limits))

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "lane": self.lane,
            "artifactHash": self.artifact_hash,
            "flowJson": _thaw_json(self.flow_json),
            "manifestJson": _thaw_json(self.manifest_json),
            "pinnedPures": _thaw_json(self.pinned_pures),
            "bundleRef": _thaw_json(self.bundle_ref),
            "evalPackages": list(self.eval_packages),
            "runtimeDeclarationsRef": _thaw_json(self.runtime_declarations_ref),
            "maxCallLimits": dict(sorted(self.max_call_limits.items())),
        }

    async def start(
        self,
        client: Any,
        *,
        session_id: str,
        input: Any,
        options: WorkflowStartOptions,
        principal: Optional[dict[str, Any]] = None,
        queue_lanes: Optional[dict[str, str]] = None,
    ) -> Any:
        """Start this exact published artifact without recompiling live source."""

        if self.task_queue is None:
            raise ValueError(
                "PipelineRelease.start requires the release-specific task queue "
                "returned by julep apply"
            )
        if options.task_queue is not None and options.task_queue != self.task_queue:
            raise ValueError(
                f"task queue override {options.task_queue!r} does not match the "
                f"queue pinned by the release: {self.task_queue!r}"
            )
        task_queue = self.task_queue

        from .execution.harness import start_flow

        return await _start_temporal_workflow(
            client,
            session_id=session_id,
            options=options,
            starter=lambda: start_flow(
                client,
                _thaw_json(self.flow_json),
                _thaw_json(self.manifest_json),
                session_id=session_id,
                input=input,
                task_queue=task_queue,
                pinned_pures=_thaw_json(self.pinned_pures),
                max_call_limits=dict(self.max_call_limits),
                principal=principal,
                bundle=_thaw_json(self.bundle_ref),
                runtime_declarations_ref=_thaw_json(self.runtime_declarations_ref),
                queue_lanes=queue_lanes,
                workflow_start_options=options.temporal_kwargs(),
            ),
        )


@dataclass(frozen=True)
class ApplicationRelease:
    application: str
    application_artifact_hash: str
    worker_image: str
    pipelines: tuple[PipelineRelease, ...]
    deployment_config: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = _RELEASE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != _RELEASE_SCHEMA_VERSION
        ):
            raise _release_schema_error(self.schema_version)
        _parse_image(self.worker_image)
        pipelines = tuple(replace(pipeline, task_queue=None) for pipeline in self.pipelines)
        object.__setattr__(self, "pipelines", pipelines)
        object.__setattr__(
            self,
            "deployment_config",
            _freeze_json(self.deployment_config),
        )
        release_hash = self.release_hash
        queues = self.deployment_config.get("queues", {})
        for pipeline in self.pipelines:
            logical_queue = (
                queues.get(pipeline.lane, pipeline.lane)
                if isinstance(queues, Mapping)
                else pipeline.lane
            )
            object.__setattr__(
                pipeline,
                "task_queue",
                lane_task_queue(str(logical_queue), release_hash),
            )

    @cached_property
    def manifest(self) -> Mapping[str, Any]:
        manifest = _freeze_json(
            {
                "schemaVersion": self.schema_version,
                "application": self.application,
                "applicationArtifactHash": self.application_artifact_hash,
                "workerImage": self.worker_image,
                "deployment": _thaw_json(self.deployment_config),
                "pipelines": [pipeline.to_json() for pipeline in self.pipelines],
                "lanes": {
                    lane: sorted(
                        pipeline.name for pipeline in self.pipelines if pipeline.lane == lane
                    )
                    for lane in sorted({pipeline.lane for pipeline in self.pipelines})
                },
            }
        )
        assert isinstance(manifest, Mapping)
        return manifest

    @cached_property
    def manifest_bytes(self) -> bytes:
        return canonical_json(self.manifest).encode("utf-8")

    @cached_property
    def release_hash(self) -> str:
        return "sha256:" + hashlib.sha256(self.manifest_bytes).hexdigest()

    @property
    def lanes(self) -> tuple[str, ...]:
        return tuple(sorted({pipeline.lane for pipeline in self.pipelines}))

    def publish(self, store: CASStore) -> str:
        digest = store.put(self.manifest_bytes)
        expected = self.release_hash.removeprefix("sha256:")
        if digest != expected:
            raise ApplicationReleaseError(
                f"release CAS returned {digest}, expected content digest {expected}"
            )
        return self.release_hash


def publish_application(
    compiled: CompiledApplication,
    store: CASStore,
    *,
    worker_image: str,
    deployment_config: Optional[Mapping[str, Any]] = None,
    signing_key: Optional[str] = None,
) -> ApplicationRelease:
    """Publish pipeline bundles followed by one immutable release manifest."""

    _parse_image(worker_image)
    pipelines: list[PipelineRelease] = []
    for pipeline in compiled.pipelines:
        deployment = pipeline.deployment
        deployment.publish(store, signing_key=signing_key)
        runtime_declarations_ref: Optional[dict[str, Any]] = None
        if pipeline.runtime_declarations_blob is not None:
            blob = pipeline.runtime_declarations_blob
            digest = store.put(blob)
            expected_digest = hashlib.sha256(blob).hexdigest()
            if digest != expected_digest:
                raise ApplicationReleaseError(
                    f"declarations CAS returned {digest}, expected content digest {expected_digest}"
                )
            runtime_declarations_ref = {
                "hash": f"sha256:{digest}",
                "size": len(blob),
            }
        pinned = {
            name: source_hash
            for name, source_hash in deployment.artifact_components["pureSourceHashes"].items()
            if isinstance(name, str) and isinstance(source_hash, str)
        }
        pipelines.append(
            PipelineRelease(
                name=pipeline.spec.name,
                lane=pipeline.spec.lane,
                artifact_hash=deployment.artifact_hash,
                flow_json=deployment.flow_json,
                manifest_json=deployment.manifest_json,
                pinned_pures=pinned,
                bundle_ref=deployment.bundle_ref,
                eval_packages=tuple(pipeline.spec.eval_packages),
                runtime_declarations_ref=runtime_declarations_ref,
                max_call_limits=(
                    deployment.capabilities.max_call_limits()
                    if deployment.capabilities is not None
                    else {}
                ),
            )
        )
    release = ApplicationRelease(
        application=compiled.name,
        application_artifact_hash=compiled.artifact_hash,
        worker_image=worker_image,
        pipelines=tuple(pipelines),
        deployment_config=deployment_config or {},
    )
    release.publish(store)
    return release


@dataclass(frozen=True)
class LaneObservation:
    lane: str
    release_hash: Optional[str] = None
    helm_ready: Optional[bool] = None
    keda_ready: Optional[bool] = None
    worker_ready: Optional[bool] = None
    temporal_backlog: Optional[int] = None
    temporal_running: Optional[int] = None
    runtime_healthy: Optional[bool] = None
    worker_image: Optional[str] = None
    deployment_config_hash: Optional[str] = None
    live_config_matches_helm: Optional[bool] = None
    detail: str = ""


@dataclass(frozen=True)
class ObservedApplicationState:
    application_artifact_hash: Optional[str] = None
    release_hash: Optional[str] = None
    recorded_release_hash: Optional[str] = None
    worker_image: Optional[str] = None
    lanes: Mapping[str, LaneObservation] = field(default_factory=dict)


@dataclass(frozen=True)
class ApplicationPlan:
    application: str
    desired_artifact_hash: str
    observed_artifact_hash: Optional[str]
    artifact_drift: bool
    desired_worker_image: Optional[str]
    observed_worker_image: Optional[str]
    worker_image_drift: bool
    mcp_schema_drift: Mapping[str, bool]
    deployment_config_drift: Mapping[str, str]
    release_drift: Mapping[str, str]
    helm_keda_drift: Mapping[str, str]
    runtime_drift: Mapping[str, str]

    def to_json(self) -> dict[str, Any]:
        return {
            "application": self.application,
            "artifact": {
                "desired": self.desired_artifact_hash,
                "observed": self.observed_artifact_hash,
                "drift": self.artifact_drift,
            },
            "workerImage": {
                "desired": self.desired_worker_image,
                "observed": self.observed_worker_image,
                "drift": self.worker_image_drift,
            },
            "mcpSchema": dict(self.mcp_schema_drift),
            "deploymentConfig": dict(self.deployment_config_drift),
            "release": dict(self.release_drift),
            "helmKeda": dict(self.helm_keda_drift),
            "runtime": dict(self.runtime_drift),
        }


def plan_application(
    compiled: CompiledApplication,
    observed: Optional[ObservedApplicationState] = None,
    *,
    worker_image: Optional[str] = None,
    desired_deployment_config_hash: Optional[str] = None,
) -> ApplicationPlan:
    """Produce all four drift dimensions without mutating a store or cluster."""

    observed = observed or ObservedApplicationState()
    helm_keda: dict[str, str] = {}
    release_drift: dict[str, str] = {}
    deployment_config_drift: dict[str, str] = {}
    runtime: dict[str, str] = {}
    for lane in compiled.lanes:
        lane_observation = observed.lanes.get(lane)
        if lane_observation is None:
            helm_keda[lane] = "unknown"
            release_drift[lane] = "unknown"
            deployment_config_drift[lane] = "unknown"
            runtime[lane] = "unknown"
            continue
        if observed.recorded_release_hash is None or lane_observation.release_hash is None:
            release_drift[lane] = "unknown"
        elif lane_observation.release_hash != observed.recorded_release_hash:
            release_drift[lane] = "drift"
        else:
            release_drift[lane] = "clean"
        if (
            desired_deployment_config_hash is None
            or lane_observation.deployment_config_hash is None
        ):
            deployment_config_drift[lane] = "unknown"
        elif (
            lane_observation.deployment_config_hash != desired_deployment_config_hash
            or lane_observation.live_config_matches_helm is False
        ):
            deployment_config_drift[lane] = "drift"
        elif lane_observation.live_config_matches_helm is True:
            deployment_config_drift[lane] = "clean"
        else:
            deployment_config_drift[lane] = "unknown"
        if (
            lane_observation.helm_ready is False
            or lane_observation.keda_ready is False
            or lane_observation.worker_ready is False
            or release_drift[lane] == "drift"
            or deployment_config_drift[lane] == "drift"
        ):
            helm_keda[lane] = "drift"
        elif (
            lane_observation.helm_ready is True
            and lane_observation.keda_ready is True
            and lane_observation.worker_ready is True
        ):
            helm_keda[lane] = "ready"
        else:
            helm_keda[lane] = "unknown"
        if lane_observation.runtime_healthy is False:
            runtime[lane] = "degraded"
        elif lane_observation.runtime_healthy is True:
            runtime[lane] = "healthy"
        else:
            runtime[lane] = "unknown"
    return ApplicationPlan(
        application=compiled.name,
        desired_artifact_hash=compiled.artifact_hash,
        observed_artifact_hash=observed.application_artifact_hash,
        artifact_drift=observed.application_artifact_hash != compiled.artifact_hash,
        desired_worker_image=worker_image,
        observed_worker_image=observed.worker_image,
        worker_image_drift=(worker_image is not None and worker_image != observed.worker_image),
        mcp_schema_drift={
            pipeline.spec.name: pipeline.mcp_schema_drift for pipeline in compiled.pipelines
        },
        deployment_config_drift=deployment_config_drift,
        release_drift=release_drift,
        helm_keda_drift=helm_keda,
        runtime_drift=runtime,
    )


@dataclass(frozen=True)
class LaneApplyResult:
    lane: str
    release_name: str
    task_queue: str


class LaneReconciler(Protocol):
    def reconcile(
        self,
        release: ApplicationRelease,
        lane: str,
        *,
        task_queue: str,
    ) -> LaneApplyResult: ...


CommandRunner = Callable[[Sequence[str]], None]


class HelmLaneReconciler:
    """Reconcile one Helm release per logical lane."""

    def __init__(
        self,
        *,
        chart: str,
        namespace: str,
        temporal_address: str,
        worker_context_factory: str,
        payload_encryption_secret: str,
        worker_application: Optional[str] = None,
        worker_runtime_declarations_hash: Optional[str] = None,
        worker_service_account: Optional[str] = None,
        worker_priority_class: Optional[str] = None,
        temporal_namespace: str = "default",
        worker_environment: Optional[Mapping[str, str]] = None,
        worker_secret_environment: Optional[Mapping[str, Mapping[str, str]]] = None,
        runner: Optional[CommandRunner] = None,
    ) -> None:
        if not worker_context_factory.strip():
            raise ApplicationReleaseError("worker_context_factory must be non-empty")
        _validate_kubernetes_object_name(
            payload_encryption_secret,
            field="payload_encryption_secret",
        )
        if worker_priority_class is not None:
            _validate_kubernetes_object_name(
                worker_priority_class,
                field="worker_priority_class",
            )
        _validate_worker_application(
            worker_application,
            worker_runtime_declarations_hash,
        )
        self.chart = chart
        self.namespace = namespace
        self.temporal_address = temporal_address
        self.temporal_namespace = temporal_namespace
        self.worker_context_factory = worker_context_factory
        self.payload_encryption_secret = payload_encryption_secret
        self.worker_application = worker_application
        self.worker_runtime_declarations_hash = worker_runtime_declarations_hash
        self.worker_service_account = worker_service_account
        self.worker_priority_class = worker_priority_class
        self.worker_environment = dict(worker_environment or {})
        self.worker_secret_environment = {
            name: dict(source) for name, source in (worker_secret_environment or {}).items()
        }
        self._runner = runner or _run_command

    def reconcile(
        self,
        release: ApplicationRelease,
        lane: str,
        *,
        task_queue: str,
    ) -> LaneApplyResult:
        if lane not in release.lanes:
            raise ApplicationReleaseError(f"release {release.release_hash} has no lane {lane!r}")
        repository, digest = _parse_image(release.worker_image)
        self._validate_deployment_config(release, lane, task_queue=task_queue)
        release_name = lane_release_name(
            release.application,
            lane,
            release_hash=release.release_hash,
        )
        release_task_queue = lane_task_queue(task_queue, release.release_hash)
        args = [
            "helm",
            "upgrade",
            "--install",
            release_name,
            self.chart,
            "--namespace",
            self.namespace,
            "--create-namespace",
            "--atomic",
            "--wait",
            "--set-string",
            f"image.repository={repository}",
            "--set-string",
            f"image.digest={digest}",
            "--set-string",
            f"temporal.address={self.temporal_address}",
            "--set-string",
            f"temporal.namespace={self.temporal_namespace}",
            "--set-string",
            f"temporal.taskQueue={release_task_queue}",
            "--set-string",
            f"worker.releaseHash={release.release_hash}",
            "--set-string",
            f"worker.applicationArtifactHash={release.application_artifact_hash}",
            "--set-string",
            f"worker.application={release.application}",
            "--set-string",
            f"worker.deploymentRevision={release.release_hash}",
            "--set-string",
            f"worker.deploymentConfigHash={deployment_config_hash(release.deployment_config)}",
            "--set-string",
            f"worker.lane={lane}",
            "--set",
            "payloadEncryption.enabled=true",
            "--set",
            "payloadEncryption.required=true",
            "--set-string",
            f"payloadEncryption.secretName={self.payload_encryption_secret}",
            "--set-string",
            f"payloadEncryption.keyringKey={_PAYLOAD_KEYRING_KEY}",
            "--set-string",
            f"payloadEncryption.activeKeyIdKey={_PAYLOAD_ACTIVE_KEY_ID_KEY}",
        ]
        args.extend(
            [
                "--set-string",
                f"worker.contextFactory={self.worker_context_factory}",
                "--set-string",
                f"worker.maxConcurrentActivities={_WORKER_MAX_CONCURRENT_ACTIVITIES}",
                "--set-string",
                f"worker.priorityClassName={self.worker_priority_class or ''}",
            ]
        )
        if self.worker_application is not None:
            assert self.worker_runtime_declarations_hash is not None
            args.extend(
                [
                    "--set-string",
                    f"worker.applicationSpec={self.worker_application}",
                    "--set-string",
                    f"worker.runtimeDeclarationsHash={self.worker_runtime_declarations_hash}",
                ]
            )
        if self.worker_service_account:
            args.extend(
                [
                    "--set",
                    "serviceAccount.create=false",
                    "--set-string",
                    f"serviceAccount.name={self.worker_service_account}",
                ]
            )
        if self.worker_environment:
            args.extend(
                [
                    "--set-json",
                    "worker.environment="
                    + json.dumps(
                        self.worker_environment,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ]
            )
        secret_environment: dict[str, dict[str, str]] = {}
        for name, source in sorted(self.worker_secret_environment.items()):
            secret_name = source.get("secret_name")
            key = source.get("key")
            if not secret_name or not key:
                raise ApplicationReleaseError(
                    f"worker secret environment {name!r} requires secret_name and key"
                )
            secret_environment[name] = {"secretName": secret_name, "key": key}
        if secret_environment:
            args.extend(
                [
                    "--set-json",
                    "worker.secretEnvironment="
                    + json.dumps(
                        secret_environment,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ]
            )
        self._runner(args)
        self._runner(
            [
                "helm",
                "test",
                release_name,
                "--namespace",
                self.namespace,
                "--timeout",
                "2m",
                "--logs",
            ]
        )
        return LaneApplyResult(
            lane=lane,
            release_name=release_name,
            task_queue=release_task_queue,
        )

    def _validate_deployment_config(
        self,
        release: ApplicationRelease,
        lane: str,
        *,
        task_queue: str,
    ) -> None:
        expected = build_lane_deployment_config(
            chart=self.chart,
            namespace=self.namespace,
            temporal_address=self.temporal_address,
            temporal_namespace=self.temporal_namespace,
            worker_context_factory=self.worker_context_factory,
            worker_application=self.worker_application,
            worker_runtime_declarations_hash=self.worker_runtime_declarations_hash,
            worker_service_account=self.worker_service_account,
            worker_priority_class=self.worker_priority_class,
            payload_encryption_secret=self.payload_encryption_secret,
            worker_environment=self.worker_environment,
            worker_secret_environment=self.worker_secret_environment,
            lanes=release.lanes,
            queue_by_lane={
                candidate: (
                    task_queue
                    if candidate == lane
                    else _deployment_queue(release.deployment_config, candidate)
                )
                for candidate in release.lanes
            },
        )
        if canonical_json(expected) != canonical_json(release.deployment_config):
            raise ApplicationReleaseError(
                "lane reconciler configuration does not match the immutable "
                f"deployment config in release {release.release_hash}"
            )


def reconcile_application(
    release: ApplicationRelease,
    reconciler: LaneReconciler,
    *,
    queue_by_lane: Optional[Mapping[str, str]] = None,
) -> tuple[LaneApplyResult, ...]:
    queue_by_lane = queue_by_lane or {}
    unknown = sorted(set(queue_by_lane) - set(release.lanes))
    if unknown:
        raise ApplicationReleaseError(
            "queue mapping references unknown lanes: " + ", ".join(unknown)
        )
    return tuple(
        reconciler.reconcile(
            release,
            lane,
            task_queue=queue_by_lane.get(lane, lane),
        )
        for lane in release.lanes
    )


def _parse_image(image: str) -> tuple[str, str]:
    match = _IMAGE_DIGEST.fullmatch(image)
    if match is None:
        raise ApplicationReleaseError(
            "worker image must be immutable and use repository@sha256:<64 lowercase hex>"
        )
    return match.group("repository"), match.group("digest")


def lane_release_name(
    application: str,
    lane: str,
    *,
    release_hash: Optional[str] = None,
) -> str:
    suffix = ""
    if release_hash is not None:
        digest = release_hash.removeprefix("sha256:")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ApplicationReleaseError("release hash must be sha256:<64 lowercase hex>")
        suffix = f"-r{digest[:10]}"
    identity = f"{application}-{lane}{suffix}"
    normalized = identity.lower()
    raw = _K8S_NAME.sub("-", normalized).strip("-")
    if not raw:
        raise ApplicationReleaseError("application and lane do not form a Kubernetes name")
    # Kubernetes/Helm normalization is lossy (for example ``.`` and ``_`` both
    # become ``-``). Preserve readable names while disambiguating every input
    # whose exact identity did not survive normalization.
    identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:8]
    if raw != identity:
        raw = f"{raw}-{identity_hash}"
    if len(raw) <= 53:
        return raw
    return f"{raw[:44].rstrip('-')}-{identity_hash}"


def lane_task_queue(logical_queue: str, release_hash: str) -> str:
    """Derive the inactive queue polled only by one immutable lane release."""

    queue = logical_queue.strip()
    if not queue:
        raise ApplicationReleaseError("logical task queue must be non-empty")
    digest = release_hash.removeprefix("sha256:")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ApplicationReleaseError("release hash must be sha256:<64 lowercase hex>")
    return f"{queue}-r{digest[:12]}"


def build_lane_deployment_config(
    *,
    chart: str,
    namespace: str,
    temporal_address: str,
    temporal_namespace: str,
    worker_context_factory: str,
    worker_application: Optional[str] = None,
    worker_runtime_declarations_hash: Optional[str] = None,
    worker_service_account: Optional[str],
    worker_priority_class: Optional[str],
    payload_encryption_secret: str,
    worker_environment: Mapping[str, str],
    worker_secret_environment: Mapping[str, Mapping[str, str]],
    lanes: Sequence[str],
    queue_by_lane: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    """Build the non-secret environment config pinned into a release hash."""

    _validate_worker_application(
        worker_application,
        worker_runtime_declarations_hash,
    )
    _validate_kubernetes_object_name(
        payload_encryption_secret,
        field="payload_encryption_secret",
    )
    if worker_priority_class is not None:
        _validate_kubernetes_object_name(
            worker_priority_class,
            field="worker_priority_class",
        )

    lane_names = tuple(sorted(set(lanes)))
    if not lane_names:
        raise ApplicationReleaseError("deployment config requires at least one lane")
    queue_by_lane = queue_by_lane or {}
    unknown = sorted(set(queue_by_lane) - set(lane_names))
    if unknown:
        raise ApplicationReleaseError(
            "queue mapping references unknown lanes: " + ", ".join(unknown)
        )
    environment_names = set(worker_environment)
    secret_environment_names = set(worker_secret_environment)
    invalid_names = sorted(
        name
        for name in environment_names | secret_environment_names
        if _ENV_NAME.fullmatch(name) is None
    )
    if invalid_names:
        raise ApplicationReleaseError(
            "worker environment contains invalid names: " + ", ".join(invalid_names)
        )
    reserved_names = sorted(
        (environment_names | secret_environment_names) & _RESERVED_WORKER_ENVIRONMENT
    )
    if reserved_names:
        raise ApplicationReleaseError(
            "worker environment cannot override release-owned settings: "
            + ", ".join(reserved_names)
        )
    duplicate_names = sorted(environment_names & secret_environment_names)
    if duplicate_names:
        raise ApplicationReleaseError(
            "worker environment names cannot be both plain and secret-backed: "
            + ", ".join(duplicate_names)
        )
    return {
        "chart": _chart_identity(chart),
        "kubernetesNamespace": namespace,
        "temporalAddress": temporal_address,
        "temporalNamespace": temporal_namespace,
        "workerContextFactory": worker_context_factory,
        "workerApplication": worker_application,
        "workerRuntimeDeclarationsHash": worker_runtime_declarations_hash,
        "workerServiceAccount": worker_service_account,
        "workerMaxConcurrentActivities": _WORKER_MAX_CONCURRENT_ACTIVITIES,
        "workerPriorityClassName": worker_priority_class,
        "payloadEncryption": {
            "enabled": True,
            "required": True,
            "secretName": payload_encryption_secret,
            "keyringKey": _PAYLOAD_KEYRING_KEY,
            "activeKeyIdKey": _PAYLOAD_ACTIVE_KEY_ID_KEY,
        },
        "workerEnvironment": dict(sorted(worker_environment.items())),
        "workerSecretEnvironment": {
            name: dict(sorted(source.items()))
            for name, source in sorted(worker_secret_environment.items())
        },
        "queues": {lane: queue_by_lane.get(lane, lane) for lane in lane_names},
    }


def _validate_kubernetes_object_name(value: str, *, field: str) -> None:
    if (
        not value
        or len(value) > _K8S_DNS_SUBDOMAIN_MAX_LENGTH
        or _K8S_DNS_SUBDOMAIN.fullmatch(value) is None
    ):
        raise ApplicationReleaseError(
            f"{field} must be a valid Kubernetes DNS-subdomain name"
        )


def _validate_worker_application(
    application: Optional[str],
    declarations_hash: Optional[str],
) -> None:
    if (application is None) != (declarations_hash is None):
        raise ApplicationReleaseError(
            "worker_application and worker_runtime_declarations_hash must be set together"
        )
    if application is None:
        return
    module_name, separator, attr_path = application.partition(":")
    if not separator or not module_name or not attr_path:
        raise ApplicationReleaseError(
            "worker_application must use the explicit 'module:attribute' form"
        )
    assert declarations_hash is not None
    if re.fullmatch(r"sha256:[0-9a-f]{64}", declarations_hash) is None:
        raise ApplicationReleaseError(
            "worker_runtime_declarations_hash must be sha256:<64 lowercase hex>"
        )


def deployment_config_hash(config: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(canonical_json(config).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _deployment_queue(config: Mapping[str, Any], lane: str) -> str:
    queues = config.get("queues")
    if not isinstance(queues, Mapping):
        raise ApplicationReleaseError("release deployment config has no queue mapping")
    value = queues.get(lane)
    if not isinstance(value, str) or not value.strip():
        raise ApplicationReleaseError(
            f"release deployment config has no logical queue for lane {lane!r}"
        )
    return value


def _chart_identity(chart: str) -> str:
    path = Path(chart)
    if path.is_file():
        digest = hashlib.sha256()
        digest.update(b"file\0")
        digest.update(path.read_bytes())
        return "sha256:" + digest.hexdigest()
    if not path.is_dir():
        if _OCI_CHART_DIGEST.fullmatch(chart):
            return "oci:" + chart.rsplit("@", 1)[1]
        raise ApplicationReleaseError(
            "helm chart must be an existing local directory/file or an OCI "
            "reference pinned with @sha256:<64 lowercase hex>"
        )
    digest = hashlib.sha256()
    digest.update(b"directory\0")
    for entry in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(entry.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _run_command(args: Sequence[str]) -> None:
    proc = subprocess.run(list(args), capture_output=True, text=True)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown Helm failure"
        raise ApplicationReleaseError(detail)


def release_from_bytes(data: bytes) -> ApplicationRelease:
    """Parse and validate a release manifest loaded from a CAS."""

    raw = json.loads(data)
    if not isinstance(raw, dict):
        raise ApplicationReleaseError("release manifest must be a JSON object")
    schema_version = raw.get("schemaVersion")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != _RELEASE_SCHEMA_VERSION
    ):
        raise _release_schema_error(schema_version)
    pipeline_values = raw.get("pipelines")
    if not isinstance(pipeline_values, list):
        raise ApplicationReleaseError("release manifest pipelines must be a list")
    pipelines: list[PipelineRelease] = []
    for value in pipeline_values:
        if not isinstance(value, dict):
            raise ApplicationReleaseError("release pipeline must be a JSON object")
        bundle_ref = value.get("bundleRef")
        runtime_declarations_ref = value.get("runtimeDeclarationsRef")
        pipelines.append(
            PipelineRelease(
                name=str(value["name"]),
                lane=str(value["lane"]),
                artifact_hash=str(value["artifactHash"]),
                flow_json=dict(value["flowJson"]),
                manifest_json=dict(value["manifestJson"]),
                pinned_pures={str(k): str(v) for k, v in dict(value["pinnedPures"]).items()},
                bundle_ref=(
                    [{str(k): str(v) for k, v in dict(item).items()} for item in bundle_ref]
                    if isinstance(bundle_ref, list)
                    else None
                ),
                eval_packages=tuple(str(item) for item in value.get("evalPackages", [])),
                runtime_declarations_ref=(
                    dict(runtime_declarations_ref)
                    if isinstance(runtime_declarations_ref, dict)
                    else runtime_declarations_ref
                ),
                max_call_limits={
                    str(k): int(v) for k, v in dict(value.get("maxCallLimits", {})).items()
                },
            )
        )
    return ApplicationRelease(
        application=str(raw["application"]),
        application_artifact_hash=str(raw["applicationArtifactHash"]),
        worker_image=str(raw["workerImage"]),
        pipelines=tuple(pipelines),
        deployment_config=(
            dict(raw["deployment"]) if isinstance(raw.get("deployment"), dict) else {}
        ),
        schema_version=_RELEASE_SCHEMA_VERSION,
    )


__all__ = [
    "ApplicationPlan",
    "ApplicationRelease",
    "ApplicationReleaseError",
    "HelmLaneReconciler",
    "LaneApplyResult",
    "LaneObservation",
    "LaneReconciler",
    "ObservedApplicationState",
    "PipelineRelease",
    "build_lane_deployment_config",
    "deployment_config_hash",
    "lane_release_name",
    "lane_task_queue",
    "plan_application",
    "publish_application",
    "reconcile_application",
    "release_from_bytes",
]
