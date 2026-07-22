"""Canonical MCP surface comparison used by freeze and run-start preflight."""

from __future__ import annotations

import difflib
import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import FrozenTool, ToolManifest, definition_hash
from .freeze import McpServerSnapshot, McpSnapshot, McpToolSpec
from .ir import McpTool, canonical_json, toolref_key


class McpSurfacePolicy(str, Enum):
    """Run-start enforcement strength for a frozen MCP surface."""

    PIN = "pin"
    NAMES = "names"
    OFF = "off"

    @classmethod
    def coerce(cls, value: "McpSurfacePolicy | str") -> "McpSurfacePolicy":
        try:
            return value if isinstance(value, cls) else cls(value)
        except ValueError:
            raise ValueError("MCP surface policy must be 'pin', 'names', or 'off'") from None


@dataclass(frozen=True)
class McpSurfaceMismatch:
    server: str
    tool: str
    reason: str
    frozen_definition_hash: str
    fresh_definition_hash: str | None = None
    diff: str | None = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "server": self.server,
            "tool": self.tool,
            "reason": self.reason,
            "frozenDefinitionHash": self.frozen_definition_hash,
            "freshDefinitionHash": self.fresh_definition_hash,
        }
        if self.diff is not None:
            out["diff"] = self.diff
        return out


class McpSurfaceMismatchError(RuntimeError):
    """A live MCP server no longer matches a release's frozen tool surface."""

    def __init__(self, mismatches: Iterable[McpSurfaceMismatch]) -> None:
        self.mismatches = tuple(mismatches)
        names = ", ".join(f"{item.server}/{item.tool}" for item in self.mismatches)
        super().__init__(f"MCP tool surface mismatch: {names}")

    @property
    def details(self) -> list[dict[str, Any]]:
        return [item.to_json() for item in self.mismatches]


def _annotations_json(tool: FrozenTool | McpToolSpec, protocol_version: str | None) -> Any:
    annotations = tool.annotations
    if annotations is None:
        return None
    if isinstance(tool, McpToolSpec):
        annotations = annotations.normalized(protocol_version)
    payload = annotations.to_json()
    return payload or None


def canonical_frozen_definition(tool: FrozenTool) -> dict[str, Any]:
    """Return exactly the provider-controlled definition represented by ``tool``."""

    definition: dict[str, Any] = {
        "ref": toolref_key(tool.ref),
        "inputSchema": tool.input_schema,
        "outputSchema": tool.output_schema,
        "serverVersion": tool.server_version,
        "annotations": _annotations_json(tool, tool.protocol_version),
    }
    if tool.protocol_version is not None:
        definition["protocolVersion"] = tool.protocol_version
    return definition


def canonical_snapshot_definition(
    server: McpServerSnapshot,
    tool_name: str,
    tool: McpToolSpec,
) -> dict[str, Any]:
    """Return a canonical provider definition for a fresh ``tools/list`` item."""

    definition: dict[str, Any] = {
        "ref": f"{server.server}/{tool_name}",
        "inputSchema": tool.input_schema,
        "outputSchema": tool.output_schema,
        "serverVersion": server.server_version or server.version,
        "annotations": _annotations_json(tool, server.protocol_version),
    }
    if server.protocol_version is not None:
        definition["protocolVersion"] = server.protocol_version
    return definition


def snapshot_definition_hash(
    server: McpServerSnapshot,
    tool_name: str,
    tool: McpToolSpec,
) -> str:
    """Hash a fresh definition with the same canonical rules as ``FrozenTool``."""

    return definition_hash(
        McpTool(server=server.server, tool=tool_name),
        tool.input_schema,
        tool.output_schema,
        server.server_version or server.version,
        tool.annotations.normalized(server.protocol_version),
        server.protocol_version,
    )


