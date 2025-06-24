# AIDEV-NOTE: This module provides helper functions for generating tool call IDs and constructing tool call objects.
import base64
import secrets

from ...autogen.openapi_model import CreateToolRequest, Tool


# AIDEV-TODO: This function for generating call IDs should be moved to a more appropriate location.
# FIXME: This shouldn't be here.
def generate_call_id() -> str:
    # Generate 18 random bytes (which will result in 24 base64 characters)
    random_bytes = secrets.token_bytes(18)
    # Encode to base64 and remove padding
    base64_string = base64.urlsafe_b64encode(random_bytes).decode("ascii").rstrip("=")
    # Add the "call_" prefix
    return f"call_{base64_string}"


# AIDEV-TODO: Refactor this function for constructing tool calls and move it to a more appropriate location.
# FIXME: This shouldn't be here, and shouldn't be done this way. Should be refactored.
# AIDEV-NOTE: Constructs a dictionary representing a tool call based on the tool definition and arguments.
def construct_tool_call(
    tool: CreateToolRequest | Tool, arguments: dict, call_id: str
) -> dict:
    return {
        tool.type: {
            "arguments": arguments,
            "name": tool.name,
        }
        if tool.type != "system"
        else {
            "resource": tool.system and tool.system.resource,
            "operation": tool.system and tool.system.operation,
            "resource_id": tool.system and tool.system.resource_id,
            "subresource": tool.system and tool.system.subresource,
            "arguments": arguments,
        },
        "id": call_id,
        "type": tool.type,
    }
