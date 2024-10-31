import os
from datetime import datetime

from anthropic import Anthropic
from anthropic.types.beta.beta_message import BetaMessage
from beartype import beartype
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
from ...models.tools.list_tools import list_tools

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


def make_function_call(tool: Tool) -> dict | None:
    result = {"type": "function"}

    if tool.function:
        result.update(
            {
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.function.parameters,
                },
            }
        )
    elif tool.api_call:
        result.update(
            {
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "method": {
                                "type": "string",
                                "description": "The HTTP method to use",
                            },
                            "url": {
                                "type": "string",
                                "description": "The URL to call",
                            },
                            "headers": {
                                "type": "object",
                                "description": "The headers to send with the request",
                            },
                            "content": {
                                "type": "string",
                                "description": "The content as base64 to send with the request",
                            },
                            "data": {
                                "type": "object",
                                "description": "The data to send as form data",
                            },
                            "json": {
                                "type": "object",
                                "description": "JSON body to send with the request",
                            },
                            "cookies": {
                                "type": "object",
                                "description": "Cookies",
                            },
                            "params": {
                                "type": "object",
                                "description": "The parameters to send with the request",
                            },
                            "follow_redirects": {
                                "type": "boolean",
                                "description": "Follow redirects",
                            },
                            "timeout": {
                                "type": "int",
                                "description": "The timeout for the request",
                            },
                        },
                        "required": ["method", "url"],
                        "additionalProperties": False,
                    },
                },
            }
        )
    elif tool.system:
        result.update(
            {
                "function": {
                    "name": f"{tool.system.resource}.{tool.system.operation}",
                    "description": f"{tool.system.operation} a {tool.system.resource}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "resource": {
                                "type": "string",
                                "description": "Resource is the name of the resource to use, one of: agent, user, task, execution, doc, session, job",
                            },
                            "operation": {
                                "type": "string",
                                "description": "Operation is the name of the operation to perform, one of: create, update, patch, create_or_update, embed, change_status, search, chat, history, delete, get, list",
                            },
                            "resource_id": {
                                "type": "string",
                                "description": "Resource id",
                            },
                            "subresource": {
                                "type": "string",
                                "description": "Sub-resource type, one of: tool, doc, execution, transition",
                            },
                            "arguments": {
                                "type": "object",
                                "description": "The arguments to pre-apply to the system call",
                            },
                        },
                        "required": ["resource", "operation"],
                        "additionalProperties": False,
                    },
                }
            }
        )
    elif tool.integration:
        result.update(
            {
                "function": {
                    "name": tool.name,
                    "description": f"{tool.integration.provider} integration",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "description": "The provider of the integration",
                            },
                            "method": {
                                "type": "string",
                                "description": "The specific method of the integration to call",
                            },
                            "setup": {
                                "type": "object",
                                "description": "The setup parameters the integration accepts",
                            },
                            "arguments": {
                                "type": "object",
                                "description": "The arguments to pre-apply to the integration call",
                            },
                        },
                        "required": ["provider"],
                        "additionalProperties": False,
                    },
                }
            }
        )

    elif tool.computer_20241022:
        return {
            "type": tool.type,
            "name": tool.name,
            "display_width_px": tool.computer_20241022.display_width_px,
            "display_height_px": tool.computer_20241022.display_height_px,
            "display_number": tool.computer_20241022.display_number,
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
    else:
        raise ValueError(f"Unsupported tool: {tool}")

    return result


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

    formatted_agent_tools = [
        func_call for tool in agent_tools if (func_call := make_function_call(tool))
    ]
    tools_mapping = {
        fmt_tool["function"]["name"]: orig_tool
        for fmt_tool, orig_tool in zip(formatted_agent_tools, agent_tools)
    }

    if context.current_step.settings:
        passed_settings: dict = context.current_step.settings.model_dump(
            exclude_unset=True
        )
    else:
        passed_settings: dict = {}

    # Wrap the prompt in a list if it is not already
    if isinstance(prompt, str):
        prompt = [{"role": "user", "content": prompt}]

    # Check if the model is Anthropic and bash/editor/computer use tool is included
    if "claude" in agent_model.lower() and any(
        tool.type in ["bash_20241022", "text_editor_20241022", "computer_20241022"]
        for tool in agent_tools
    ):
        # Retrieve the API key from the environment variable
        betas = [COMPUTER_USE_BETA_FLAG]
        # Use Anthropic API directly
        client = Anthropic(api_key=anthropic_api_key)

        # Claude Response
        claude_response: BetaMessage = await client.beta.messages.create(
            model=agent_model,
            messages=prompt,
            tools=formatted_agent_tools,
            max_tokens=1024,
            betas=betas,
        )

        # FIXME: Handle multiple messages
        if len(claude_response.content) != 1:
            raise ApplicationError("Claude should only return one message")

        content_block = claude_response.content[0]
        stop_reason = claude_response.stop_reason

        if stop_reason == "tool_use":
            choice = Choices(
                message=Message(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            type="function",
                            function=Function(
                                name=content_block.name,
                                arguments=content_block.input,
                            ),
                        )
                    ],
                ),
                finish_reason="tool_calls",
            )
        else:
            choice = Choices(
                message=Message(
                    role="assistant",
                    content=content_block.text,
                ),
                finish_reason="stop",
            )

        response: ModelResponse = ModelResponse(
            id=claude_response.id,
            choices=[choice],
            created=datetime.now().timestamp(),
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
