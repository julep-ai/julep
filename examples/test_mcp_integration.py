#!/usr/bin/env python3
"""
Test script for MCP integration with Julep.
Tests both stdio and HTTP transport modes.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "integrations-service"))

from integrations.autogen.Tools import (
    McpCallToolArguments,
    McpListToolsArguments,
    McpSetup,
)
from integrations.utils.integrations.mcp import call_tool, list_tools


async def test_stdio_transport():
    """Test MCP with stdio transport using the test server."""
    print("\n=== Testing stdio transport ===")
    
    # Setup for stdio transport
    setup = McpSetup(
        transport="stdio",
        command="python3",
        args=["examples/mcp-test-server.py"],
        cwd=str(Path(__file__).parent.parent),
        env={}
    )
    
    # Test listing tools
    print("\n1. Listing tools...")
    list_args = McpListToolsArguments()
    try:
        tools_result = await list_tools(setup, list_args)
        print(f"Found {len(tools_result.tools)} tools:")
        for tool in tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"Error listing tools: {e}")
        return
    
    # Test calling the echo tool
    print("\n2. Testing echo tool...")
    call_args = McpCallToolArguments(
        tool_name="echo",
        arguments={"message": "Hello from Julep MCP integration!"}
    )
    try:
        result = await call_tool(setup, call_args)
        print(f"Echo result: {result.text}")
    except Exception as e:
        print(f"Error calling echo tool: {e}")
    
    # Test calling the add tool
    print("\n3. Testing add tool...")
    call_args = McpCallToolArguments(
        tool_name="add",
        arguments={"a": 42, "b": 58}
    )
    try:
        result = await call_tool(setup, call_args)
        print(f"Add result: {result.text}")
    except Exception as e:
        print(f"Error calling add tool: {e}")
    
    # Test calling the get_time tool
    print("\n4. Testing get_time tool...")
    call_args = McpCallToolArguments(
        tool_name="get_time",
        arguments={}
    )
    try:
        result = await call_tool(setup, call_args)
        print(f"Time result: {result.text}")
    except Exception as e:
        print(f"Error calling get_time tool: {e}")


async def test_http_transport():
    """Test MCP with HTTP transport (requires HTTP MCP server)."""
    print("\n=== Testing HTTP transport ===")
    print("Note: This requires an HTTP MCP server running at http://localhost:8000/mcp")
    
    # Setup for HTTP transport
    setup = McpSetup(
        transport="http",
        http_url="http://localhost:8000/mcp",
        http_headers={}
    )
    
    # Test listing tools
    print("\n1. Listing tools via HTTP...")
    list_args = McpListToolsArguments()
    try:
        tools_result = await list_tools(setup, list_args)
        print(f"Found {len(tools_result.tools)} tools via HTTP")
    except Exception as e:
        print(f"HTTP transport not available or error: {e}")
        print("This is expected if no HTTP MCP server is running")


async def main():
    """Run all MCP integration tests."""
    print("MCP Integration Test Suite")
    print("=" * 50)
    
    # Test stdio transport (should work with our test server)
    await test_stdio_transport()
    
    # Test HTTP transport (optional, requires HTTP server)
    await test_http_transport()
    
    print("\n" + "=" * 50)
    print("MCP Integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())