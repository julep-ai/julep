from unittest.mock import patch

from agents_api.autogen.openapi_model import (
    ApiCallDef,
    CreateToolRequest,
    DummyIntegrationDef,
    FunctionDef,
    SystemDef,
)
from agents_api.common.utils.tool_runner import format_tool
from ward import test


@test("format_tool correctly formats function tool")
async def _():
    tool = CreateToolRequest(
        name="test_function",
        type="function",
        function=FunctionDef(
            parameters={"type": "object", "properties": {"param1": {"type": "string"}}},
        ),
        description="A test function",
    )

    result = await format_tool(tool)

    assert result["type"] == "function"
    assert result["function"]["name"] == "test_function"
    assert result["function"]["description"] == "A test function"
    assert result["function"]["parameters"]["properties"]["param1"]["type"] == "string"


@test("format_tool correctly formats integration tool")
async def _():
    with patch("agents_api.clients.integrations.convert_to_openai_tool") as mock_convert:
        mock_convert.return_value = {
            "type": "function",
            "function": {
                "name": "slack",
                "description": "Send message to Slack",
                "parameters": {"type": "object"},
            },
        }

        tool = CreateToolRequest(
            name="dummy_integration",
            type="integration",
            integration=DummyIntegrationDef(provider="dummy", method="post_message"),
        )

        result = await format_tool(tool)

        assert result["type"] == "function"
        assert result["function"]["name"] == "slack"
        mock_convert.assert_called_once_with(provider="dummy", method="post_message")


@test("format_tool correctly formats api_call tool")
async def _():
    tool = CreateToolRequest(
        name="weather_api",
        type="api_call",
        description="Get weather data",
        api_call=ApiCallDef(
            method="GET",
            url="https://api.weather.com",
            params_schema={"type": "object", "properties": {"city": {"type": "string"}}},
        ),
    )

    result = await format_tool(tool)

    assert result["type"] == "function"
    assert result["function"]["name"] == "weather_api"
    assert result["function"]["description"] == "Get weather data"
    assert result["function"]["parameters"]["properties"]["city"]["type"] == "string"


@test("format_tool handles missing description")
async def _():
    tool = CreateToolRequest(
        name="simple_function",
        type="function",
        function=FunctionDef(parameters={"type": "object"}),
    )

    result = await format_tool(tool)

    assert result["type"] == "function"
    assert result["function"]["name"] == "simple_function"
    assert result["function"]["description"] is None
    assert result["function"]["parameters"]["type"] == "object"


@test("format_tool correctly formats system tool")
async def _():
    # Use a real system definition that maps to an actual handler
    tool = CreateToolRequest(
        name="get_agent",
        type="system",
        description="Retrieve agent information",
        system=SystemDef(
            resource="agent",
            operation="get",
        ),
    )

    result = await format_tool(tool)

    assert result["type"] == "function"
    assert result["function"]["name"] == "get_agent"
    assert result["function"]["description"] == "Retrieve agent information"
    # Check that parameters schema was generated from actual handler
    assert "properties" in result["function"]["parameters"]
    # The actual get_agent handler should have these parameters
    assert "agent_id" in result["function"]["parameters"]["properties"]
    # Check that the parameter has proper schema
    assert result["function"]["parameters"]["properties"]["agent_id"]["type"] == "string"
    assert result["function"]["parameters"]["properties"]["agent_id"]["format"] == "uuid"


@test("format_tool uses handler docstring when no description provided")
async def _():
    # Use a real system definition without providing a description
    tool = CreateToolRequest(
        name="list_agents",
        type="system",
        # No description provided - should fallback to handler's docstring
        system=SystemDef(
            resource="agent",
            operation="list",
        ),
    )

    result = await format_tool(tool)

    assert result["type"] == "function"
    assert result["function"]["name"] == "list_agents"
    # Should use handler's docstring when no description provided
    assert result["function"]["description"] is not None
    assert len(result["function"]["description"]) > 0
    # The description should come from the actual handler's docstring
    assert "agent" in result["function"]["description"].lower()
    # Check that parameters schema was generated
    assert "properties" in result["function"]["parameters"]
    # List operations typically have pagination parameters
    assert "limit" in result["function"]["parameters"]["properties"]
    assert "offset" in result["function"]["parameters"]["properties"]
