# AIDEV-NOTE: This module contains the activity for executing a prompt step, which interacts with the language model.
import functools

from beartype import beartype
from temporalio import activity
from temporalio.exceptions import ApplicationError

from ...common.protocol.tasks import ExecutionInput, StepContext, StepOutcome
from ...common.utils.tool_runner import run_context_tool, run_llm_with_tools
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
