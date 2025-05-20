# AIDEV-NOTE: This module contains the activity for executing a prompt step, which interacts with the language model.
from beartype import beartype
import contextlib
import json
from litellm.types.utils import ModelResponse
from temporalio import activity
from temporalio.exceptions import ApplicationError

from ...autogen.openapi_model import CreateToolRequest, Tool
from ...clients import (
    litellm,  # We dont directly import `acompletion` so we can mock it
)
from ...common.protocol.tasks import ExecutionInput, StepContext, StepOutcome
from ...env import debug
from ..execute_api_call import execute_api_call
from ..execute_integration import execute_integration
from ..execute_system import execute_system
from .base_evaluate import base_evaluate
from ...common.utils.tool_runner import format_tool, run_llm_with_tools

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

    if not passed_settings.get("tools"):
        passed_settings.pop("tool_choice", None)

    all_tools = await context.tools()

    async def run_tool(tool: Tool | CreateToolRequest, call: BaseChosenToolCall) -> ToolExecutionResult:
        arguments = {}
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

    passed_settings = {k: v for k, v in passed_settings.items() if v is not None}

    completion_data: dict = {
        "model": agent_model,
        **agent_default_settings,
        **passed_settings,
    }

    response: ModelResponse = await run_llm_with_tools(
        messages=prompt,
        tools=all_tools,
        settings=completion_data,
        run_tool_call=run_tool,
        user=str(context.execution_input.developer_id),
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

    return StepOutcome(
        output=response.model_dump(),
        next=None,
    )
