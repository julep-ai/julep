from beartype import beartype
from litellm.types.utils import Function
from temporalio import activity
from temporalio.exceptions import ApplicationError

from ...autogen.Tools import ApiCallDef, Tool
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
                        k.rstrip("_"): getattr(tool.api_call, k)
                        for k in ApiCallDef.model_fields.keys()
                    },
                },
            }
        )
    elif tool.system:
        parameters = {
            "resource_id": tool.system.resource_id,
            "subresource": tool.system.subresource,
        }
        if tool.system.arguments:
            parameters.update({"arguments": tool.system.arguments})

        result.update(
            {
                "function": {
                    "name": f"{tool.system.resource}.{tool.system.operation}",
                    "description": f"{tool.system.operation} a {tool.system.resource}",
                    "parameters": parameters,
                }
            }
        )
    elif tool.integration:
        parameters = {}
        if tool.integration.method:
            parameters.update({"method": tool.integration.method})
        if tool.integration.setup:
            parameters.update({"setup": tool.integration.setup})
        if tool.integration.arguments:
            parameters.update({"arguments": tool.integration.arguments})

        result.update(
            {
                "function": {
                    "name": tool.name,
                    "description": f"{tool.integration.provider} integration",
                    "parameters": parameters,
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

    ### [Function(...), ApiCall(...), Integration(...)]
    ### -> [{"type": "function", "function": {...}}, {"type": "api_call", "api_call": {...}}, {"type": "integration", "integration": {...}}]
    ### -> [{"type": "function", "function": {...}}]
    ### -> openai

    # Format agent_tools for litellm
    # COMMENT(oct-16): Format the tools for openai api here (api_call | integration | system) -> function
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
        choice.message.tool_calls = [
            call if isinstance(tc.function, dict) else tc.function.name
            for tc in choice.message.tool_calls
            if (
                call := (
                    tools_mapping.get(
                        tc.function["name"]
                        if isinstance(tc.function, dict)
                        else tc.function.name
                    )
                )
            )
        ]

    ### response.choices[0].finish_reason == "tool_calls"
    ### -> response.choices[0].message.tool_calls
    ### -> [{"id": "call_abc", "name": "my_function", "arguments": "..."}, ...]
    ###    (cross-reference with original agent_tools list to get the original tool)
    ###
    ### -> FunctionCall(...) | ApiCall(...) | IntegrationCall(...) | SystemCall(...)
    ### -> set this on response.choices[0].tool_calls

    # COMMENT(oct-16): Reference the original tool from tools passed to the activity
    #                  if openai chooses to use a tool (finish_reason == "tool_calls")

    return StepOutcome(
        output=response.model_dump() if hasattr(response, "model_dump") else response,
        next=None,
    )
