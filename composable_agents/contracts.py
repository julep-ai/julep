"""Tool contracts and the frozen manifest (blueprint §1.3).

MCP hints are *untrusted* by spec, so the annotation -> contract mapping is
deliberately conservative: anything not explicitly hinted read-only/idempotent
collapses to ``write`` / ``none``, which makes it illegal inside a race until a
human asserts otherwise in the capability manifest (§9). The manifest is keyed
by a content hash over the tool's identity and schema; that hash is what every
IR ``ToolRef`` is bound to at freeze, and what replay re-checks.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

from .ir import JSONSchema, ToolRef, canonical_json, toolref_from_json, toolref_key
from .kinds import Effect, Idempotency


@dataclass(frozen=True)
class ToolContract:
    """The asserted (or conservatively defaulted) behavior of a tool."""

    effect: Effect
    idempotency: Idempotency

    def to_json(self) -> dict[str, Any]:
        return {"effect": self.effect.value, "idempotency": self.idempotency.value}

    @staticmethod
    def from_json(d: dict[str, Any]) -> "ToolContract":
        return ToolContract(
            effect=Effect(d["effect"]),
            idempotency=Idempotency(d["idempotency"]),
        )


# Conservative default applied to *any* tool before overrides.
CONSERVATIVE_DEFAULT = ToolContract(effect=Effect.WRITE, idempotency=Idempotency.NONE)


@dataclass(frozen=True)
class McpAnnotations:
    """The four MCP behavior hints we know how to read. All optional."""

    read_only_hint: Optional[bool] = None
    destructive_hint: Optional[bool] = None
    open_world_hint: Optional[bool] = None
    idempotent_hint: Optional[bool] = None

    @staticmethod
    def from_mcp(d: dict[str, Any]) -> "McpAnnotations":
        # MCP puts these under tool.annotations; accept a flat dict too.
        ann = d.get("annotations", d) if isinstance(d, dict) else {}
        return McpAnnotations(
            read_only_hint=ann.get("readOnlyHint"),
            destructive_hint=ann.get("destructiveHint"),
            open_world_hint=ann.get("openWorldHint"),
            idempotent_hint=ann.get("idempotentHint"),
        )

    def to_json(self) -> dict[str, bool]:
        out: dict[str, bool] = {}
        if self.read_only_hint is not None:
            out["readOnlyHint"] = self.read_only_hint
        if self.destructive_hint is not None:
            out["destructiveHint"] = self.destructive_hint
        if self.open_world_hint is not None:
            out["openWorldHint"] = self.open_world_hint
        if self.idempotent_hint is not None:
            out["idempotentHint"] = self.idempotent_hint
        return out


def contract_from_annotations(ann: McpAnnotations) -> ToolContract:
    """Seed a contract from MCP hints (blueprint §1.3 table), conservatively.

    Precedence for ``effect``: destructive > external > read-only > default.
    ``idempotency`` becomes ``native`` only when explicitly hinted.
    """
    effect = CONSERVATIVE_DEFAULT.effect
    if ann.read_only_hint:
        effect = Effect.READ
    if ann.open_world_hint:
        effect = Effect.EXTERNAL
    if ann.destructive_hint:
        effect = Effect.DANGEROUS  # destructive dominates

    idempotency = (
        Idempotency.NATIVE if ann.idempotent_hint else CONSERVATIVE_DEFAULT.idempotency
    )
    return ToolContract(effect=effect, idempotency=idempotency)


def _sha256_json(value: dict[str, Any]) -> str:
    payload = canonical_json(value)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _annotations_json(
    annotations: Optional[McpAnnotations | dict[str, Any]],
) -> Optional[dict[str, Any]]:
    if annotations is None:
        return None
    if isinstance(annotations, McpAnnotations):
        payload = annotations.to_json()
        return payload or None
    return annotations or None


def definition_hash(
    ref: ToolRef,
    input_schema: JSONSchema,
    output_schema: Optional[JSONSchema] = None,
    server_version: Optional[str] = None,
    annotations: Optional[McpAnnotations | dict[str, Any]] = None,
) -> str:
    """Provider definition identity for a frozen tool.

    This covers what the provider advertises: reference, input/output schemas,
    server version, and the MCP annotation snapshot. It intentionally excludes
    deployment-local contract assertions.
    """
    return _sha256_json(
        {
            "ref": toolref_key(ref),
            "inputSchema": input_schema,
            "outputSchema": output_schema,
            "serverVersion": server_version,
            "annotations": _annotations_json(annotations),
        }
    )


def execution_hash(
    tool_definition_hash: str,
    contract: ToolContract,
    asserted: bool,
) -> str:
    """Execution identity for the exact contract this deployment will use."""
    return _sha256_json(
        {
            "definitionHash": tool_definition_hash,
            "contract": contract.to_json(),
            "asserted": asserted,
        }
    )


@dataclass(frozen=True)
class FrozenTool:
    """A tool pinned at run start: hash-addressed, with a settled contract."""

    definition_hash: str
    execution_hash: str
    ref: ToolRef
    input_schema: JSONSchema
    contract: ToolContract
    output_schema: Optional[JSONSchema] = None
    server_version: Optional[str] = None
    # True iff the contract was explicitly asserted (capability manifest / native
    # declaration) rather than defaulted from untrusted MCP hints. Race admission
    # (§5) treats an unasserted contract as `none`.
    asserted: bool = False

    @property
    def hash(self) -> str:
        return self.execution_hash

    @staticmethod
    def create(
        ref: ToolRef,
        input_schema: JSONSchema,
        contract: ToolContract,
        output_schema: Optional[JSONSchema] = None,
        server_version: Optional[str] = None,
        asserted: bool = False,
        annotations: Optional[McpAnnotations | dict[str, Any]] = None,
    ) -> "FrozenTool":
        def_hash = definition_hash(
            ref,
            input_schema,
            output_schema,
            server_version,
            annotations,
        )
        exec_hash = execution_hash(def_hash, contract, asserted)
        return FrozenTool(
            definition_hash=def_hash,
            execution_hash=exec_hash,
            ref=ref,
            input_schema=input_schema,
            contract=contract,
            output_schema=output_schema,
            server_version=server_version,
            asserted=asserted,
        )

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "hash": self.execution_hash,
            "definitionHash": self.definition_hash,
            "executionHash": self.execution_hash,
            "ref": self.ref.to_json(),
            "inputSchema": self.input_schema,
            "contract": self.contract.to_json(),
            "asserted": self.asserted,
        }
        if self.output_schema is not None:
            out["outputSchema"] = self.output_schema
        if self.server_version is not None:
            out["serverVersion"] = self.server_version
        return out


# hash -> FrozenTool
ToolManifest = dict[str, FrozenTool]


def manifest_to_json(m: ToolManifest) -> dict[str, Any]:
    return {h: t.to_json() for h, t in m.items()}


def frozentool_from_json(d: dict[str, Any]) -> FrozenTool:
    """Rebuild a :class:`FrozenTool` from its ``to_json`` form.

    The hash is taken verbatim from the payload rather than recomputed: a frozen
    manifest crossing a serialization boundary (workflow input, projection) must
    round-trip to the *same* hash the run was bound to, even if this process's
    hashing were to differ.
    """
    execution = d.get("executionHash", d.get("hash"))
    if execution is None:
        raise KeyError("executionHash")
    return FrozenTool(
        definition_hash=d.get("definitionHash", d.get("hash", execution)),
        execution_hash=execution,
        ref=toolref_from_json(d["ref"]),
        input_schema=d.get("inputSchema", {}),
        contract=ToolContract.from_json(d["contract"]),
        output_schema=d.get("outputSchema"),
        server_version=d.get("serverVersion"),
        asserted=d.get("asserted", False),
    )


def manifest_from_json(d: dict[str, Any]) -> ToolManifest:
    """Inverse of :func:`manifest_to_json`."""
    return {h: frozentool_from_json(t) for h, t in d.items()}
