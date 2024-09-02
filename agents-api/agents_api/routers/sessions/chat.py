from typing import Annotated
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
    ChunkChatResponse,
    CreateEntryRequest,
    MessageChatResponse,
)
from ...clients import litellm
from ...common.protocol.developers import Developer
from ...common.protocol.sessions import ChatContext
from ...common.utils.datetime import utcnow
from ...common.utils.template import render_template
from ...dependencies.developer_id import get_developer_data
from ...models.chat.gather_messages import gather_messages
from ...models.chat.prepare_chat_context import prepare_chat_context
from ...models.entry.create_entries import create_entries
from .router import router


@router.post(
    "/sessions/{session_id}/chat",
    status_code=HTTP_201_CREATED,
    tags=["sessions", "chat"],
)
async def chat(
    developer: Annotated[Developer, Depends(get_developer_data)],
    session_id: UUID,
    chat_input: ChatInput,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    # First get the chat context
    chat_context: ChatContext = prepare_chat_context(
        developer_id=developer.id,
        session_id=session_id,
    )

    # Merge the settings and prepare environment
    chat_context.merge_settings(chat_input)
    settings: dict = chat_context.settings.model_dump()
    env: dict = chat_context.get_chat_environment()
    new_raw_messages = [msg.model_dump() for msg in chat_input.messages]

    # Render the messages
    past_messages, doc_references = await gather_messages(
        developer=developer,
        session_id=session_id,
        chat_context=chat_context,
        chat_input=chat_input,
    )

    env["docs"] = doc_references
    new_messages = await render_template(new_raw_messages, variables=env)
    messages = past_messages + new_messages

    # Get the tools
    tools = settings.get("tools") or chat_context.get_active_tools()

    # FIXME: Truncate the messages if necessary
    if chat_context.session.context_overflow == "truncate":
        # messages = messages[-settings["max_tokens"] :]
        raise NotImplementedError("Truncation is not yet implemented")

    # Get the response from the model
    model_response = await litellm.acompletion(
        messages=messages,
        tools=tools,
        user=str(developer.id),  # For tracking usage
        tags=developer.tags,  # For filtering models in litellm
        **settings,
    )

    # Save the input and the response to the session history
    if chat_input.save:
        new_entries = [
            CreateEntryRequest.from_model_input(
                model=settings["model"], **msg, source="api_request"
            )
            for msg in new_messages
        ]

        background_tasks.add_task(
            create_entries,
            developer_id=developer.id,
            session_id=session_id,
            data=new_entries,
            mark_session_as_updated=True,
        )

    # Adaptive context handling
    jobs = []
    if chat_context.session.context_overflow == "adaptive":
        # FIXME: Start the adaptive context workflow
        # jobs = [await start_adaptive_context_workflow]
        raise NotImplementedError("Adaptive context is not yet implemented")

    # Return the response
    # FIXME: Implement streaming
    chat_response_class = (
        ChunkChatResponse if chat_input.stream else MessageChatResponse
    )
    chat_response: ChatResponse = chat_response_class(
        id=uuid4(),
        created_at=utcnow(),
        jobs=jobs,
        docs=doc_references,
        usage=model_response.usage.model_dump(),
        choices=[choice.model_dump() for choice in model_response.choices],
    )

    return chat_response
