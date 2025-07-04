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
from ....common.utils.template import render_template
from ....dependencies.developer_id import get_developer_data
from ....env import max_free_sessions
from ....queries.chat.gather_messages import gather_messages
from ....queries.chat.prepare_chat_context import prepare_chat_context
from ....queries.sessions.count_sessions import count_sessions as count_sessions_query
from ...utils.model_validation import validate_model

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

    await validate_model(settings.get("model"))

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

    # AIDEV-NOTE: Return actual Tool objects (unformatted) for auto_tools implementation
    # The auto_tools/chat.py handles tool formatting and execution internally
    return messages, doc_references, tools, settings, new_messages, chat_context
