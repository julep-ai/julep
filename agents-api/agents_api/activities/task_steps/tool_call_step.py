import base64
import secrets

from ...autogen.openapi_model import CreateToolRequest, Tool


# FIXME: This shouldn't be here.
def generate_call_id():
    # Generate 18 random bytes (which will result in 24 base64 characters)
    random_bytes = secrets.token_bytes(18)
    # Encode to base64 and remove padding
    base64_string = base64.urlsafe_b64encode(random_bytes).decode("ascii").rstrip("=")
    # Add the "call_" prefix
    return f"call_{base64_string}"


# FIXME: This shouldn't be here, and shouldn't be done this way. Should be refactored.
def construct_tool_call(tool: CreateToolRequest | Tool, arguments: dict, call_id: str) -> dict:
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
            "systemDefType": tool.system and tool.system.system_def_type,
        },
        "id": call_id,
        "type": tool.type,
    }
