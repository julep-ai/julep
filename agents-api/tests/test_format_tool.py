from agents_api.activities.task_steps.prompt_step import format_tool
from agents_api.autogen.openapi_model import (
    ApiCallDef,
    CreateToolRequest,
    DummyIntegrationDef,
    SystemDef,
)
from ward import test


@test("format_tool formats system tools")
def _():
    tool = CreateToolRequest(
        name="system_tool",
        type="system",
        system=SystemDef(resource="agent", operation="list"),
    )
    formatted = format_tool(tool)
    assert formatted["type"] == "function"
    assert formatted["function"]["name"] == "system_tool"
    assert formatted["function"]["parameters"]


@test("format_tool formats integration tools")
def _():
    tool = CreateToolRequest(
        name="integration_tool",
        type="integration",
        integration=DummyIntegrationDef(provider="dummy"),
    )
    formatted = format_tool(tool)
    assert formatted["function"]["name"] == "integration_tool"
    assert formatted["function"]["parameters"]


@test("format_tool formats api_call tools")
def _():
    api = ApiCallDef(method="GET", url="https://example.com")
    tool = CreateToolRequest(name="api_tool", type="api_call", api_call=api)
    formatted = format_tool(tool)
    assert formatted["function"]["name"] == "api_tool"
    assert "method" in formatted["function"]["parameters"]["properties"]
