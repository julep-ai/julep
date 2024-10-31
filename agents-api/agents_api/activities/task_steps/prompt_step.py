import os
from datetime import datetime

from anthropic import Anthropic, AsyncAnthropic  # Import AsyncAnthropic client
from anthropic.types.beta.beta_message import BetaMessage
from beartype import beartype
from litellm import ChatCompletionMessageToolCall, Function, Message
from litellm.types.utils import Choices, ModelResponse
from litellm.utils import CustomStreamWrapper, ModelResponse
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
    if tool.type == "function":
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
    elif tool.type == "computer_20241022":
        return {
            "type": tool.type,
            "name": tool.name,
            "display_width_px": tool.spec["display_width_px"],
            "display_height_px": tool.spec["display_height_px"],
            "display_number": tool.spec["display_number"],
        }
    elif tool.type == "bash_20241022":
        return {
            "type": tool.type,
            "name": tool.name,
        }
    elif tool.type == "text_editor_20241022":
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
    # grab the tools from context.current_step.tools and then append it to the agent_tools
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
    # Initialize the formatted_agent_tools with context tools
    task_tools = context.tools
    formatted_agent_tools = [format_agent_tool(tool) for tool in task_tools]
    # Add agent_tools if they are not already in formatted_agent_tools
    for agent_tool in agent_tools:
        if (
            format_agent_tool(agent_tool)
            and format_agent_tool(agent_tool) not in formatted_agent_tools
        ):
            formatted_agent_tools.append(format_agent_tool(agent_tool))

    # Check if the model is Anthropic
    if agent_model.lower().startswith("claude-3.5") and any(
        tool["type"] in ["computer_20241022", "bash_20241022", "text_editor_20241022"]
        for tool in formatted_agent_tools
    ):
        # Retrieve the API key from the environment variable
        betas = [COMPUTER_USE_BETA_FLAG]
        # Use Anthropic API directly
        client = AsyncAnthropic(api_key=anthropic_api_key)
        new_prompt = [{"role": "user", "content": prompt[0]["content"]}]
        # Claude Response
        claude_response: BetaMessage = await client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=new_prompt,
            tools=formatted_agent_tools,
            max_tokens=1024,
            betas=betas,
        )

        # Claude returns [ToolUse | TextBlock]
        # We need to convert tool_use to tool_calls
        # And set content = TextBlock.text
        # But we need to ensure no more than one text block is returned
        if (
            len([block for block in claude_response.content if block.type == "text"])
            > 1
        ):
            raise ApplicationError("Claude should only return one message")

        text_block = next(
            (block for block in claude_response.content if block.type == "text"),
            None,
        )

        stop_reason = claude_response.stop_reason

        if stop_reason == "tool_use":
            choice = Choices(
                message=Message(
                    role="assistant",
                    content=text_block.text if text_block else None,
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            type="function",
                            function=Function(
                                name=block.name,
                                arguments=block.input,
                            ),
                        )
                        for block in claude_response.content
                        if block.type == "tool_use"
                    ],
                ),
                finish_reason="tool_calls",
            )
        else:
            assert (
                text_block
            ), "Claude should always return a text block for stop_reason=stop"

            choice = Choices(
                message=Message(
                    role="assistant",
                    content=text_block.text,
                ),
                finish_reason="stop",
            )

        response: ModelResponse = ModelResponse(
            id=claude_response.id,
            choices=[choice],
            created=int(datetime.now().timestamp()),
            model=claude_response.model,
            object="text_completion",
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
        output=response.model_dump() if hasattr(response, "model_dump") else response,
        next=None,
    )
