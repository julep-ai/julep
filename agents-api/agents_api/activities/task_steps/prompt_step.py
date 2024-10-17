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
from ...env import debug
from ...models.tools.list_tools import list_tools


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
                                "type": "bool",
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

    return result if result.get("function") else None


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

    completion_data: dict = {
        "model": agent_model,
        "tools": formatted_agent_tools or None,
        "messages": prompt,
        **agent_default_settings,
        **passed_settings,
    }

    extra_body = {  # OpenAI python accepts extra args in extra_body
        "cache": {"no-cache": debug},  # will not return a cached response
    }

    response = await litellm.acompletion(
        **completion_data,
        extra_body=extra_body,
    )

    choice = response.choices[0]
    if context.current_step.unwrap:
        if choice.finish_reason == "tool_calls":
            raise ApplicationError("Tool calls cannot be unwrapped")

        response = choice.message.content

    if choice.finish_reason == "tool_calls":
        tc = choice.message.tool_calls[0]
        choice.message.tool_calls = tools_mapping.get(
            tc.function["name"] if isinstance(tc.function, dict) else tc.function.name
        )

    return StepOutcome(
        output=response.model_dump() if hasattr(response, "model_dump") else response,
        next=None,
    )
