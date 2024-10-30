import os

from anthropic import Anthropic  # Import Anthropic client
from beartype import beartype
from temporalio import activity
from temporalio.exceptions import ApplicationError

from ...autogen.Tools import Tool
from ...clients import (
    litellm,  # We dont directly import `acompletion` so we can mock it
)
from ...common.protocol.tasks import StepContext, StepOutcome
from ...common.storage_handler import auto_blob_store
from ...common.utils.template import render_template
from ...env import anthropic_api_key, debug
from ...models.tools.list_tools import list_tools

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


# FIXME: This shouldn't be here.
def format_agent_tool(tool: Tool) -> dict:
    if tool.function:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.function.parameters,
            },
        }
    elif tool.computer_20241022:
        return {
            "type": tool.type,
            "name": tool.name,
            "display_width_px": tool.display_width_px,
            "display_height_px": tool.display_height_px,
            "display_number": tool.display_number,
        }
    elif tool.bash_20241022:
        return {
            "type": tool.type,
            "name": tool.name,
        }
    elif tool.text_editor_20241022:
        return {
            "type": tool.type,
            "name": tool.name,
        }
    # TODO: Add integration | system | api_call tool types
    else:
        return {}


@activity.defn
@auto_blob_store
@beartype
async def prompt_step(context: StepContext) -> StepOutcome:
    # Get context data
    prompt: str | list[dict] = context.current_step.model_dump()["prompt"]
    context_data: dict = context.model_dump()

    # Render template messages
    prompt = await render_template(
        prompt,
        context_data,
        skip_vars=["developer_id"],
    )
    # Get settings and run llm
    agent_default_settings: dict = (
        context.execution_input.agent.default_settings.model_dump()
        if context.execution_input.agent.default_settings
        else {}
    )
    agent_model: str = (
        context.execution_input.agent.model
        if context.execution_input.agent.model
        else "gpt-4o"
    )

    agent_tools = list_tools(
        developer_id=context.execution_input.developer_id,
        agent_id=context.execution_input.agent.id,
        limit=128,  # Max number of supported functions in OpenAI. See https://platform.openai.com/docs/api-reference/chat/create
        offset=0,
        sort_by="created_at",
        direction="desc",
    )

    if context.current_step.settings:
        passed_settings: dict = context.current_step.settings.model_dump(
            exclude_unset=True
        )
    else:
        passed_settings: dict = {}

    # Wrap the prompt in a list if it is not already
    if isinstance(prompt, str):
        prompt = [{"role": "user", "content": prompt}]

    # Format agent_tools for litellm
    formatted_agent_tools = [
        format_agent_tool(tool) for tool in agent_tools if format_agent_tool(tool)
    ]

    # Check if the model is Anthropic
    if "claude-3.5-sonnet-20241022" == agent_model.lower():
        # Retrieve the API key from the environment variable
        betas = [COMPUTER_USE_BETA_FLAG]
        # Use Anthropic API directly
        client = Anthropic(api_key=anthropic_api_key)

        # Claude Response
        response = await client.beta.messages.create(
            model=agent_model,
            messages=prompt,
            tools=formatted_agent_tools,
            max_tokens=1024,
            betas=betas,
        )

        return StepOutcome(
            output=response.model_dump()
            if hasattr(response, "model_dump")
            else response,
            next=None,
        )
    else:
        # Use litellm for other models
        completion_data: dict = {
            "model": agent_model,
            "tools": formatted_agent_tools or None,
            "messages": prompt,
            **agent_default_settings,
            **passed_settings,
        }

        extra_body = {
            "cache": {"no-cache": debug},
        }

        response = await litellm.acompletion(
            **completion_data,
            extra_body=extra_body,
        )

        if context.current_step.unwrap:
            if response.choices[0].finish_reason == "tool_calls":
                raise ApplicationError("Tool calls cannot be unwrapped")

            response = response.choices[0].message.content

        return StepOutcome(
            output=response.model_dump()
            if hasattr(response, "model_dump")
            else response,
            next=None,
        )
