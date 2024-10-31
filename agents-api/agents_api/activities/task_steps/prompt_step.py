from datetime import datetime

from anthropic import AsyncAnthropic  # Import AsyncAnthropic client
from anthropic.types.beta.beta_message import BetaMessage
from beartype import beartype
from langchain_core.tools import BaseTool
from langchain_core.tools.convert import tool as tool_decorator
from litellm import ChatCompletionMessageToolCall, Function, Message
from litellm.types.utils import Choices, ModelResponse
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
from ..utils import get_handler

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


def format_tool(tool: Tool) -> dict:
    if tool.type == "computer_20241022":
        return {
            "type": tool.type,
            "name": tool.name,
            "display_width_px": tool.computer_20241022
            and tool.computer_20241022.display_width_px,
            "display_height_px": tool.computer_20241022
            and tool.computer_20241022.display_height_px,
            "display_number": tool.computer_20241022
            and tool.computer_20241022.display_number,
        }

    if tool.type in ["bash_20241022", "text_editor_20241022"]:
        return tool.model_dump(include={"type", "name"})

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
    formatted = {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description},
    }

    if tool.type == "system":
        handler = get_handler(tool.system)
        lc_tool: BaseTool = tool_decorator(handler)
        json_schema: dict = lc_tool.get_input_jsonschema()

        formatted["function"]["description"] = formatted["function"][
            "description"
        ] or json_schema.get("description")

        formatted["function"]["parameters"] = json_schema

    # FIXME: Implement integration tools
    elif tool.type == "integration":
        raise NotImplementedError("Integration tools are not supported")

    # FIXME: Implement API call tools
    elif tool.type == "api_call":
        raise NotImplementedError("API call tools are not supported")

    return formatted


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

    if context.current_step.settings:
        passed_settings: dict = context.current_step.settings.model_dump(
            exclude_unset=True
        )
    else:
        passed_settings: dict = {}

    # Wrap the prompt in a list if it is not already
    if isinstance(prompt, str):
        prompt = [{"role": "user", "content": prompt}]

    # Format tools for litellm
    formatted_tools = [format_tool(tool) for tool in context.tools]

    # Map tools to their original objects
    tools_mapping: dict[str, Tool] = {
        fmt_tool.get("name") or fmt_tool.get("function", {}).get("name"): orig_tool
        for fmt_tool, orig_tool in zip(formatted_tools, context.tools)
    }

    # Check if the model is Anthropic
    if agent_model.lower().startswith("claude-3.5") and any(
        tool["type"] in ["computer_20241022", "bash_20241022", "text_editor_20241022"]
        for tool in formatted_tools
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
            tools=formatted_tools,
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
            "tools": formatted_tools or None,
            "messages": prompt,
            **agent_default_settings,
            **passed_settings,
        }

        extra_body = {
            "cache": {"no-cache": debug},
        }

        response: ModelResponse = await litellm.acompletion(
            **completion_data,
            extra_body=extra_body,
        )

    if context.current_step.unwrap:
        if len(response.choices) != 1:
            raise ApplicationError("Only one choice is supported")

        choice = response.choices[0]
        if choice.finish_reason == "tool_calls":
            raise ApplicationError("Tool calls cannot be unwrapped")

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
                    raise ApplicationError(f"Tool {call_name} not found")

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
