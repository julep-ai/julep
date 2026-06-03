"""Deploy-time compilation (blueprint §5/§6/§9): freeze, check, and package a flow.

:func:`deploy` is the one call that turns an authored flow into a runnable,
hash-addressed artifact, running every static gate in order:

1. **Freeze** (§ tool manifest): snapshot every MCP/native tool to a content
   hash and bind each ``call`` to it, so the tool set can never shift under a
   running flow. Capability contract assertions (§9) feed in here as overrides —
   the only way a non-read tool becomes legal inside a race.
2. **Validate** (well-formedness): per-op structure, schema edges, and the
   whole-session degrade warning for ``par``.
3. **Capability enforcement** (§9): the flow may only use granted tools, brains,
   memory scopes and servers; ungranted use is blocking.
4. **Race admission** (§5): every branch of a ``race``/``hedge``/``quorum`` must
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

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .capabilities import CapabilityManifest
from .contracts import ToolManifest, manifest_to_json
from .derived import check_race_admission
from .errors import ValidationError
from .freeze import (
    CapabilityOverrides,
    FreezeResult,
    McpServerSnapshot,
    McpSnapshot,
    McpToolSpec,
    freeze,
)
from .ir import Node
from .contracts import McpAnnotations
from .validate import Diagnostic, blocking, validate


def _merge_overrides(*overrides: Optional[CapabilityOverrides]) -> CapabilityOverrides:
    merged: dict[str, Any] = {}
    for ov in overrides:
        if ov is not None:
            merged.update(ov.contracts)
    return CapabilityOverrides(contracts=merged)


def snapshot_from_listings(
    listings: dict[str, dict[str, Any]],
    *,
    versions: Optional[dict[str, str]] = None,
) -> McpSnapshot:
    """Build an :class:`McpSnapshot` from plain tool listings (MCP-SDK seam).

    ``listings`` maps ``server -> {tool_name -> {"inputSchema": ..., "annotations": {...}}}``,
    exactly the shape an MCP ``tools/list`` response flattens to. This is the
    integration point where a concrete MCP client plugs in: gather each server's
    tools, hand them here, and the result is a frozen-ready snapshot. ``versions``
    optionally pins a server version into the content hash.
    """
    versions = versions or {}
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
                    destructive_hint=ann_raw.get("destructiveHint", ann_raw.get("destructive_hint")),
                    open_world_hint=ann_raw.get("openWorldHint", ann_raw.get("open_world_hint")),
                ),
            )
        servers[server] = McpServerSnapshot(
            server=server, version=versions.get(server, "1"), tools=tool_specs
        )
    return McpSnapshot(servers=servers)


@dataclass
class Deployment:
    """A compiled, frozen flow ready to run, with its compile diagnostics."""

    flow: Node
    manifest: ToolManifest
    diagnostics: list[Diagnostic] = field(default_factory=list)
    capabilities: Optional[CapabilityManifest] = None
    freeze_timing: str = "deploy_time"
    # Retained only for freeze_timing == "per_run": a source of fresh snapshots
    # and the overrides to re-apply, so each launch can re-freeze.
    _snapshot_source: Optional[Callable[[], McpSnapshot]] = None
    _overrides: CapabilityOverrides = field(default_factory=CapabilityOverrides)

    @property
    def flow_json(self) -> dict[str, Any]:
        return self.flow.to_json()

    @property
    def manifest_json(self) -> dict[str, Any]:
        return manifest_to_json(self.manifest)

    @property
    def warnings(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity != "error"]

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
        return deploy(
            self.flow,
            snap,
            capabilities=self.capabilities,
            extra_overrides=self._overrides,
            freeze_timing=self.freeze_timing,
            snapshot_source=self._snapshot_source,
            strict=True,
        )

    async def run(self, client, *, session_id: str, input: Any = None,
                  task_queue: str = "composable-agents", policy: Any = None) -> Any:
        """Run this deployment on Temporal and await the result.

        Imports the execution layer lazily so offline compilation never requires
        ``temporalio``. For the per-run freeze seam, callers that want a fresh
        snapshot each launch should ``deployment.refresh(...).run(...)``.
        """
        from .execution.harness import run_flow  # lazy: keeps deploy import-light

        return await run_flow(
            client, self.flow_json, self.manifest_json,
            session_id=session_id, input=input, task_queue=task_queue, policy=policy,
        )


def deploy(
    flow: Node,
    snapshot: McpSnapshot,
    *,
    capabilities: Optional[CapabilityManifest] = None,
    extra_overrides: Optional[CapabilityOverrides] = None,
    strict: bool = True,
    freeze_timing: str = "deploy_time",
    snapshot_source: Optional[Callable[[], McpSnapshot]] = None,
) -> Deployment:
    """Compile ``flow`` against ``snapshot`` into a runnable :class:`Deployment`.

    Runs freeze -> validate -> capability enforcement -> race admission. With
    ``strict`` (default), any blocking diagnostic raises
    :class:`~composable_agents.errors.ValidationError`; otherwise all diagnostics
    are returned on the deployment for the caller to triage.

    ``capabilities`` (a §9 manifest) both supplies contract-assertion overrides
    (so asserted-idempotent tools may appear in races) and constrains which
    tools/brains/servers the flow may use. ``extra_overrides`` merges additional
    assertions on top. ``freeze_timing`` selects the §6 seam; pass
    ``snapshot_source`` for the per-run case so :meth:`Deployment.refresh` can
    re-freeze without an explicit snapshot.
    """
    if freeze_timing not in ("deploy_time", "per_run"):
        raise ValueError("freeze_timing must be 'deploy_time' or 'per_run'")

    cap_overrides = capabilities.overrides() if capabilities is not None else None
    overrides = _merge_overrides(cap_overrides, extra_overrides)

    # 1. Freeze (raises FreezeError on cycle / unresolved tool).
    fr: FreezeResult = freeze(flow, snapshot, overrides)

    diagnostics: list[Diagnostic] = []
    # 2. Well-formedness + schema edges.
    diagnostics.extend(validate(fr.flow, fr.manifest))
    # 3. Capability enforcement (§9): granted tools/brains/servers only.
    if capabilities is not None:
        diagnostics.extend(capabilities.enforce_compile(fr.flow))
    # 4. Race admission (§5): every race branch read-only or asserted-idempotent.
    diagnostics.extend(check_race_admission(fr.flow, fr.manifest))

    if strict:
        bad = blocking(diagnostics)
        if bad:
            raise ValidationError(bad)

    return Deployment(
        flow=fr.flow,
        manifest=fr.manifest,
        diagnostics=diagnostics,
        capabilities=capabilities,
        freeze_timing=freeze_timing,
        _snapshot_source=snapshot_source,
        _overrides=overrides,
    )


__all__ = ["Deployment", "deploy", "snapshot_from_listings"]
