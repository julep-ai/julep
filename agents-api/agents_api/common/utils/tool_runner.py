from __future__ import annotations

import json
import contextlib
from typing import Any, Awaitable, Callable, Sequence, cast, Union, TypeVar

from beartype import beartype
from litellm.utils import ModelResponse
from litellm.types.utils import ChatCompletionMessageToolCall

from ...clients import litellm
from ...autogen.openapi_model import (
    BaseChosenToolCall,
    ChosenFunctionCall,
    CreateToolRequest,
    FunctionCallOption,
    Tool,
    ToolExecutionResult,
)
from ...activities.tool_executor import format_tool_results_for_llm
from ...activities.execute_integration import execute_integration
from ...activities.execute_system import execute_system
from ...activities.execute_api_call import execute_api_call
from ...common.protocol.tasks import StepContext
from ...clients import integrations

# AIDEV-NOTE: Formats internal Tool definitions into the structure expected by the LLM (currently focused on OpenAI function tools and integrations).
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
        return integrations.convert_to_openai_tool(
            provider=tool.integration.provider,
            method=tool.integration.method,
        )
    # if tool.type == "system" and tool.system is not None:
    #     return {
    #         "type": "function",
    #         "function": {
    #             "name": tool.name,
    #             "description": tool.description
    #             or f"System {tool.system.resource}.{tool.system.operation}",
    #             "parameters": {
    #                 "type": "object",
    #                 "additionalProperties": True,
    #             },
    #         },
    #     }
    # if tool.type == "api_call" and tool.api_call is not None:
    #     return {
    #         "type": "function",
    #         "function": {
    #             "name": tool.name,
    #             "description": tool.description
    #             or f"API call {tool.api_call.method} {tool.api_call.url}",
    #             "parameters": {
    #                 "type": "object",
    #                 "additionalProperties": True,
    #             },
    #         },
    #     }
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
def convert_litellm_to_chosen_tool_call(
    call: ChatCompletionMessageToolCall,
    tool: Tool | CreateToolRequest
) -> BaseChosenToolCall:
    """
    Convert a LiteLLM ChatCompletionMessageToolCall to the appropriate BaseChosenToolCall subtype
    based on the tool's type. This preserves the internal tool type information.
    """
    # Parse arguments from the string
    arguments_str = call.function.arguments
    arguments = {}
    if arguments_str:
        with contextlib.suppress(json.JSONDecodeError):
            arguments = json.loads(arguments_str)
    
    # Common fields for all tool types
    base_args = {
        "id": call.id,
        "type": tool.type,  # Preserve the original tool type
    }
    
    # Create appropriate tool call structure based on the tool type
    if tool.type == "function":
        return ChosenFunctionCall(
            **base_args,
            function=FunctionCallOption(
                name=call.function.name,
                arguments=arguments_str  # Keep the original string format
            )
        )
    elif tool.type == "integration":
        # For integration tools, we need to structure it properly
        return BaseChosenToolCall(
            **base_args,
            function=FunctionCallOption(
                name=call.function.name,
                arguments=arguments_str  # Keep arguments as a string
            )
        )
    elif tool.type == "api_call":
        return BaseChosenToolCall(
            **base_args,
            function=FunctionCallOption(
                name=call.function.name,
                arguments=arguments_str
            )
        )
    elif tool.type == "system":
        return BaseChosenToolCall(
            **base_args,
            function=FunctionCallOption(
                name=call.function.name,
                arguments=arguments_str
            )
        )
    else:
        # For other tool types (like Anthropic tools)
        return BaseChosenToolCall(
            **base_args,
            function=FunctionCallOption(
                name=call.function.name,
                arguments=arguments_str
            )
        )

@beartype
async def run_llm_with_tools(
    *,
    messages: list[dict],
    tools: Sequence[Tool | CreateToolRequest],
    settings: dict[str, Any],
    run_tool_call: Callable[[Tool | CreateToolRequest, BaseChosenToolCall], Awaitable[ToolExecutionResult]], # TODO: Probably can be removed
) -> ModelResponse:
    """Run the LLM with a tool loop."""

    formatted_tools = [format_tool(t) for t in tools]
    
    # Build a map of function name to tool
    tool_map = {}
    for t in tools:
        if t.type == "integration" and t.integration is not None:
            tool_map[t.integration.provider] = t
        else:
            tool_map[t.name] = t

    while True:
        response: ModelResponse = await litellm.acompletion(
            tools=formatted_tools,
            messages=messages,
            **settings,
        )
        choice = response.choices[0]
        messages.append(choice.message.model_dump())

        if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
            return response

        # Process ALL tool calls before continuing
        for litellm_call in choice.message.tool_calls:
            # Get the function name from the call
            function_name = litellm_call.function.name
            
            # Try to find the tool by name or handle integration tools
            tool = tool_map.get(function_name)
            
            if tool is None:
                # Create a dummy response for unknown tools to satisfy the API requirement
                error_result = ToolExecutionResult(
                    id=litellm_call.id, 
                    name=function_name,
                    output={},
                    error=f"Tool '{function_name}' not found"
                )
                messages.append(format_tool_results_for_llm(error_result))
                continue
            
            # Convert LiteLLM call to appropriate internal format while preserving tool type
            internal_call = convert_litellm_to_chosen_tool_call(litellm_call, tool)
            
            # Execute the tool with the correctly typed call
            result = await run_tool_call(tool, internal_call)
            messages.append(format_tool_results_for_llm(result))