def canonical_surface_digest(tools: ToolManifest | Iterable[FrozenTool]) -> str:
    """Stable digest for the referenced MCP portion of a frozen manifest."""

    values = tools.values() if isinstance(tools, Mapping) else tools
    surface = {
        toolref_key(tool.ref): tool.definition_hash
        for tool in values
        if isinstance(tool.ref, McpTool)
    }
    digest = hashlib.sha256(canonical_json(surface).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _definition_diff(frozen: dict[str, Any], fresh: dict[str, Any]) -> str:
    before = json.dumps(frozen, indent=2, sort_keys=True).splitlines()
    after = json.dumps(fresh, indent=2, sort_keys=True).splitlines()
    return "\n".join(
        difflib.unified_diff(before, after, fromfile="frozen", tofile="fresh", lineterm="")
    )


def compare_mcp_surface(
    frozen: ToolManifest | Iterable[FrozenTool],
    fresh: McpSnapshot,
    *,
    policy: McpSurfacePolicy | str = McpSurfacePolicy.PIN,
) -> tuple[McpSurfaceMismatch, ...]:
    """Compare only release-referenced MCP tools under ``pin``/``names``/``off``.

    Additional live tools are intentionally ignored: they are not part of the
    release's reachable surface.  ``names`` checks only presence.  ``pin``
    requires exact canonical definition-hash equality.
    """

    selected = McpSurfacePolicy.coerce(policy)
    if selected is McpSurfacePolicy.OFF:
        return ()
    values = frozen.values() if isinstance(frozen, Mapping) else frozen
    mismatches: list[McpSurfaceMismatch] = []
    for frozen_tool in sorted(values, key=lambda item: toolref_key(item.ref)):
        ref = frozen_tool.ref
        if not isinstance(ref, McpTool):
            continue
        server = fresh.servers.get(ref.server)
        if server is None:
            mismatches.append(
                McpSurfaceMismatch(
                    server=ref.server,
                    tool=ref.tool,
                    reason="missing_server",
                    frozen_definition_hash=frozen_tool.definition_hash,
                )
            )
            continue
        fresh_tool = server.tools.get(ref.tool)
        if fresh_tool is None:
            mismatches.append(
                McpSurfaceMismatch(
                    server=ref.server,
                    tool=ref.tool,
                    reason="missing_tool",
                    frozen_definition_hash=frozen_tool.definition_hash,
                )
            )
            continue
        if selected is McpSurfacePolicy.NAMES:
            continue
        fresh_hash = snapshot_definition_hash(server, ref.tool, fresh_tool)
        if frozen_tool.definition_hash != fresh_hash:
            frozen_definition = canonical_frozen_definition(frozen_tool)
            fresh_definition = canonical_snapshot_definition(server, ref.tool, fresh_tool)
            mismatches.append(
                McpSurfaceMismatch(
                    server=ref.server,
                    tool=ref.tool,
                    reason="definition_hash",
                    frozen_definition_hash=frozen_tool.definition_hash,
                    fresh_definition_hash=fresh_hash,
                    diff=_definition_diff(frozen_definition, fresh_definition),
                )
            )
    return tuple(mismatches)


def assert_mcp_surface(
    frozen: ToolManifest | Iterable[FrozenTool],
    fresh: McpSnapshot,
    *,
    policy: McpSurfacePolicy | str = McpSurfacePolicy.PIN,
) -> None:
    """Raise :class:`McpSurfaceMismatchError` when comparison fails."""

    mismatches = compare_mcp_surface(frozen, fresh, policy=policy)
    if mismatches:
        raise McpSurfaceMismatchError(mismatches)


# A descriptive alias used by preflight call sites.
compare_tool_surfaces = compare_mcp_surface


__all__ = [
    "McpSurfaceMismatch",
    "McpSurfaceMismatchError",
    "McpSurfacePolicy",
    "assert_mcp_surface",
    "canonical_frozen_definition",
    "canonical_snapshot_definition",
    "canonical_surface_digest",
    "compare_mcp_surface",
    "compare_tool_surfaces",
    "snapshot_definition_hash",
]
