from typing import Annotated
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, Depends
from litellm.types.utils import ModelResponse
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
    ChunkChatResponse,
    CreateEntryRequest,
    MessageChatResponse,
)
from ...clients import litellm
from ...clients.temporal import run_summarization_task, run_truncation_task
from ...common.protocol.developers import Developer
from ...common.protocol.sessions import ChatContext
from ...common.utils.datetime import utcnow
from ...common.utils.template import render_template
from ...dependencies.developer_id import get_developer_data
from ...exceptions import PromptTooBigError
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
    if chat_input.stream:
        raise NotImplementedError("Streaming is not yet implemented")

    # First get the chat context
    chat_context: ChatContext = prepare_chat_context(
        developer_id=developer.id,
        session_id=session_id,
    )

    # Merge the settings and prepare environment
    chat_context.merge_settings(chat_input)
    settings: dict = chat_context.settings.model_dump()
    settings["model"] = f"openai/{settings['model']}"  # litellm proxy idiosyncracy

    # Get the past messages and doc references
    past_messages, doc_references = await gather_messages(
        developer=developer,
        session_id=session_id,
        chat_context=chat_context,
        chat_input=chat_input,
    )

    # Prepare the environment
    env: dict = chat_context.get_chat_environment()
    env["docs"] = doc_references

    # Render the system message
    if situation := chat_context.session.situation:
        system_message = dict(
            role="system",
            content=situation,
        )

        system_messages: list[dict] = await render_template(
            [system_message], variables=env
        )
        past_messages = system_messages + past_messages

    # Render the incoming messages
    new_raw_messages = [msg.model_dump() for msg in chat_input.messages]

    if chat_context.session.render_templates:
        new_messages = await render_template(new_raw_messages, variables=env)
    else:
        new_messages = new_raw_messages

    # Combine the past messages with the new messages
    messages = past_messages + new_messages

    # Get the tools
    tools = settings.get("tools") or chat_context.get_active_tools()

    # Get the response from the model
    model_response = await litellm.acompletion(
        messages=messages,
        tools=tools or None,
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

        # Add the response to the new entries
        new_entries.append(
            CreateEntryRequest.from_model_input(
                model=settings["model"],
                **model_response.choices[0].model_dump()["message"],
                source="api_response",
            )
        )
        background_tasks.add_task(
            create_entries,
            developer_id=developer.id,
            session_id=session_id,
            data=new_entries,
            mark_session_as_updated=True,
        )

    # Adaptive context handling
    job_id = uuid4()
    if chat_context.session.context_overflow == "adaptive":
        await run_summarization_task(session_id=session_id, job_id=job_id)
    elif chat_context.session.context_overflow == "truncate":
        await run_truncation_task(
            token_count_threshold=chat_context.session.token_budget,
            developer_id=developer.id,
            session_id=session_id,
            job_id=job_id,
        )
    else:
        # TODO: set this valur for a streaming response
        total_tokens = 0
        if isinstance(model_response, ModelResponse):
            total_tokens = model_response.usage.total_tokens

        raise PromptTooBigError(total_tokens, chat_context.session.token_budget)

    # Return the response
    # FIXME: Implement streaming for chat
    chat_response_class = (
        ChunkChatResponse if chat_input.stream else MessageChatResponse
    )
    chat_response: ChatResponse = chat_response_class(
        id=uuid4(),
        created_at=utcnow(),
        jobs=[job_id],
        docs=doc_references,
        usage=model_response.usage.model_dump(),
        choices=[choice.model_dump() for choice in model_response.choices],
    )

    return chat_response
