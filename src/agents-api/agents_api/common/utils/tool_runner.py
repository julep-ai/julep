from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable, Sequence
from typing import Any
from uuid import UUID

from beartype import beartype
from litellm.types.utils import ChatCompletionMessageToolCall
from litellm.utils import ModelResponse
from pydantic import create_model

from ...activities.execute_api_call import execute_api_call
from ...activities.execute_integration import execute_integration
from ...activities.execute_system import execute_system
from ...activities.tool_executor import format_tool_results_for_llm
from ...autogen.openapi_model import (
    BaseChosenToolCall,
    CreateToolRequest,
    SystemDef,
    Tool,
    ToolExecutionResult,
)
from ...clients import integrations, litellm
from ...common.protocol.tasks import StepContext
from ...common.utils.evaluator import get_handler_with_filtered_params


# AIDEV-NOTE: Formats internal Tool definitions into the structure expected by the LLM (currently focused on OpenAI function tools and integrations).
@beartype
async def format_tool(tool: Tool | CreateToolRequest) -> dict:
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
        return await integrations.convert_to_openai_tool(
            provider=tool.integration.provider,
            method=tool.integration.method,
        )
    if tool.type == "api_call" and tool.api_call is not None:
        params = {}
        if tool.api_call.params_schema is not None:
            params = tool.api_call.params_schema.model_dump(exclude_none=True)
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": params,
            },
        }
    if tool.type == "system" and tool.system is not None:
        handler = get_handler_with_filtered_params(tool.system)
        sig = inspect.signature(handler)
        fields = {
            name: (
                param.annotation,
                ... if param.default is inspect.Signature.empty else param.default,
            )
            for name, param in sig.parameters.items()
        }
        Model = create_model(f"{handler.__name__.title()}Params", **fields)

        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or inspect.getdoc(handler),
                "parameters": Model.model_json_schema(),
            },
        }
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.function.parameters if tool.function else {},
        },
    }


# AIDEV-NOTE: Context-free tool execution function that can be used from chat endpoint or other contexts
@beartype
async def run_tool_call(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID | None = None,
    session_id: UUID | None = None,
    tool: Tool | CreateToolRequest,
    call: BaseChosenToolCall,
    connection_pool=None,
) -> ToolExecutionResult:
    """Execute a tool call with explicit parameters (no context required)."""

    call_spec = call.model_dump()
    arguments = call_spec[f"{call.type}"]["arguments"]
    setup = call_spec[f"{call.type}"]["setup"]

    if tool.type == "integration" and tool.integration:
        output = await execute_integration(
            developer_id=developer_id,
            agent_id=agent_id,
            task_id=task_id,
            session_id=session_id,
            tool_name=tool.name,
            integration=tool.integration,
            arguments=arguments,
            setup=setup,
            connection_pool=connection_pool,
        )
        return ToolExecutionResult(id=call.id, name=tool.name, output=output)

    if tool.type == "system" and tool.system:
        system = tool.system.model_copy(update={"arguments": arguments})
        system_dict = system.model_dump()
        system_def = SystemDef(**system_dict)
        output = await execute_system(
            developer_id=developer_id,
            system=system_def,
            connection_pool=connection_pool,
        )
        if hasattr(output, "model_dump"):
            return ToolExecutionResult(id=call.id, name=tool.name, output=output.model_dump())
        return ToolExecutionResult(id=call.id, name=tool.name, output=output)

    if tool.type == "api_call" and tool.api_call:
        arguments["include_response_content"] = tool.api_call.include_response_content
        output = await execute_api_call(tool.api_call, arguments)
        return ToolExecutionResult(id=call.id, name=tool.name, output=output)

    return ToolExecutionResult(id=call.id, name=tool.name, output={})


@beartype
async def run_context_tool(
    context: StepContext,
    tool: Tool | CreateToolRequest,
    call: BaseChosenToolCall,
) -> ToolExecutionResult:
    """Execute a tool call within a workflow step context."""

    # AIDEV-NOTE: Extract parameters from context and delegate to context-free function
    developer_id = context.execution_input.developer_id
    agent_id = context.execution_input.agent.id
    task_id = context.execution_input.task.id if context.execution_input.task else None
    session_id = getattr(context.execution_input, "session", None)
    session_id = session_id.id if session_id else None

    # Delegate to the context-free function
    return await run_tool_call(
        developer_id=developer_id,
        agent_id=agent_id,
        task_id=task_id,
        session_id=session_id,
        tool=tool,
        call=call,
    )


@beartype
def convert_litellm_to_chosen_tool_call(
    call: ChatCompletionMessageToolCall, tool: Tool | CreateToolRequest
) -> BaseChosenToolCall:
    """
    Convert a LiteLLM ChatCompletionMessageToolCall to the appropriate BaseChosenToolCall subtype
    based on the tool's type. This preserves the internal tool type information.
    """
    # Parse arguments from the string
    arguments_str = json.loads(call.function.arguments)

    tool_spec = tool.model_dump()
    if "id" in tool_spec:
        tool_spec.pop("id")

    setup = getattr(tool_spec, f"{tool.type}", {}).get("setup", {})
    if setup:
        setup = setup.model_dump()
    tool_spec[f"{tool.type}"]["setup"] = setup

    # TODO: add computer_20241022, text_editor_20241022, bash_20241022
    tool_spec[f"{tool.type}"]["arguments"] = arguments_str

    return BaseChosenToolCall(
        id=call.id,
        **tool_spec,
    )


@beartype
async def run_llm_with_tools(
    *,
    messages: list[dict],
    tools: Sequence[Tool | CreateToolRequest],
    settings: dict[str, Any],
    run_tool_call: Callable[
        [Tool | CreateToolRequest, BaseChosenToolCall], Awaitable[ToolExecutionResult]
    ],  # TODO: Probably can be removed
) -> list[dict]:
    """Run the LLM with a tool loop."""

    # Create a copy of messages to avoid mutating the original
    messages_copy = messages.copy()
    
    formatted_tools = [await format_tool(t) for t in tools]

    print("*" * 100)
    print("Formatted tools in run_llm_with_tools: ", formatted_tools)
    print("Messages: ", messages_copy)
    print("Settings: ", settings)
    print("*" * 100)

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
            messages=messages_copy,
            **settings,
        )
        choice = response.choices[0]
        messages_copy.append(choice.message.model_dump())

        print("*" * 100)
        print("Messages: ", messages_copy)
        print("*" * 100)

        if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
            return messages_copy

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
                    error=f"Tool '{function_name}' not found",
                )
                messages_copy.append(format_tool_results_for_llm(error_result))
                continue

            # Convert LiteLLM call to appropriate internal format while preserving tool type
            internal_call = convert_litellm_to_chosen_tool_call(litellm_call, tool)
            # Execute the tool with the correctly typed call
            result = await run_tool_call(tool, internal_call)
            messages_copy.append(format_tool_results_for_llm(result))
