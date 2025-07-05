from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from ....autogen.openapi_model import (
    ChatInput,
    DocReference,
    RenderResponse,
)
from ....common.protocol.developers import Developer
from ....common.protocol.sessions import ChatContext
from ....common.utils.expressions import evaluate_expressions
from ....common.utils.template import render_template
from ....dependencies.developer_id import get_developer_data
from ....env import max_free_sessions
from ....queries.chat.gather_messages import gather_messages
from ....queries.chat.prepare_chat_context import prepare_chat_context
from ....queries.secrets.list import list_secrets_query
from ....queries.sessions.count_sessions import count_sessions as count_sessions_query

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


async def render(
    developer: Annotated[Developer, Depends(get_developer_data)],
    session_id: UUID,
    chat_input: ChatInput,
) -> RenderResponse:
    """
    Renders a chat input.

    Parameters:
        developer (Developer): The developer associated with the chat session.
        session_id (UUID): The unique identifier of the chat session.
        chat_input (ChatInput): The chat input data.

    Returns:
        RenderResponse: The rendered chat input.
    """

    messages, doc_references, tools, *_ = await render_chat_input(
        developer=developer,
        session_id=session_id,
        chat_input=chat_input,
    )

    return RenderResponse(messages=messages, docs=doc_references, tools=tools)


async def render_chat_input(
    developer: Developer,
    session_id: UUID,
    chat_input: ChatInput,
) -> tuple[list[dict], list[DocReference], list[dict] | None, dict, list[dict], ChatContext]:
    # check if the developer is paid
    if "paid" not in developer.tags:
        # get the session length
        sessions = await count_sessions_query(developer_id=developer.id)
        session_length = sessions["count"]
        if session_length > max_free_sessions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session length exceeded the free tier limit",
            )

    # First get the chat context
    chat_context: ChatContext = await prepare_chat_context(
        developer_id=developer.id,
        session_id=session_id,
    )

    # Merge the settings and prepare environment
    chat_context.merge_settings(chat_input)
    settings: dict = chat_context.settings or {}

    # await validate_model(settings.get("model")) # Note: temporarily disabled

    # Get the past messages and doc references
    past_messages, doc_references = await gather_messages(
        developer=developer,
        session_id=session_id,
        chat_context=chat_context,
        chat_input=chat_input,
    )

    # Prepare the environment
    env: dict = chat_context.get_chat_environment()
    env["docs"] = [
        {
            "title": ref.title,
            "content": [ref.snippet.content],
            "metadata": ref.metadata or None,
        }
        for ref in doc_references
    ]

    # Add metadata from chat_input to the environment
    # AIDEV-NOTE: metadata field enables dynamic instructions at message level via system template
    if hasattr(chat_input, "metadata") and chat_input.metadata:
        env["metadata"] = chat_input.metadata

    # Render the system message
    if system_template := chat_context.merge_system_template(
        chat_context.session.system_template,
    ):
        system_message = {
            "role": "system",
            "content": system_template,
        }
        system_messages: list[dict] = await render_template([system_message], variables=env)
        past_messages = system_messages + past_messages

    # Render the incoming messages
    new_raw_messages = [msg.model_dump(mode="json") for msg in chat_input.messages]

    if chat_context.session.render_templates:
        new_messages = await render_template(new_raw_messages, variables=env)
    else:
        new_messages = new_raw_messages

    # Combine the past messages with the new messages
    messages = past_messages + new_messages

    # Get the agent tools
    tools = chat_context.get_active_tools()
    # If the user has provided tools, add them to the tools, but only if they are not already in the tools
    if chat_input.tools:
        existing_tool_names = {tool.name for tool in tools}
        for tool in chat_input.tools:
            if tool.name not in existing_tool_names:
                tools.append(tool)

    # Check if using Claude model and has specific tool types
    is_claude_model = settings.get("model", "").lower().startswith("claude-3.5")

    # Format tools for litellm
    # formatted_tools = (
    #     tools if is_claude_model else [format_tool(tool) for tool in tools]
    # )

    # FIXME: Truncate chat messages in the chat context
    # SCRUM-7
    if chat_context.session.context_overflow == "truncate":
        # messages = messages[-settings["max_tokens"] :]
        msg = "Truncation is not yet implemented"
        raise NotImplementedError(msg)

    # FIXME: Hotfix for datetime not serializable. Needs investigation
    messages = [
        {
            k: v
            for k, v in m.items()
            if k in ["role", "content", "tool_calls", "tool_call_id", "user"]
        }
        for m in messages
    ]

    # FIXME: Hack to make the computer use tools compatible with litellm
    # Issue was: litellm expects type to be `computer_20241022` and spec to be
    # `function` (see: https://docs.litellm.ai/docs/providers/anthropic#computer-tools)
    # but we don't allow that (spec should match type).
    formatted_tools = []
    secrets = {}
    if tools and any(
        tool.type == "computer_20241022" and tool.computer_20241022 for tool in tools
    ):
        secrets = {
            secret.name: secret.value
            for secret in await list_secrets_query(
                developer_id=developer.id,
                decrypt=True,
            )
        }

    for tool in tools:
        if tool.type == "computer_20241022" and tool.computer_20241022:
            function = tool.computer_20241022
            tool = {
                "type": tool.type,
                "function": {
                    "name": tool.name,
                    "parameters": {
                        k: evaluate_expressions(v, values={"secrets": secrets})
                        for k, v in function.model_dump().items()
                        if k not in ["name", "type"]
                    }
                    if function is not None
                    else {},
                },
            }
            formatted_tools.append(tool)

    # If not using Claude model
    # FIXME: Enable formatted_tools once format-tools PR is merged.
    if not is_claude_model:
        formatted_tools = None

    # HOTFIX: for groq calls, litellm expects tool_calls_id not to be in the messages
    # FIXME: This is a temporary fix. We need to update the agent-api to use the new tool calling format
    is_groq_model = settings.get("model", "").lower().startswith("llama-3.1")
    if is_groq_model:
        messages = [
            {
                k: v
                for k, v in message.items()
                if k not in ["tool_calls", "tool_call_id", "user", "continue_", "name"]
            }
            for message in messages
        ]

    return messages, doc_references, formatted_tools, settings, new_messages, chat_context
