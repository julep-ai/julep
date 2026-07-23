"""MCP tool references for define-by-construction authoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from . import dsl
from .ir import McpTool, Node
from .typed import FlowLike


@dataclass(frozen=True)
class McpToolStep(FlowLike[Any, Any]):
    """An MCP tool callable whose contract is supplied by a frozen snapshot."""

    server: str
    tool: str
    name: str

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        from .define import apply_if_authoring

        authored = apply_if_authoring(self, args, kwargs)
        if authored is not NotImplemented:
            return authored
        raise TypeError("McpToolStep can only be called with Handles inside an @flow")

    def to_ir(self) -> Node:
        return dsl.call(McpTool(server=self.server, tool=self.tool))


def mcp_tool(server: str, tool: str, *, name: Optional[str] = None) -> McpToolStep:
    """Declare an MCP tool for ``@flow`` authoring."""
    if not isinstance(server, str) or not server:
        raise ValueError("mcp_tool server must be a non-empty string")
    if not isinstance(tool, str) or not tool:
        raise ValueError("mcp_tool tool must be a non-empty string")
    if name is not None and (not isinstance(name, str) or not name):
        raise ValueError("mcp_tool name must be a non-empty string")
    return McpToolStep(server=server, tool=tool, name=name or tool)
