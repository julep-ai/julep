from beartype import beartype
from litellm.types.utils import ModelResponse
from temporalio import activity
from temporalio.exceptions import ApplicationError

from ...autogen.openapi_model import Tool
from ...clients import (
    litellm,  # We dont directly import `acompletion` so we can mock it
)
from ...common.protocol.tasks import ExecutionInput, StepContext, StepOutcome
from ...env import debug
from .base_evaluate import base_evaluate

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


def format_tool(tool: Tool) -> dict:
    if tool.type == "function":
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.function and tool.function.parameters,
            },
        }

    # For other tool types, we need to translate them to the OpenAI function tool format
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description},
    }

    # FIXME: Implement system tools
    # if tool.type == "system":
    #     handler: Callable = get_handler_with_filtered_params(tool.system)

    #     lc_tool: BaseTool = tool_decorator(handler)

    #     json_schema: dict = lc_tool.get_input_jsonschema()

    #     formatted["function"]["description"] = formatted["function"][
    #         "description"
    #     ] or json_schema.get("description")

    #     formatted["function"]["parameters"] = json_schema

    # # FIXME: Implement integration tools
    # elif tool.type == "integration":
    #     raise NotImplementedError("Integration tools are not supported")

    # # FIXME: Implement API call tools
    # elif tool.type == "api_call":
    #     raise NotImplementedError("API call tools are not supported")


@activity.defn
@beartype
async def prompt_step(context: StepContext) -> StepOutcome:
    # Get context data
    prompt: str | list[dict] = context.current_step.model_dump()["prompt"]

    if isinstance(prompt, list):
        for i, msg in enumerate(prompt):
            prompt[i]["content"] = await base_evaluate(msg["content"], context)
            prompt[i]["role"] = await base_evaluate(msg["role"], context)
    else:
        prompt = await base_evaluate(prompt, context)

    # Wrap the prompt in a list if it is not already
    prompt = prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}]

    if not isinstance(context.execution_input, ExecutionInput):
        msg = "Expected ExecutionInput type for context.execution_input"
        raise TypeError(msg)

    # Get settings and run llm
    agent_default_settings: dict = context.execution_input.agent.default_settings or {}

    agent_model: str = (
        context.execution_input.agent.model if context.execution_input.agent.model else "gpt-4o"
    )

    excluded_keys = [
        "prompt",
        "kind_",
        "label",
        "unwrap",
        "auto_run_tools",
        "disable_cache",
        "tools",
    ]

    # Get passed settings
    passed_settings: dict = context.current_step.model_dump(
        exclude=excluded_keys, exclude_unset=True
    )
    passed_settings.update(passed_settings.pop("settings", {}) or {})

    if not passed_settings.get("tools"):
        passed_settings.pop("tool_choice", None)

    # Format tools for litellm
    formatted_tools = [format_tool(tool) for tool in context.tools]

    # Map tools to their original objects
    tools_mapping: dict[str, Tool] = {
        fmt_tool.get("name") or fmt_tool.get("function", {}).get("name"): orig_tool
        for fmt_tool, orig_tool in zip(formatted_tools, context.tools)
    }

    # Check if using Claude model and has specific tool types
    is_claude_model = agent_model.lower().startswith("claude-3.5")

    # FIXME: Hack to make the computer use tools compatible with litellm
    # Issue was: litellm expects type to be `computer_20241022` and spec to be
    # `function` (see: https://docs.litellm.ai/docs/providers/anthropic#computer-tools)
    # but we don't allow that (spec should match type).
    formatted_tools = []
    for i, tool in enumerate(context.tools):
        if tool.type == "computer_20241022" and tool.computer_20241022:
            function = tool.computer_20241022
            tool = {
                "type": tool.type,
                "function": {
                    "name": tool.name,
                    "parameters": {
                        k: v
                        for k, v in function.model_dump().items()
                        if k not in ["name", "type"]
                    },
                },
            }
            formatted_tools.append(tool)
    # For non-Claude models, we don't need to send tools
    # FIXME: Enable formatted_tools once format-tools PR is merged.
    if not is_claude_model:
        formatted_tools = None

    # HOTFIX: for groq calls, litellm expects tool_calls_id not to be in the messages
    # FIXME: This is a temporary fix. We need to update the agent-api to use the new tool calling format
    # FIXME: Enable formatted_tools once format-tools PR is merged.
    is_groq_model = agent_model.lower().startswith("llama-3.1")
    if is_groq_model:
        prompt = [
            {
                k: v
                for k, v in message.items()
                if k not in ["tool_calls", "tool_call_id", "user", "continue_", "name"]
            }
            for message in prompt
        ]

    # Remove None values from passed_settings (avoid overwriting agent's settings)
    passed_settings = {k: v for k, v in passed_settings.items() if v is not None}

    # Use litellm for other models
    completion_data: dict = {
        "model": agent_model,
        "tools": formatted_tools or None,
        "messages": prompt,
        **agent_default_settings,
        **passed_settings,
    }

    extra_body = {
        "cache": {"no-cache": debug or context.current_step.disable_cache},
    }

    response: ModelResponse = await litellm.acompletion(
        **completion_data,
        extra_body=extra_body,
    )

    if context.current_step.unwrap:
        if len(response.choices) != 1:
            msg = "Only one choice is supported"
            raise ApplicationError(msg)

        choice = response.choices[0]
        if choice.finish_reason == "tool_calls":
            msg = "Tool calls cannot be unwrapped"
            raise ApplicationError(msg)

        return StepOutcome(
            output=choice.message.content,
            next=None,
        )

    # Re-convert tool-calls to integration/system calls if needed
    response_as_dict = response.model_dump()

    for choice in response_as_dict["choices"]:
        if choice["finish_reason"] == "tool_calls":
            calls = choice["message"]["tool_calls"]

            for call in calls:
                call_name = call["function"]["name"]
                call_args = call["function"]["arguments"]

                original_tool = tools_mapping.get(call_name)
                if not original_tool:
                    msg = f"Tool {call_name} not found"
                    raise ApplicationError(msg)

                if original_tool.type == "function":
                    continue

                call.pop("function")
                call["type"] = original_tool.type
                call[original_tool.type] = {
                    "name": call_name,
                    "arguments": call_args,
                }

    return StepOutcome(
        output=response_as_dict,
        next=None,
    )
