from typing import Any

from pydantic import Field

from .base_models import BaseOutput


class McpToolCallOutput(BaseOutput):
    text: str | None = Field(
        default=None,
        description="Concatenated textual content, if any was returned.",
    )
    structured: dict[str, Any] | list[Any] | None = Field(
        default=None,
        description="Structured content returned by the server, if present.",
    )
    content: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Raw content items as returned by MCP (best-effort JSON form).",
    )
    is_error: bool = Field(
        default=False,
        description="Whether the server indicated an error for this call.",
    )


class McpToolInfo(BaseOutput):
    name: str
    description: str | None = None
    input_schema: dict[str, Any] | None = None


class McpListToolsOutput(BaseOutput):
    tools: list[McpToolInfo]
