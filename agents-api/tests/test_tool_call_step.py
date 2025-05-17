from uuid import UUID

from agents_api.activities.task_steps.tool_call_step import (
    construct_tool_call,
    generate_call_id,
)
from agents_api.autogen.openapi_model import CreateToolRequest, SystemDef, Tool
import pytest


@pytest.mark.asyncio
async def test_generate_call_id_returns_call_id_with_proper_format():
    """generate_call_id returns call ID with proper format"""
    # Generate a call ID
    call_id = generate_call_id()

    # Validate the call ID format
    assert call_id.startswith("call_")
    # The call_id should be call_ followed by 24 base64 characters
    assert len(call_id) == 29
    # Should not have any padding character
    assert "=" not in call_id


@pytest.mark.asyncio
async def test_construct_tool_call_correctly_formats_function_tool():
    """construct_tool_call correctly formats function tool"""
    # Create a function tool
    tool = CreateToolRequest(
        name="test_function",
        type="function",
        function={
            "description": "A test function",
            "parameters": {"type": "object", "properties": {"param1": {"type": "string"}}},
        },
    )

    arguments = {"param1": "test_value"}
    call_id = "call_abc123"

    # Construct the tool call
    tool_call = construct_tool_call(tool, arguments, call_id)

    # Verify the structure
    assert tool_call["id"] == call_id
    assert tool_call["type"] == "function"
    assert tool_call["function"]["name"] == "test_function"
    assert tool_call["function"]["arguments"] == arguments


@pytest.mark.asyncio
async def test_construct_tool_call_correctly_formats_system_tool():
    """construct_tool_call correctly formats system tool"""
    # Create a system tool
    system_info = SystemDef(
        resource="doc",
        operation="get",
        resource_id=UUID("00000000-0000-0000-0000-000000000000"),
        subresource="doc",
    )

    tool = CreateToolRequest(name="test_system", type="system", system=system_info)

    arguments = {"param1": "test_value"}
    call_id = "call_abc123"

    # Construct the tool call
    tool_call = construct_tool_call(tool, arguments, call_id)

    # Verify the structure
    assert tool_call["id"] == call_id
    assert tool_call["type"] == "system"
    assert tool_call["system"]["resource"] == "doc"
    assert tool_call["system"]["operation"] == "get"
    assert tool_call["system"]["resource_id"] == UUID("00000000-0000-0000-0000-000000000000")
    assert tool_call["system"]["subresource"] == "doc"
    assert tool_call["system"]["arguments"] == arguments


@pytest.mark.asyncio
async def test_construct_tool_call_works_with_tool_objects_not_just_createtoolrequest():
    """construct_tool_call works with Tool objects (not just CreateToolRequest)"""
    # Create a function Tool (not CreateToolRequest)
    tool = Tool(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        name="test_function",
        type="function",
        function={
            "description": "A test function",
            "parameters": {"type": "object", "properties": {"param1": {"type": "string"}}},
        },
        agent_id=UUID("00000000-0000-0000-0000-000000000000"),
        developer_id=UUID("00000000-0000-0000-0000-000000000000"),
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z",
    )

    arguments = {"param1": "test_value"}
    call_id = "call_abc123"

    # Construct the tool call
    tool_call = construct_tool_call(tool, arguments, call_id)

    # Verify the structure
    assert tool_call["id"] == call_id
    assert tool_call["type"] == "function"
    assert tool_call["function"]["name"] == "test_function"
    assert tool_call["function"]["arguments"] == arguments
