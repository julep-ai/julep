from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Sequence

from beartype import beartype
from litellm.utils import ModelResponse

from ...clients import litellm
from ...autogen.openapi_model import (
    BaseChosenToolCall,
    CreateToolRequest,
    Tool,
    ToolExecutionResult,
)
import contextlib
from ...activities.execute_api_call import execute_api_call
from ...activities.execute_integration import execute_integration
from ...activities.execute_system import execute_system
from ...activities.tool_executor import format_tool_results_for_llm
from ..protocol.tasks import StepContext


@beartype
def format_tool(tool: Tool | CreateToolRequest) -> dict:
    """Format a Tool or CreateToolRequest for the LLM."""

    if tool.type == "function":
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.function and tool.function.parameters,
            },
        }
    if tool.type == "integration" and tool.integration is not None:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description
                or f"Integration {tool.integration.provider}.{tool.integration.method}",
                "parameters": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
        }
    if tool.type == "system" and tool.system is not None:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description
                or f"System {tool.system.resource}.{tool.system.operation}",
                "parameters": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
        }
    if tool.type == "api_call" and tool.api_call is not None:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description
                or f"API call {tool.api_call.method} {tool.api_call.url}",
                "parameters": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
        }
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description},
    }


@beartype
async def run_context_tool(
    context: StepContext,
    tool: Tool | CreateToolRequest,
    call: BaseChosenToolCall,
) -> ToolExecutionResult:
    """Execute a tool call within a workflow step context."""

    arguments: dict[str, Any] = {}
    if call.function and call.function.arguments:
        with contextlib.suppress(Exception):
            arguments = json.loads(call.function.arguments)

    if tool.type == "integration" and tool.integration:
        output = await execute_integration(context, tool.name, tool.integration, arguments)
        return ToolExecutionResult(id=call.id or "", name=tool.name, output=output)

    if tool.type == "system" and tool.system:
        system = tool.system.model_copy(update={"arguments": arguments})
        output = await execute_system(context, system)
        return ToolExecutionResult(id=call.id or "", name=tool.name, output=output)

    if tool.type == "api_call" and tool.api_call:
        output = await execute_api_call(tool.api_call, arguments)
        return ToolExecutionResult(id=call.id or "", name=tool.name, output=output)

    return ToolExecutionResult(id=call.id or "", name=tool.name, output={})


@beartype
async def run_llm_with_tools(
    *,
    messages: list[dict],
    tools: Sequence[Tool | CreateToolRequest],
    settings: dict[str, Any],
    run_tool_call: Callable[[Tool | CreateToolRequest, BaseChosenToolCall], Awaitable[ToolExecutionResult]],
    user: str | None = None,
) -> ModelResponse:
    """Run the LLM with a tool loop."""

    formatted_tools = [format_tool(t) for t in tools]
    tool_map = {t.name: t for t in tools}

    while True:
        response: ModelResponse = await litellm.acompletion(
            tools=formatted_tools,
            messages=messages,
            user=user,
            **settings,
        )
        choice = response.choices[0]
        messages.append(choice.message.model_dump())

        if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
            return response

        for call in choice.message.tool_calls:
            tool = tool_map.get(call.function.name)
            if tool is None:
                continue
            result = await run_tool_call(tool, call)
            messages.append(format_tool_results_for_llm(result))


