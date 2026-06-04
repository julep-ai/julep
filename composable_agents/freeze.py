"""freeze(): resolve the tool surface and pin it (blueprint §1.4).

This is a *pure* function: snapshot in, frozen IR + manifest out. The live
``tools/list`` calls and native-schema lookups happen in
:mod:`composable_agents.deploy` and feed the ``snapshot`` here. Keeping freeze
pure is what lets the golden tests pin tool hashes without a network.

After freeze the flow sees a static tool surface: every ``call`` node carries a
``frozen_hash`` into a :class:`~composable_agents.contracts.FrozenTool`, so
``surface_shape`` stays decidable, replay stays hash-checkable, and §5 race
admission has a real contract to check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .contracts import (
    FrozenTool,
    McpAnnotations,
    ToolContract,
    ToolManifest,
    contract_from_annotations,
)
from .errors import FreezeError
from .ir import (
    CallStep,
    HUMAN_GATE_TOOL,
    JSONSchema,
    McpTool,
    NativeTool,
    Node,
    SourceSpan,
    ToolRef,
    toolref_key,
)
from .kinds import Effect, Idempotency, Op
from .transforms import detect_cycles, normalize_ids


# The reserved human-gate hand has a fixed contract and never needs a snapshot
# entry: it waits on a human signal (external, non-idempotent, but ours so the
# contract is asserted). It is intentionally not race-safe.
_HUMAN_GATE_CONTRACT = ToolContract(effect=Effect.EXTERNAL, idempotency=Idempotency.NONE)


# --------------------------------------------------------------------------- #
# Snapshot model (what a live tools/list + native registry resolves to).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class McpToolSpec:
    input_schema: JSONSchema
    annotations: McpAnnotations = field(default_factory=McpAnnotations)
    output_schema: Optional[JSONSchema] = None


@dataclass(frozen=True)
class McpServerSnapshot:
    server: str
    tools: dict[str, McpToolSpec]
    version: Optional[str] = None


@dataclass(frozen=True)
class NativeToolSpec:
    input_schema: JSONSchema
    contract: ToolContract  # we own native hands, so we declare their contract
    output_schema: Optional[JSONSchema] = None


@dataclass(frozen=True)
class McpSnapshot:
    """A frozen view of every referenced server plus our native hands."""

    servers: dict[str, McpServerSnapshot] = field(default_factory=dict)
    native: dict[str, NativeToolSpec] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityOverrides:
    """Contract assertions from the capability manifest (§9).

    A ToolRef key present here is treated as *asserted*: its contract is trusted
    rather than conservatively defaulted from MCP hints, which is the only way a
    non-read tool becomes legal inside a race.
    """

    contracts: dict[str, ToolContract] = field(default_factory=dict)

    def get(self, key: str) -> Optional[ToolContract]:
        return self.contracts.get(key)


@dataclass(frozen=True)
class FreezeResult:
    flow: Node
    manifest: ToolManifest
    source_map: dict[str, SourceSpan] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Resolution of a single ToolRef -> FrozenTool.
# --------------------------------------------------------------------------- #
def _resolve(
    ref: ToolRef, snapshot: McpSnapshot, overrides: CapabilityOverrides
) -> FrozenTool:
    key = toolref_key(ref)
    asserted_contract = overrides.get(key)

    # Reserved human-gate hand: synthetic, no snapshot lookup.
    if isinstance(ref, NativeTool) and ref.name == HUMAN_GATE_TOOL:
        return FrozenTool.create(
            ref=ref,
            input_schema={},
            contract=asserted_contract or _HUMAN_GATE_CONTRACT,
            output_schema=None,
            server_version=None,
            asserted=True,
        )

    if isinstance(ref, NativeTool):
        native_spec = snapshot.native.get(ref.name)
        if native_spec is None:
            raise FreezeError(f"native tool not in snapshot: {ref.name!r}")
        contract = asserted_contract or native_spec.contract
        return FrozenTool.create(
            ref=ref,
            input_schema=native_spec.input_schema,
            contract=contract,
            output_schema=native_spec.output_schema,
            server_version=None,
            asserted=True,  # native tools are ours: their contract is declared
        )

    # MCP tool.
    server = snapshot.servers.get(ref.server)
    if server is None:
        raise FreezeError(f"MCP server not in snapshot: {ref.server!r}")
    mcp_spec = server.tools.get(ref.tool)
    if mcp_spec is None:
        raise FreezeError(f"MCP tool not found: {ref.server}/{ref.tool}")

    if asserted_contract is not None:
        contract = asserted_contract
        asserted = True
    else:
        # Untrusted hints -> conservative default. Not asserted: illegal to race.
        contract = contract_from_annotations(mcp_spec.annotations)
        asserted = False

    return FrozenTool.create(
        ref=ref,
        input_schema=mcp_spec.input_schema,
        contract=contract,
        output_schema=mcp_spec.output_schema,
        server_version=server.version,
        asserted=asserted,
        annotations=mcp_spec.annotations,
    )


def _toolref_from_key(key: str) -> ToolRef:
    """Reverse of toolref_key for app inline tool grants."""
    if "/" in key:
        server, tool = key.split("/", 1)
        return McpTool(server=server, tool=tool)
    return NativeTool(name=key)


def freeze(
    flow: Node,
    snapshot: McpSnapshot,
    overrides: Optional[CapabilityOverrides] = None,
) -> FreezeResult:
    """Bind every ToolRef in ``flow`` to a frozen, hash-addressed contract.

    Returns a *copy* of the flow that is a clean tree (cycles rejected, sharing
    removed, ids normalized to deterministic paths) with each ``call`` node's
    ``frozen_hash`` set, plus the manifest keyed by hash. Raises
    :class:`FreezeError` if the flow has a cycle or any tool can't be resolved.
    """
    overrides = overrides or CapabilityOverrides()

    # 1. Reject host-language knots before to_json would recurse forever.
    cycle = detect_cycles(flow)
    if cycle is not None:
        raise FreezeError("flow has a cycle: " + " -> ".join(cycle))

    # 2. Deep-copy via canonical JSON (unshares any DAG nodes); 3. normalize ids.
    frozen_flow = normalize_ids(Node.from_json(flow.to_json()))
    authored_nodes = list(flow.walk())
    frozen_nodes = list(frozen_flow.walk())
    source_map: dict[str, SourceSpan] = {}
    if len(authored_nodes) == len(frozen_nodes):
        for authored, frozen in zip(authored_nodes, frozen_nodes, strict=True):
            if authored.source is not None:
                source_map[frozen.id] = authored.source

    # 4. Bind every call node to a frozen tool.
    manifest: ToolManifest = {}
    for node in frozen_flow.walk():
        step = node.step
        if not isinstance(step, CallStep):
            continue
        tool = _resolve(step.tool, snapshot, overrides)
        manifest[tool.hash] = tool
        step.frozen_hash = tool.hash

    # 5. Agent/app nodes name the tools their controller may call, but they are
    # not call leaves and do not receive a frozen_hash. Bind them into the
    # manifest so deployed agent loops receive the same contracts as local runs.
    for node in frozen_flow.walk():
        if node.op != Op.APP or not node.tools:
            continue
        for key in node.tools:
            tool = _resolve(_toolref_from_key(key), snapshot, overrides)
            manifest[tool.hash] = tool

    return FreezeResult(flow=frozen_flow, manifest=manifest, source_map=source_map)


def bind(node: Node, manifest: ToolManifest) -> FrozenTool:
    """Look up the FrozenTool a frozen ``call`` node was bound to."""
    step = node.step
    if not isinstance(step, CallStep) or step.frozen_hash is None:
        raise FreezeError(f"node {node.id!r} is not a frozen call step")
    try:
        return manifest[step.frozen_hash]
    except KeyError as e:
        raise FreezeError(
            f"node {node.id!r} bound to {step.frozen_hash} which is not in the manifest"
        ) from e
