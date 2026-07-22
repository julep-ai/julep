"""Deploy-time compilation (blueprint §5/§6/§9): freeze, check, and package a flow.

:func:`deploy` is the one call that turns an authored flow into a runnable,
hash-addressed artifact, running every static gate in order:

1. **Freeze** (§ tool manifest): snapshot every MCP/native tool to a content
   hash and bind each ``call`` to it, so the tool set can never shift under a
   running flow. Capability contract assertions (§9) feed in here as overrides —
   the only way a non-read tool becomes legal inside a race.
2. **Validate** (well-formedness): per-op structure, schema edges, and the
   whole-session degrade warning for ``par``.
3. **Capability enforcement** (§9): the flow may only use granted tools, reasoners,
   memory scopes and servers; ungranted use is blocking.
4. **Approval gates** (§7.3): dangerous or grant-approved tools must be dominated
   by a human gate.
5. **Race admission** (§5): every branch of a ``race``/``hedge``/``quorum`` must
   be read-only or contract-asserted idempotent, so a duplicated branch can do
   no harm.

Blocking diagnostics from any stage abort the deploy (with ``strict``, the
default); the diagnostics are always returned on the :class:`Deployment` for
inspection.

The §6 *freeze-timing* seam is surfaced explicitly via ``freeze_timing``:
``"deploy_time"`` (default) freezes once and reuses the artifact for every run —
maximal determinism; ``"per_run"`` keeps a snapshot source so each launch can
re-freeze against a fresh tool snapshot — necessary when tool definitions may
drift between deploys. :meth:`Deployment.refresh` re-runs the pipeline against a
new snapshot for the per-run case.

The Temporal workflow *types* are fixed (one :class:`FlowWorkflow`, one
:class:`AgentWorkflow`), so "registration" is not code generation: a deployment
is the frozen IR + manifest plus the run helpers. The execution-layer imports
are guarded so this module is usable for offline compilation without Temporal.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import timedelta
from functools import cached_property
from typing import TYPE_CHECKING, Any, Callable, Mapping, Optional, Sequence

from . import __version__
from .capabilities import CapabilityManifest, check_approval_gates
from .contracts import McpAnnotations, ToolManifest, manifest_to_json
from .derived import check_race_admission
from .dotctx import Reasoner, get_reasoner
from .errors import ValidationError
from .freeze import (
    CapabilityOverrides,
    FreezeResult,
    McpServerSnapshot,
    McpSnapshot,
    McpToolSpec,
    freeze,
)
from .ir import McpTool, Node, ThinkStep, canonical_json, toolref_key
from .kinds import EnforcementMode, Op, Shape
from .purity import is_registered, source_hash_of
from .registry import DEFAULT_REGISTRY
from .shapes import surface_shape as _compute_surface_shape
from .validate import Diagnostic, blocking, validate

if TYPE_CHECKING:
    from .agent import Tool
    from .artifact_store import ArtifactStore
    from .execution.effects import McpCaller
    from .execution.interpreter import Result as InterpreterResult
    from .typed import FlowLike


def _merge_overrides(*overrides: Optional[CapabilityOverrides]) -> CapabilityOverrides:
    merged: dict[str, Any] = {}
    provenance: dict[str, str] = {}
    for ov in overrides:
        if ov is not None:
            for key, contract in ov.contracts.items():
                merged[key] = contract
                source = ov.provenance_for(key)
                if source is not None:
                    provenance[key] = source
    return CapabilityOverrides(contracts=merged, provenance=provenance)


def snapshot_from_listings(
    listings: dict[str, dict[str, Any]],
    *,
    versions: Optional[dict[str, str]] = None,
    protocol_versions: Optional[dict[str, str]] = None,
    server_versions: Optional[dict[str, str]] = None,
) -> McpSnapshot:
    """Build an :class:`McpSnapshot` from plain tool listings (MCP-SDK seam).

    ``listings`` maps ``server -> {tool_name -> {"inputSchema": ..., "annotations": {...}}}``,
    exactly the shape an MCP ``tools/list`` response flattens to. This is the
    integration point where a concrete MCP client plugs in: gather each server's
    tools, tool them here, and the result is a frozen-ready snapshot. ``versions``
    optionally pins a server version into the content hash.
    """
    versions = versions or {}
    protocol_versions = protocol_versions or {}
    server_versions = server_versions or {}
    servers: dict[str, McpServerSnapshot] = {}
    for server, tools in listings.items():
        tool_specs: dict[str, McpToolSpec] = {}
        for tool, spec in tools.items():
            ann_raw = spec.get("annotations") or {}
            tool_specs[tool] = McpToolSpec(
                input_schema=spec.get("inputSchema", spec.get("input_schema", {})),
                annotations=McpAnnotations(
                    read_only_hint=ann_raw.get("readOnlyHint", ann_raw.get("read_only_hint")),
                    idempotent_hint=ann_raw.get("idempotentHint", ann_raw.get("idempotent_hint")),
                    destructive_hint=ann_raw.get(
                        "destructiveHint", ann_raw.get("destructive_hint")
                    ),
                    open_world_hint=ann_raw.get("openWorldHint", ann_raw.get("open_world_hint")),
                ),
                output_schema=spec.get("outputSchema", spec.get("output_schema")),
            )
        version = versions.get(server, "1")
        protocol_version = protocol_versions.get(server)
        server_version = server_versions.get(server)
        # Live snapshots historically represented both values as one canonical
        # JSON string.  Decode that wire form while continuing to accept old
        # author-managed snapshots whose version is just an opaque string.
        if protocol_version is None or server_version is None:
            try:
                parsed_version = json.loads(version)
            except (TypeError, ValueError):
                parsed_version = None
            if isinstance(parsed_version, dict):
                protocol_raw = parsed_version.get("protocol")
                server_raw = parsed_version.get("server")
                if protocol_version is None and isinstance(protocol_raw, str):
                    protocol_version = protocol_raw
                if server_version is None and isinstance(server_raw, str):
                    server_version = server_raw
        servers[server] = McpServerSnapshot(
            server=server,
            version=version,
            protocol_version=protocol_version,
            server_version=server_version,
            tools=tool_specs,
        )
    return McpSnapshot(servers=servers)


def _referenced_pures(flow: Node) -> list[str]:
    names: set[str] = set()
    for node in flow.walk():
        if node.pure is not None:
            names.add(node.pure)
        if node.round_note is not None:
            names.add(node.round_note)
        if node.op == Op.ALT and node.select is not None:
            names.add(node.select)
        if node.merge is not None and node.merge.reducer is not None:
            names.add(node.merge.reducer)
    return sorted(names)


def _pure_source_hashes(flow: Node) -> dict[str, str | None]:
    return {
        name: source_hash_of(name) if is_registered(name) else None
        for name in _referenced_pures(flow)
    }


def _renderer_source_hashes(flow: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in _referenced_reasoners(flow):
        try:
            reasoner = get_reasoner(name)
        except KeyError:
            continue
        for render_name in (reasoner.system_render, reasoner.user_render):
            if render_name is None:
                continue
            if render_name not in DEFAULT_REGISTRY.renderers:
                raise ValueError(f"reasoner {name!r} references unknown renderer {render_name!r}")
            out[render_name] = DEFAULT_REGISTRY.renderer_source_hash_of(render_name)
    return out


def _referenced_reasoners(flow: Node) -> list[str]:
    names: set[str] = set()
    for node in flow.walk():
        step = node.step
        if isinstance(step, ThinkStep):
            names.add(step.reasoner)
        if node.op in (Op.APP, Op.EVAL_PLAN) and node.controller is not None:
            names.add(node.controller)
        if node.summarizer is not None:
            names.add(node.summarizer)
    return sorted(names)


def _reasoner_identity(name: str) -> dict[str, Any]:
    try:
        reasoner: Reasoner = get_reasoner(name)
    except KeyError:
        return {"name": name}
    ident: dict[str, Any] = {
        "name": reasoner.name,
        "model": reasoner.model,
        "system": reasoner.system,
        "replySchema": reasoner.reply_schema,
        "tools": list(reasoner.tools),
    }
    # New fields enter only when set, so pre-existing artifacts hash identically.
    if reasoner.system_render is not None:
        ident["systemRender"] = reasoner.system_render
    if reasoner.user_render is not None:
        ident["userRender"] = reasoner.user_render
    if reasoner.max_tokens is not None:
        ident["maxTokens"] = reasoner.max_tokens
    if reasoner.reasoning_effort is not None:
        ident["reasoningEffort"] = reasoner.reasoning_effort
    if reasoner.output_retries:
        ident["outputRetries"] = reasoner.output_retries
    if reasoner.require_tool_call:
        ident["requireToolCall"] = True
    if reasoner.response_format is not None:
        ident["responseFormat"] = reasoner.response_format
    if reasoner.prompt_cache is not None:
        ident["promptCache"] = reasoner.prompt_cache
    return ident


def _framework_version() -> str:
    import julep as package

    return getattr(package, "__version__", __version__)


def _hash_artifact_components(components: dict[str, Any]) -> str:
    payload = canonical_json(components)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _capabilities_from_tools(
    tools: Sequence[Tool[Any, Any]],
    reasoners: Optional[Sequence[str]],
) -> CapabilityManifest:
    data: dict[str, Any] = {
        "tools": [
            {
                "name": native_tool.name,
                "effect": native_tool.contract.effect.value,
                "idempotency": native_tool.contract.idempotency.value,
            }
            for native_tool in tools
        ]
    }
    if reasoners is not None:
        data["reasoners"] = list(reasoners)
    return CapabilityManifest.from_dict(data)


def _capabilities_from_resolved_manifest(
    manifest: ToolManifest,
    reasoners: Sequence[str],
) -> CapabilityManifest:
    grants = {
        toolref_key(tool.ref): {
            "name": toolref_key(tool.ref),
            "effect": tool.contract.effect.value,
            "idempotency": tool.contract.idempotency.value,
        }
        for tool in manifest.values()
    }
    return CapabilityManifest.from_dict(
        {
            "tools": [grants[name] for name in sorted(grants)],
            "reasoners": list(reasoners),
        }
    )


def _configured_mcp_urls(servers: Mapping[str, Any]) -> frozenset[str]:
    urls: set[str] = set()
    for server, raw in servers.items():
        url: object
        if isinstance(raw, str):
            url = raw
        elif isinstance(raw, Mapping):
            url = raw.get("url")
        else:
            url = getattr(raw, "url", None)
        if not isinstance(url, str):
            raise ValueError(f"MCP server {server!r} requires a URL")
        urls.add(url)
    return frozenset(urls)


_ID_REUSE_POLICIES = {
    "allow_duplicate": "ALLOW_DUPLICATE",
    "allow_duplicate_failed_only": "ALLOW_DUPLICATE_FAILED_ONLY",
    "reject_duplicate": "REJECT_DUPLICATE",
    "terminate_if_running": "TERMINATE_IF_RUNNING",
}
_ID_CONFLICT_POLICIES = {
    "unspecified": "UNSPECIFIED",
    "fail": "FAIL",
    "use_existing": "USE_EXISTING",
    "terminate_existing": "TERMINATE_EXISTING",
}


@dataclass(frozen=True)
class WorkflowStartOptions:
    """Explicit Temporal options for a non-blocking deployment start.

    The defaults implement an idempotent producer: an already-running workflow
    returns its existing handle, a successful terminal workflow is accepted
    without being rerun, and only a failed terminal workflow may start again
    with the same ID.
    """

    workflow_id_reuse_policy: str = "allow_duplicate_failed_only"
    workflow_id_conflict_policy: str = "use_existing"
    execution_timeout: Optional[timedelta] = None
    search_attributes: Optional[Mapping[str, Any]] = None
    trace_headers: Optional[Mapping[str, str | bytes]] = None
    task_queue: Optional[str] = None
    require_payload_encryption: bool = True

    def __post_init__(self) -> None:
        if self.workflow_id_reuse_policy not in _ID_REUSE_POLICIES:
            raise ValueError(
                "workflow_id_reuse_policy must be one of " + ", ".join(sorted(_ID_REUSE_POLICIES))
            )
        if self.workflow_id_conflict_policy not in _ID_CONFLICT_POLICIES:
            raise ValueError(
                "workflow_id_conflict_policy must be one of "
                + ", ".join(sorted(_ID_CONFLICT_POLICIES))
            )
        if self.execution_timeout is not None and self.execution_timeout <= timedelta(0):
            raise ValueError("execution_timeout must be positive")
        if self.task_queue is not None and not self.task_queue.strip():
            raise ValueError("task_queue must be non-empty when provided")

    def temporal_kwargs(self) -> dict[str, Any]:
        """Materialize SDK enums lazily so compilation stays Temporal-optional."""

        try:
            from temporalio.common import (
                TypedSearchAttributes,
                WorkflowIDConflictPolicy,
                WorkflowIDReusePolicy,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Temporal support is not installed; install it with pip install 'julep[temporal]'"
            ) from exc

        kwargs: dict[str, Any] = {
            "id_reuse_policy": getattr(
                WorkflowIDReusePolicy,
                _ID_REUSE_POLICIES[self.workflow_id_reuse_policy],
            ),
            "id_conflict_policy": getattr(
                WorkflowIDConflictPolicy,
                _ID_CONFLICT_POLICIES[self.workflow_id_conflict_policy],
            ),
        }
        if self.execution_timeout is not None:
            kwargs["execution_timeout"] = self.execution_timeout
        if self.search_attributes is not None:
            if isinstance(self.search_attributes, TypedSearchAttributes):
                kwargs["search_attributes"] = self.search_attributes
            elif isinstance(self.search_attributes, Mapping):
                normalized: dict[str, list[Any]] = {}
                for name, value in self.search_attributes.items():
                    if not isinstance(name, str) or not name.strip():
                        raise ValueError("search attribute names must be non-empty strings")
                    values = list(value) if isinstance(value, (list, tuple)) else [value]
                    if not values:
                        raise ValueError(
                            f"search attribute {name!r} must contain at least one value"
                        )
                    normalized[name] = values
                kwargs["search_attributes"] = normalized
            else:
                raise TypeError("search_attributes must be a mapping or TypedSearchAttributes")
        return kwargs


async def _start_temporal_workflow(
    client: Any,
    *,
    session_id: str,
    options: WorkflowStartOptions,
    starter: Callable[[], Any],
) -> Any:
    """Start with durable trace headers and duplicate-as-accepted semantics."""

    from .execution.trace_headers import (
        require_trace_headers_interceptor,
        workflow_trace_headers,
    )

    if options.trace_headers:
        require_trace_headers_interceptor(client)
    config_method = getattr(client, "config", None)
    if options.require_payload_encryption:
        from .execution.codec import data_converter_uses_aes_gcm

        if not callable(config_method):
            raise ValueError(
                "payload encryption requires a verifiable Temporal client with config()"
            )
        config = config_method(active_config=True)
        converter = config.get("data_converter") if isinstance(config, dict) else None
        if not data_converter_uses_aes_gcm(converter):
            raise ValueError(
                "Temporal starts require the AES-256-GCM data converter; set "
                "require_payload_encryption=False only for local development"
            )
    with workflow_trace_headers(options.trace_headers):
        try:
            return await starter()
        except Exception as exc:
            try:
                from temporalio.exceptions import WorkflowAlreadyStartedError
            except ImportError:
                raise
            if not isinstance(exc, WorkflowAlreadyStartedError):
                raise
            if (
                options.workflow_id_reuse_policy != "allow_duplicate_failed_only"
                or options.workflow_id_conflict_policy != "use_existing"
            ):
                raise
            get_handle = getattr(client, "get_workflow_handle", None)
            if not callable(get_handle):
                raise
            return get_handle(session_id)


@dataclass
class Deployment:
    """A compiled, frozen flow ready to run, with its compile diagnostics."""

    flow: Node
    manifest: ToolManifest
    diagnostics: list[Diagnostic] = field(default_factory=list)
    capabilities: Optional[CapabilityManifest] = None
    mode: EnforcementMode = EnforcementMode.STRICT
    freeze_timing: str = "deploy_time"
    # Retained only for freeze_timing == "per_run": a source of fresh snapshots
    # and the overrides to re-apply, so each launch can re-freeze.
    _snapshot_source: Optional[Callable[[], McpSnapshot]] = None
    _overrides: CapabilityOverrides = field(default_factory=CapabilityOverrides)
    _tools: Optional[Sequence[Tool[Any, Any]]] = None
    _capabilities_from_resolved_manifest: bool = False
    bundle_ref: Optional[list[dict[str, str]]] = None
    queue: Optional[str] = None

    def __post_init__(self) -> None:
        # Capture the compile boundary immediately. Runtime/publish paths verify
        # the live object against this canonical snapshot before using it.
        _ = self.artifact_hash

    @property
    def flow_json(self) -> dict[str, Any]:
        return self.flow.to_json()

    @property
    def manifest_json(self) -> dict[str, Any]:
        return manifest_to_json(self.manifest)

    @cached_property
    def artifact_components(self) -> dict[str, Any]:
        return self._build_artifact_components()

    def _build_artifact_components(self) -> dict[str, Any]:
        capabilities_json = self.capabilities.to_json() if self.capabilities is not None else None
        components = {
            "flowJson": self.flow_json,
            "manifestJson": self.manifest_json,
            "pureSourceHashes": _pure_source_hashes(self.flow),
            "reasoners": {
                name: _reasoner_identity(name) for name in _referenced_reasoners(self.flow)
            },
            "capabilities": capabilities_json,
            "executionPolicy": None,
            "frameworkVersion": _framework_version(),
        }
        renderer_hashes = _renderer_source_hashes(self.flow)
        if renderer_hashes:
            components["rendererSourceHashes"] = renderer_hashes
        return components

    def assert_artifact_integrity(self) -> None:
        """Reject mutation after the deployment's compile boundary."""

        frozen = self.artifact_components
        # Registry identities are compile-time pins. Re-reading process-global
        # registries here would make integrity depend on unrelated registration
        # order and would pre-empt worker-side pure drift verification. Recompute
        # only state owned by this Deployment object; a referenced identity change
        # in the flow itself is already visible in ``flowJson``. Bundle publishing
        # separately validates pinned pure sources before writing artifacts.
        current = dict(frozen)
        current["flowJson"] = self.flow_json
        current["manifestJson"] = self.manifest_json
        current["capabilities"] = (
            self.capabilities.to_json() if self.capabilities is not None else None
        )

        if canonical_json(current) != canonical_json(frozen):
            raise ValueError(
                "deployment flow, manifest, or capabilities changed after "
                "compilation; compile a new Deployment"
            )

    @cached_property
    def artifact_hash(self) -> str:
        return _hash_artifact_components(self.artifact_components)

    def artifact_components_with_refs(
        self, pure_runtime_refs: Optional[dict[str, dict[str, str]]]
    ) -> dict[str, Any]:
        """Return the published envelope when runtime refs are present.

        The cached base envelope is what a bundle manifest pins as
        ``artifactHash``. Runtime refs are joined only for the published
        identity and are absent when unset.
        """
        if not pure_runtime_refs:
            return self.artifact_components
        components = dict(self.artifact_components)
        components["pureRuntimeRefs"] = pure_runtime_refs
        return components

    def artifact_hash_with_refs(
        self, pure_runtime_refs: Optional[dict[str, dict[str, str]]]
    ) -> str:
        """Hash the published envelope derived from runtime refs.

        The base ``artifact_hash`` remains the refs-absent program identity; this
        hash is the refs-present identity after a bundle manifest exists.
        """
        return _hash_artifact_components(self.artifact_components_with_refs(pure_runtime_refs))

    def publish(
        self,
        store_or_url: "ArtifactStore | str",
        *,
        signing_key: str | None = None,
    ) -> dict[str, Any]:
        """Publish this deployment's artifact-store bundle and detached signature."""
        from .bundle import publish_bundle
        from .artifact_store import LocalDirArtifactStore, artifact_store_from_url
        from .gc import Lease, LeaseStore

        self.assert_artifact_integrity()
        store = artifact_store_from_url(store_or_url) if isinstance(store_or_url, str) else store_or_url
        rec = publish_bundle(self, store, signing_key=signing_key)
        if isinstance(store, LocalDirArtifactStore):
            LeaseStore(store.root).acquire(
                Lease(
                    bundle_hash=rec["bundleHash"],
                    signature_digest=rec["signatureDigest"],
                    name=self.artifact_hash,
                )
            )
        self.bundle_ref = (
            [{"bundleHash": rec["bundleHash"], "signatureDigest": rec["signatureDigest"]}]
            if rec.get("pureRuntimeRefs")
            else None
        )
        return rec

    @property
    def warnings(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity != "error"]

    @property
    def prod_gap(self) -> list[Diagnostic]:
        return blocking(self.diagnostics)

    def prod_gap_summary(self) -> str:
        if not self.prod_gap:
            return "no prod gap"

        buckets: dict[str, int] = {}
        for diagnostic in self.prod_gap:
            bucket = _prod_gap_bucket(diagnostic.code)
            buckets[bucket] = buckets.get(bucket, 0) + 1
        parts = [f"{count} {_pluralize_bucket(bucket, count)}" for bucket, count in buckets.items()]
        return "in prod this would block: " + ", ".join(parts)

    @cached_property
    def surface_shape(self) -> Shape:
        """Where this flow sits on the shape lattice (Pipeline..Agent)."""
        return _compute_surface_shape(self.flow)

    def refresh(self, snapshot: Optional[McpSnapshot] = None) -> "Deployment":
        """Re-run the compile pipeline against a fresh snapshot (per-run seam).

        Uses the explicit ``snapshot`` if given, else the stored snapshot source.
        Returns a new :class:`Deployment`; the original is left untouched so a
        running deployment is never mutated underfoot.
        """
        snap = snapshot
        if snap is None:
            if self._snapshot_source is None:
                raise ValueError("no snapshot source retained; pass a snapshot to refresh()")
            snap = self._snapshot_source()
        refreshed = deploy(
            self.flow,
            snap,
            capabilities=(
                None if self._capabilities_from_resolved_manifest else self.capabilities
            ),
            reasoners=(
                sorted(self.capabilities.reasoners)
                if self._capabilities_from_resolved_manifest and self.capabilities is not None
                else None
            ),
            extra_overrides=self._overrides,
            freeze_timing=self.freeze_timing,
            snapshot_source=self._snapshot_source,
            strict=True,
            mode=self.mode,
            queue=self.queue,
        )
        refreshed._tools = self._tools
        return refreshed

    async def run(
        self,
        client: Any,
        *,
        session_id: str,
        input: Any = None,
        task_queue: str = "julep",
        policy: Any = None,
        principal: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Run this deployment on Temporal and await the result.

        Imports the execution layer lazily so offline compilation never requires
        ``temporalio``. For the per-run freeze seam, callers that want a fresh
        snapshot each launch should ``deployment.refresh(...).run(...)``.
        ``principal`` is the run's opaque tenant/credential reference (never a
        secret); it is workflow input, not part of the frozen artifact.
        """
        if self.mode is EnforcementMode.DEV:
            raise ValueError(
                "cannot run a dev-mode deployment on Temporal: dev mode is a local "
                "iteration aid and Deployment.run() is prod-strict. Resolve "
                "deployment.prod_gap and rebuild with deploy(..., mode='strict') "
                "(or 'prod') before deploying."
            )

        from .execution.harness import run_flow  # lazy: keeps deploy import-light

        self.assert_artifact_integrity()

        run_kwargs = {
            "session_id": session_id,
            "input": input,
            "task_queue": task_queue,
            "policy": policy,
            "pinned_pures": self.artifact_components["pureSourceHashes"],
            "max_call_limits": (
                self.capabilities.max_call_limits() if self.capabilities is not None else None
            ),
            "principal": principal,
        }
        if self.bundle_ref is not None:
            run_kwargs["bundle"] = self.bundle_ref
        return await run_flow(client, self.flow_json, self.manifest_json, **run_kwargs)

    async def start(
        self,
        client: Any,
        *,
        session_id: str,
        input: Any = None,
        options: WorkflowStartOptions,
        policy: Any = None,
        principal: Optional[dict[str, Any]] = None,
        queue_lanes: Optional[dict[str, str]] = None,
    ) -> Any:
        """Start this deployment on Temporal and return its handle immediately."""

        if self.mode is EnforcementMode.DEV:
            raise ValueError(
                "cannot start a dev-mode deployment on Temporal: resolve "
                "deployment.prod_gap and rebuild in strict mode"
            )
        from .execution.harness import start_flow

        self.assert_artifact_integrity()

        start_kwargs: dict[str, Any] = {
            "session_id": session_id,
            "input": input,
            "task_queue": options.task_queue or self.queue or "julep",
            "policy": policy,
            "pinned_pures": self.artifact_components["pureSourceHashes"],
            "max_call_limits": (
                self.capabilities.max_call_limits() if self.capabilities is not None else None
            ),
            "principal": principal,
            "queue_lanes": queue_lanes,
            "workflow_start_options": options.temporal_kwargs(),
        }
        if self.bundle_ref is not None:
            start_kwargs["bundle"] = self.bundle_ref
        return await _start_temporal_workflow(
            client,
            session_id=session_id,
            options=options,
            starter=lambda: start_flow(
                client,
                self.flow_json,
                self.manifest_json,
                **start_kwargs,
            ),
        )

    async def adry_run(
        self,
        value: Any,
        *,
        mcp_call: Optional[McpCaller] = None,
        reasoners: Optional[dict[str, Callable[[Any], Any]]] = None,
        tools: Optional[dict[str, Callable[[Any], Any]]] = None,
    ) -> "InterpreterResult":
        """Run locally with stashed native tools, an MCP caller, and fake reasoners."""
        mcp_backed = any(isinstance(tool.ref, McpTool) for tool in self.manifest.values())
        if self._tools is None and not mcp_backed:
            raise ValueError(
                "Deployment.dry_run() requires a deployment built with "
                "deploy(tools=...). Rebuild with deploy(..., tools=...) so local "
                "dry runs can bind native tool tools."
            )
        if mcp_backed and mcp_call is None and not tools:
            raise ValueError(
                "Deployment.dry_run() requires mcp_call=... for an MCP-backed deployment"
            )

        from .execution.interpreter import InMemoryEnv, interpret  # lazy: keeps deploy import-light
        from .projection import InMemoryProjection, ProjectionEmitter

        local_tools = {
            native_tool.name: native_tool.bound_tool
            for native_tool in (self._tools or ())
        }
        local_tools.update(tools or {})
        env = InMemoryEnv(
            self.manifest,
            ProjectionEmitter(InMemoryProjection()),
            tools=local_tools or None,
            mcp_call=mcp_call,
            reasoners=reasoners,
            max_calls=(
                self.capabilities.max_call_limits() if self.capabilities is not None else {}
            ),
        )
        return await interpret(self.flow, value, env)

    def dry_run(
        self,
        value: Any,
        *,
        mcp_call: Optional[McpCaller] = None,
        reasoners: Optional[dict[str, Callable[[Any], Any]]] = None,
        tools: Optional[dict[str, Callable[[Any], Any]]] = None,
    ) -> "InterpreterResult":
        """Synchronously run this deployment locally via :meth:`adry_run`."""
        return asyncio.run(
            self.adry_run(
                value,
                mcp_call=mcp_call,
                reasoners=reasoners,
                tools=tools,
            )
        )


def deploy(
    flow: Node | FlowLike[Any, Any],
    snapshot: Optional[McpSnapshot] = None,
    *,
    tools: Optional[Sequence[Tool[Any, Any]]] = None,
    mcp_servers: Optional[Mapping[str, Any]] = None,
    mcp_listings: Optional[dict[str, dict[str, Any]]] = None,
    reasoners: Optional[Sequence[str | Reasoner]] = None,
    capabilities: Optional[CapabilityManifest] = None,
    extra_overrides: Optional[CapabilityOverrides] = None,
    strict: bool = True,
    mode: EnforcementMode | str = EnforcementMode.STRICT,
    freeze_timing: str = "deploy_time",
    snapshot_source: Optional[Callable[[], McpSnapshot]] = None,
    target: str = "flow",
    queue: Optional[str] = None,
) -> Deployment:
    """Compile ``flow`` against ``snapshot`` into a runnable :class:`Deployment`.

    Runs freeze -> validate -> capability enforcement -> approval gates -> race
    admission. With ``mode="strict"`` and ``strict`` (the defaults), any blocking
    diagnostic raises :class:`~julep.errors.ValidationError`;
    ``mode="dev"`` always returns a deployment and exposes the would-block
    diagnostics through :attr:`Deployment.prod_gap`.

    ``capabilities`` (a §9 manifest) both supplies contract-assertion overrides
    (so asserted-idempotent tools may appear in races) and constrains which
    tools/reasoners/servers the flow may use. ``extra_overrides`` merges additional
    assertions on top. ``freeze_timing`` selects the §6 seam; pass
    ``snapshot_source`` for the per-run case so :meth:`Deployment.refresh` can
    re-freeze without an explicit snapshot.

    An explicit ``snapshot`` is authoritative. Without one, pass exactly one of
    ``mcp_listings``, ``mcp_servers``, or native ``tools``.
    """
    if reasoners is not None and capabilities is not None:
        raise ValueError("pass either capabilities or reasoners=, not both")
    generated_sources = (mcp_listings, mcp_servers, tools)
    if snapshot is None and sum(source is not None for source in generated_sources) != 1:
        raise ValueError(
            "pass snapshot= or exactly one generated tool source: "
            "mcp_listings=, mcp_servers=, or tools="
        )

    if not isinstance(flow, Node):
        flow = flow.to_ir()

    reasoner_names: Optional[list[str]] = None
    if reasoners is not None:
        reasoner_names = []
        for reasoner in reasoners:
            if isinstance(reasoner, Reasoner):
                DEFAULT_REGISTRY.register_reasoner(reasoner)
                reasoner_names.append(reasoner.name)
            else:
                reasoner_names.append(reasoner)

    retained_tools: Optional[Sequence[Tool[Any, Any]]] = None
    if snapshot is not None:
        pass
    elif mcp_listings is not None:
        snapshot = snapshot_from_listings(mcp_listings)
    elif mcp_servers is not None:
        from .mcp_snapshot import snapshot_servers

        allowlist = _configured_mcp_urls(mcp_servers)

        def live_snapshot() -> McpSnapshot:
            return snapshot_servers(mcp_servers, allowlist=allowlist)

        snapshot = live_snapshot()
        if snapshot_source is None:
            snapshot_source = live_snapshot
    elif tools is not None:
        from .agent import (
            snapshot_from_tools,
        )  # lazy: deploy.py must not import agent.py at module load

        snapshot = snapshot_from_tools(tools)
        retained_tools = tools
        if capabilities is None:
            capabilities = _capabilities_from_tools(tools, reasoner_names)
    assert snapshot is not None

    enforcement_mode = EnforcementMode.coerce(mode)
    if freeze_timing not in ("deploy_time", "per_run"):
        raise ValueError("freeze_timing must be 'deploy_time' or 'per_run'")

    cap_overrides = capabilities.overrides() if capabilities is not None else None
    overrides = _merge_overrides(cap_overrides, extra_overrides)

    # 1. Freeze (raises FreezeError on cycle / unresolved tool).
    fr: FreezeResult = freeze(flow, snapshot, overrides)
    derived_from_resolved_manifest = False
    if capabilities is None and any(
        isinstance(tool.ref, McpTool) for tool in fr.manifest.values()
    ):
        capabilities = _capabilities_from_resolved_manifest(
            fr.manifest,
            _referenced_reasoners(fr.flow),
        )
        derived_from_resolved_manifest = True

    diagnostics: list[Diagnostic] = []
    # 2. Well-formedness + schema edges.
    diagnostics.extend(validate(fr.flow, fr.manifest, target=target))
    # 3. Capability enforcement (§9): granted tools/reasoners/servers only.
    if capabilities is not None:
        diagnostics.extend(capabilities.enforce_compile(fr.flow, fr.manifest))
    # 4. Approval gates (§7.3): dangerous or explicitly-approved calls need a gate.
    diagnostics.extend(check_approval_gates(fr.flow, fr.manifest, capabilities))
    # 5. Race admission (§5): every race branch read-only or asserted-idempotent.
    diagnostics.extend(check_race_admission(fr.flow, fr.manifest))

    for diagnostic in diagnostics:
        source = fr.source_map.get(diagnostic.node_id)
        if source is not None:
            diagnostic.source = source

    raise_on_blocking = (enforcement_mode is EnforcementMode.STRICT) and strict
    if raise_on_blocking:
        bad = blocking(diagnostics)
        if bad:
            raise ValidationError(bad)

    deployment = Deployment(
        flow=fr.flow,
        manifest=fr.manifest,
        diagnostics=diagnostics,
        capabilities=capabilities,
        mode=enforcement_mode,
        freeze_timing=freeze_timing,
        _snapshot_source=snapshot_source,
        _overrides=overrides,
        _tools=retained_tools,
        _capabilities_from_resolved_manifest=derived_from_resolved_manifest,
        queue=queue,
    )
    from .bundle import validate_pure_deps

    validate_pure_deps(deployment, registry=DEFAULT_REGISTRY)
    _ = deployment.artifact_hash
    return deployment


def _prod_gap_bucket(code: str) -> str:
    if code.startswith("CAP_MODEL") and code.endswith("_DENIED"):
        return "ungranted reasoner/model"
    if code in {"CAP_TOOL_DENIED", "CAP_APP_TOOL_DENIED"}:
        return "ungranted tool"
    if code in {"CAP_SUBFLOW_DENIED", "CAP_APP_SUBFLOW_DENIED"}:
        return "ungranted subflow"
    if code in {"CAP_SERVER_DENIED", "CAP_MEMORY_DENIED"}:
        return "ungranted server"
    if code in {"APPROVAL_UNGATED", "CAP_APP_APPROVAL_TOOL"}:
        return "ungated dangerous/approval call"
    if code == "CAP_VERSION_PIN":
        return "version pin mismatch"
    if code.startswith("CAP_") and code.endswith("_DENIED"):
        return "ungranted tool/subflow/server"
    return "other"


def _pluralize_bucket(bucket: str, count: int) -> str:
    if count == 1:
        return bucket
    if bucket == "other":
        return "others"
    return f"{bucket}s"


__all__ = ["Deployment", "WorkflowStartOptions", "deploy", "snapshot_from_listings"]
