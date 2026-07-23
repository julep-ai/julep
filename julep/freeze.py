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
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from typing import Any, Optional

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
from .registry import (
    DEFAULT_REGISTRY,
    ToolSchemaExpectation,
    scoped_tool_expectation_key,
)
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
    # ``version`` is the legacy, combined snapshot identity.  New live
    # snapshots also persist the negotiated protocol and server versions
    # separately so releases can normalize and compare definitions exactly.
    version: Optional[str] = None
    protocol_version: Optional[str] = None
    server_version: Optional[str] = None


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
    provenance: dict[str, str] = field(default_factory=dict)
    default_provenance: str = "operator_override"

    def get(self, key: str) -> Optional[ToolContract]:
        return self.contracts.get(key)

    def provenance_for(self, key: str) -> Optional[str]:
        if key not in self.contracts:
            return None
        return self.provenance.get(key, self.default_provenance)


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
    asserted_provenance = overrides.provenance_for(key)

    # Reserved human-gate tool: synthetic, no snapshot lookup.
    if isinstance(ref, NativeTool) and ref.name == HUMAN_GATE_TOOL:
        return FrozenTool.create(
            ref=ref,
            input_schema={},
            contract=asserted_contract or _HUMAN_GATE_CONTRACT,
            output_schema=None,
            server_version=None,
            asserted=True,
            assertion_provenance=asserted_provenance or "framework_builtin",
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
            assertion_provenance=asserted_provenance or "framework_builtin",
        )

    if isinstance(ref, NativeTool) and ref.name == RECV_TOOL:
        return FrozenTool.create(
            ref=ref,
            input_schema={},
            contract=asserted_contract or _RECV_CONTRACT,
            output_schema=None,
            server_version=None,
            asserted=True,
            assertion_provenance=asserted_provenance or "framework_builtin",
        )

    if isinstance(ref, NativeTool) and ref.name == EMIT_TOOL:
        return FrozenTool.create(
            ref=ref,
            input_schema={},
            contract=asserted_contract or _EMIT_CONTRACT,
            output_schema=None,
            server_version=None,
            asserted=True,
            assertion_provenance=asserted_provenance or "framework_builtin",
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
            assertion_provenance=(
                asserted_provenance or "native_declaration"
            ),
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

    normalized_annotations = mcp_spec.annotations.normalized(server.protocol_version)

    return FrozenTool.create(
        ref=ref,
        input_schema=mcp_spec.input_schema,
        contract=contract,
        output_schema=mcp_spec.output_schema,
        server_version=server.server_version or server.version,
        asserted=asserted,
        annotations=normalized_annotations,
        protocol_version=server.protocol_version,
        assertion_provenance=asserted_provenance if asserted else None,
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


def _app_tool_expectation(
    expectations: Mapping[str, ToolSchemaExpectation],
    node: Node,
    alias: str,
    wire_key: str,
) -> Optional[ToolSchemaExpectation]:
    if node.controller is not None:
        scoped = expectations.get(scoped_tool_expectation_key(node.controller, alias))
        if scoped is not None:
            return scoped
    return expectations.get(alias) or expectations.get(wire_key)


def _reasoners_with_tool_expectations(flow: Node) -> set[str]:
    """Reasoners whose declared tools are part of this non-APP flow surface."""
    reasoners: set[str] = set()
    for node in flow.walk():
        step = node.step
        if isinstance(step, ThinkStep):
            reasoners.add(step.reasoner)
        if node.op == Op.EVAL_PLAN and node.controller is not None:
            reasoners.add(node.controller)
        # APP nodes with explicit grants are checked through their alias-to-wire
        # surface below. Retain the registered-reasoner fallback for legacy APPs
        # that carry no inline grant list.
        if node.op == Op.APP and node.controller is not None and not node.tools:
            reasoners.add(node.controller)
    return reasoners


def _direct_tool_keys(flow: Node) -> set[str]:
    return {
        toolref_key(step.tool)
        for node in flow.walk()
        if isinstance((step := node.step), CallStep)
    }


def _check_tool_schema_drift(
    flow: Node,
    snapshot: McpSnapshot,
    expectations: Mapping[str, ToolSchemaExpectation],
    *,
    scoped_fallbacks: Collection[str] = frozenset(),
) -> None:
    """TOOL_SCHEMA_DRIFT: a dotctx package's expected tool schema (tools.pyi)
    must match the served schema by canonical hash when the snapshot resolves
    the tool. A prompt written against one tool contract silently running
    against another is exactly the class of bug freeze exists to stop."""
    if not expectations:
        return
    checked: set[tuple[str, str]] = set()

    # APP aliases compare the prompt-side bare schema with the resolved wire
    # target. This is the important dotctx binding path: changing a config
    # target never changes tools.pyi, but a mismatched target fails freeze.
    for node in flow.walk():
        if node.op != Op.APP or not node.tools:
            continue
        aliases = node.tool_aliases or {}
        for raw_alias in node.tools:
            alias = str(raw_alias)
            wire_key = aliases.get(alias, alias)
            expectation = _app_tool_expectation(expectations, node, alias, wire_key)
            if expectation is None:
                continue
            checked.add((alias, wire_key))
            served = _served_input_schema(wire_key, snapshot)
            if served is None:
                continue  # APP resolution reports the stronger missing-tool error
            expected_hash = _schema_hash(expectation.input_schema)
            served_hash = _schema_hash(served)
            if expected_hash != served_hash:
                ref = _toolref_from_key(wire_key)
                server = ref.server if isinstance(ref, McpTool) else "<native>"
                raise FreezeError(
                    f"TOOL_SCHEMA_DRIFT: alias {alias!r} resolves to {wire_key!r} "
                    f"(server {server!r}) with schema {served_hash}, but "
                    f"{expectation.ctx_path!r} was written against {expected_hash}"
                )

    def check_tool(key: str, expectation: ToolSchemaExpectation) -> None:
        served = _served_input_schema(key, snapshot)
        if served is None:
            return  # not resolved by this snapshot; missing call tools raise in _resolve
        expected_hash = _schema_hash(expectation.input_schema)
        served_hash = _schema_hash(served)
        if expected_hash == served_hash:
            return
        ref = _toolref_from_key(key)
        server = ref.server if isinstance(ref, McpTool) else "<native>"
        raise FreezeError(
            f"TOOL_SCHEMA_DRIFT: tool {key!r} (server {server!r}) serves schema "
            f"{served_hash}, but {expectation.ctx_path!r} was written against "
            f"{expected_hash}"
        )

    # A scoped fallback is unsafe for an unrelated authored call, but remains
    # authoritative for the reasoner whose dotctx package registered it.
    for reasoner_name in sorted(_reasoners_with_tool_expectations(flow)):
        reasoner = DEFAULT_REGISTRY.reasoners.get(reasoner_name)
        if reasoner is None:
            continue
        for key in sorted(reasoner.tools):
            expectation = expectations.get(
                scoped_tool_expectation_key(reasoner_name, key)
            )
            if expectation is not None:
                check_tool(key, expectation)

    for key in sorted(_direct_tool_keys(flow)):
        if (key, key) in checked or any(wire == key for _, wire in checked):
            continue
        if key in scoped_fallbacks:
            # This unscoped entry exists only as a compatibility lookup for a
            # scoped dotctx package. It must not bind an unrelated authored
            # call with the same common name (for example, ``lookup``).
            continue
        expectation = expectations.get(key)
        if expectation is None:
            continue
        check_tool(key, expectation)


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
    using_default_expectations = expected_tool_schemas is None
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
        aliases_authored = node.tool_aliases is not None
        aliases = node.tool_aliases or {str(key): str(key) for key in node.tools}
        grant_names = [str(key) for key in node.tools]
        if set(aliases) != set(grant_names):
            missing = sorted(set(grant_names) - set(aliases))
            extra = sorted(set(aliases) - set(grant_names))
            details: list[str] = []
            if missing:
                details.append("unbound aliases: " + ", ".join(missing))
            if extra:
                details.append("bindings without grants: " + ", ".join(extra))
            raise FreezeError("APP tool alias map mismatch: " + "; ".join(details))

        tool_defs: list[dict[str, Any]] = []
        tool_contracts: dict[str, dict[str, Any]] = {}
        for alias in grant_names:
            # Explicit aliases are provider-visible names and must satisfy the
            # portable bare-name contract. An absent alias map is the legacy APP
            # surface, where grants are wire ToolRefs such as ``srv/search``;
            # keep those valid and dispatch them by identity.
            if aliases_authored and not alias.isidentifier():
                raise FreezeError(
                    f"APP provider tool alias {alias!r} must be a bare Python identifier"
                )
            key = aliases[alias]
            tool = _resolve(_toolref_from_key(key), snapshot, overrides)
            manifest[tool.hash] = tool
            expectation = _app_tool_expectation(expectations, node, alias, key)
            tool_defs.append(
                {
                    "type": "function",
                    "function": {
                        "name": alias,
                        "description": expectation.description if expectation else "",
                        "parameters": tool.input_schema,
                    },
                }
            )
            payload: dict[str, Any] = tool.contract.to_json()
            payload["asserted"] = tool.asserted
            tool_contracts[alias] = payload
        if aliases_authored:
            node.tool_aliases = aliases
        node.tool_defs = tool_defs
        node.tool_contracts = tool_contracts

    # 6. Verify recorded dotctx tool-schema expectations against the snapshot.
    _check_tool_schema_drift(
        frozen_flow,
        snapshot,
        expectations,
        scoped_fallbacks=(
            DEFAULT_REGISTRY.scoped_tool_fallbacks
            if using_default_expectations
            else frozenset()
        ),
    )

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
