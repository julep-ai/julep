"""freeze(): resolve the tool surface and pin it (blueprint §1.4).

This is a *pure* function: snapshot in, frozen IR + manifest out. The live
``tools/list`` calls and native-schema lookups happen in
:mod:`julep.deploy` and feed the ``snapshot`` here. Keeping freeze
pure is what lets the golden tests pin tool hashes without a network.

After freeze the flow sees a static tool surface: every ``call`` node carries a
``frozen_hash`` into a :class:`~julep.contracts.FrozenTool`, so
``surface_shape`` stays decidable, replay stays hash-checkable, and §5 race
admission has a real contract to check.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
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
    EMIT_TOOL,
    HUMAN_GATE_TOOL,
    JSONSchema,
    McpTool,
    NativeTool,
    Node,
    RECV_TOOL,
    SLEEP_TOOL,
    SourceSpan,
    ThinkStep,
    ToolRef,
    canonical_json,
    toolref_key,
)
from .kinds import Effect, Idempotency, Op
from .registry import DEFAULT_REGISTRY, ToolSchemaExpectation
from .transforms import detect_cycles, normalize_ids


# The reserved human-gate tool has a fixed contract and never needs a snapshot
# entry: it waits on a human signal (external, non-idempotent, but ours so the
# contract is asserted). It is intentionally not race-safe.
_HUMAN_GATE_CONTRACT = ToolContract(effect=Effect.EXTERNAL, idempotency=Idempotency.NONE)

# The reserved sleep tool is side-effect-free and replay-safe by construction.
_SLEEP_CONTRACT = ToolContract(effect=Effect.READ, idempotency=Idempotency.NATIVE)

_RECV_CONTRACT = ToolContract(effect=Effect.EXTERNAL, idempotency=Idempotency.NONE)
_EMIT_CONTRACT = ToolContract(effect=Effect.EXTERNAL, idempotency=Idempotency.NONE)


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
    contract: ToolContract  # we own native tools, so we declare their contract
    output_schema: Optional[JSONSchema] = None


@dataclass(frozen=True)
class McpSnapshot:
    """A frozen view of every referenced server plus our native tools."""

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

    # Reserved human-gate tool: synthetic, no snapshot lookup.
    if isinstance(ref, NativeTool) and ref.name == HUMAN_GATE_TOOL:
        return FrozenTool.create(
            ref=ref,
            input_schema={},
            contract=asserted_contract or _HUMAN_GATE_CONTRACT,
            output_schema=None,
            server_version=None,
            asserted=True,
        )

    # Reserved sleep tool: synthetic, no snapshot lookup.
    if isinstance(ref, NativeTool) and ref.name == SLEEP_TOOL:
        return FrozenTool.create(
            ref=ref,
            input_schema={},
            contract=asserted_contract or _SLEEP_CONTRACT,
            output_schema=None,
            server_version=None,
            asserted=True,
        )

    if isinstance(ref, NativeTool) and ref.name == RECV_TOOL:
        return FrozenTool.create(
            ref=ref,
            input_schema={},
            contract=asserted_contract or _RECV_CONTRACT,
            output_schema=None,
            server_version=None,
            asserted=True,
        )

    if isinstance(ref, NativeTool) and ref.name == EMIT_TOOL:
        return FrozenTool.create(
            ref=ref,
            input_schema={},
            contract=asserted_contract or _EMIT_CONTRACT,
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


# --------------------------------------------------------------------------- #
# Expected-schema verification (dotctx tools.pyi contract assertions).
# --------------------------------------------------------------------------- #
def _schema_hash(schema: JSONSchema) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(schema).encode("utf-8")).hexdigest()


def _served_input_schema(key: str, snapshot: McpSnapshot) -> Optional[JSONSchema]:
    ref = _toolref_from_key(key)
    if isinstance(ref, NativeTool):
        native_spec = snapshot.native.get(ref.name)
        return native_spec.input_schema if native_spec is not None else None
    server = snapshot.servers.get(ref.server)
    if server is None:
        return None
    mcp_spec = server.tools.get(ref.tool)
    return mcp_spec.input_schema if mcp_spec is not None else None


def _expected_tool_keys(flow: Node) -> set[str]:
    """Every toolref key the flow can reach: call leaves, app inline grants,
    and the granted tools of each registered reasoner the flow references."""
    keys: set[str] = set()
    reasoners: set[str] = set()
    for node in flow.walk():
        step = node.step
        if isinstance(step, CallStep):
            keys.add(toolref_key(step.tool))
        if isinstance(step, ThinkStep):
            reasoners.add(step.reasoner)
        if node.op in (Op.APP, Op.EVAL_PLAN) and node.controller is not None:
            reasoners.add(node.controller)
        if node.op == Op.APP and node.tools:
            keys.update(str(k) for k in node.tools)
    for name in reasoners:
        reasoner = DEFAULT_REGISTRY.reasoners.get(name)
        if reasoner is not None:
            keys.update(reasoner.tools)
    return keys


def _check_tool_schema_drift(
    flow: Node,
    snapshot: McpSnapshot,
    expectations: Mapping[str, ToolSchemaExpectation],
) -> None:
    """TOOL_SCHEMA_DRIFT: a dotctx package's expected tool schema (tools.pyi)
    must match the served schema by canonical hash when the snapshot resolves
    the tool. A prompt written against one tool contract silently running
    against another is exactly the class of bug freeze exists to stop."""
    if not expectations:
        return
    for key in sorted(_expected_tool_keys(flow)):
        expectation = expectations.get(key)
        if expectation is None:
            continue
        served = _served_input_schema(key, snapshot)
        if served is None:
            continue  # not resolved by this snapshot; missing call tools raise in _resolve
        expected_hash = _schema_hash(expectation.input_schema)
        served_hash = _schema_hash(served)
        if expected_hash != served_hash:
            ref = _toolref_from_key(key)
            server = ref.server if isinstance(ref, McpTool) else "<native>"
            raise FreezeError(
                f"TOOL_SCHEMA_DRIFT: tool {key!r} (server {server!r}) serves schema "
                f"{served_hash}, but {expectation.ctx_path!r} was written against "
                f"{expected_hash}"
            )


def freeze(
    flow: Node,
    snapshot: McpSnapshot,
    overrides: Optional[CapabilityOverrides] = None,
    *,
    expected_tool_schemas: Optional[Mapping[str, ToolSchemaExpectation]] = None,
) -> FreezeResult:
    """Bind every ToolRef in ``flow`` to a frozen, hash-addressed contract.

    Returns a *copy* of the flow that is a clean tree (cycles rejected, sharing
    removed, ids normalized to deterministic paths) with each ``call`` node's
    ``frozen_hash`` set, plus the manifest keyed by hash. Raises
    :class:`FreezeError` if the flow has a cycle, any tool can't be resolved, or
    a served tool schema drifts from a recorded dotctx expectation
    (``expected_tool_schemas``; defaults to the registry's recorded ones).
    """
    overrides = overrides or CapabilityOverrides()
    expectations: Mapping[str, ToolSchemaExpectation] = (
        expected_tool_schemas
        if expected_tool_schemas is not None
        else DEFAULT_REGISTRY.tool_expectations
    )

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

    # 6. Verify recorded dotctx tool-schema expectations against the snapshot.
    _check_tool_schema_drift(frozen_flow, snapshot, expectations)

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
