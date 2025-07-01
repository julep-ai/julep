# AIDEV-NOTE: This module contains the activity for executing a prompt step, which interacts with the language model.
import functools

from beartype import beartype
from litellm.types.utils import ModelResponse
from temporalio import activity
from temporalio.exceptions import ApplicationError

from ...autogen.openapi_model import Tool
from ...clients import (
    litellm,  # We dont directly import `acompletion` so we can mock it
)
from ...common.protocol.tasks import ExecutionInput, StepContext, StepOutcome
from ...common.utils.feature_flags import get_feature_flag_value
from ...common.utils.tool_runner import format_tool, run_context_tool, run_llm_with_tools
from ...env import debug
from .base_evaluate import base_evaluate

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


@activity.defn
@beartype
# AIDEV-NOTE: Executes the prompt step by interacting with the language model via LiteLLM.
# Handles prompt evaluation, tool formatting, model calling, and response processing.
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
        exclude=excluded_keys,
        exclude_unset=True,
    )
    passed_settings.update(passed_settings.pop("settings", {}) or {})
    passed_settings["user"] = str(context.execution_input.developer_id)

    if get_feature_flag_value(
        "auto_tool_calls_prompt_step", developer_id=str(context.execution_input.developer_id)
    ):
        if not passed_settings.get("tools"):
            passed_settings.pop("tool_choice", None)

        all_tools = await context.tools()

        passed_settings = {k: v for k, v in passed_settings.items() if v is not None}

        completion_data: dict = {
            "model": agent_model,
            **agent_default_settings,
            **passed_settings,
        }

        responses: list[dict] = await run_llm_with_tools(
            messages=prompt,
            tools=all_tools,
            settings=completion_data,
            run_tool_call=functools.partial(run_context_tool, context),
        )

        if context.current_step.unwrap:
            response = responses[-1]

            # TODO: Allow unwrapping of function tool calls
            if response["tool_calls"] is not None:
                msg = "Function tool calls unwrapping is not supported yet"
                raise ApplicationError(msg)

            return StepOutcome(
                output=response["content"],
                next=None,
            )

        return StepOutcome(
            output=responses,
            next=None,
        )
    if not passed_settings.get("tools"):
        passed_settings.pop("tool_choice", None)

    # Format tools for litellm
    formatted_tools = [await format_tool(tool) for tool in await context.tools()]

    # Map tools to their original objects
    tools_mapping: dict[str, Tool] = {
        fmt_tool.get("name") or fmt_tool.get("function", {}).get("name"): orig_tool
        for fmt_tool, orig_tool in zip(formatted_tools, await context.tools())
    }

    # Check if using Claude model and has specific tool types
    is_claude_model = agent_model.lower().startswith("claude-3.5")

    # AIDEV-FIXME: Hack to make the computer use tools compatible with litellm.
    # Issue was: litellm expects type to be `computer_20241022` and spec to be
    # `function` (see: https://docs.litellm.ai/docs/providers/anthropic#computer-tools)
    # but we don't allow that (spec should match type).
    formatted_tools = []
    for i, tool in enumerate(await context.tools()):
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
    # AIDEV-TODO: Enable formatted_tools once format-tools PR is merged.
    # FIXME: Enable formatted_tools once format-tools PR is merged.
    if not is_claude_model:
        formatted_tools = None

    # AIDEV-HOTFIX: for groq calls, litellm expects tool_calls_id not to be in the messages.
    # AIDEV-FIXME: This is a temporary fix. We need to update the agent-api to use the new tool calling format.
    # HOTFIX: for groq calls, litellm expects tool_calls_id not to be in the messages
    # FIXME: This is a temporary fix. We need to update the agent-api to use the new tool calling format
    # AIDEV-TODO: Enable formatted_tools once format-tools PR is merged.
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

    # AIDEV-NOTE: Re-convert tool-calls from LLM response back to internal integration/system call format if needed.
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
