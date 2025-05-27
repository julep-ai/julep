from typing import Annotated, Any
from uuid import UUID

from fastapi import BackgroundTasks, Depends, Header
from starlette.status import HTTP_201_CREATED
from uuid_extensions import uuid7

from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
    ChunkChatResponse,
    CreateEntryRequest,
    MessageChatResponse,
)
from ...common.protocol.developers import Developer
from ...common.utils.datetime import utcnow
from ...common.utils.tool_runner import run_session_llm_with_tools
from ...dependencies.developer_id import get_developer_data
from ...queries.entries.create_entries import create_entries
from .metrics import total_tokens_per_user
from .render import render_chat_input
from .router import router

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


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
    x_custom_api_key: str | None = Header(None, alias="X-Custom-Api-Key"),
    connection_pool: Any = None,  # FIXME: Placeholder that should be removed
) -> ChatResponse:
    """
    Initiates a chat session.

    Parameters:
        developer (Developer): The developer associated with the chat session.
        session_id (UUID): The unique identifier of the chat session.
        chat_input (ChatInput): The chat input data.
        background_tasks (BackgroundTasks): The background tasks to run.
        x_custom_api_key (Optional[str]): The custom API key.

    Returns:
        ChatResponse: The chat response.
    """
    (
        messages,
        doc_references,
        _formatted_tools,
        tools,
        settings,
        new_messages,
        chat_context,
    ) = await render_chat_input(
        developer=developer,
        session_id=session_id,
        chat_input=chat_input,
    )

    # Prepare parameters for the LLM call
    params = {
        "user": str(developer.id),
        "tags": developer.tags,
        "custom_api_key": x_custom_api_key,
    }
    payload = {**settings, **params}

    messages, model_response = await run_session_llm_with_tools(
        developer_id=developer.id,
        messages=messages,
        tools=tools,
        settings=payload,
    )

    # Save the input and the response to the session history
    if chat_input.save:
        new_entries = [
            CreateEntryRequest.from_model_input(
                model=settings["model"],
                **msg,
                source="api_request",
            )
            for msg in new_messages
        ]

        # Add the response to the new entries
        # FIXME: We need to save all the choices
        new_entries.append(
            CreateEntryRequest.from_model_input(
                model=settings["model"],
                **model_response.choices[0].model_dump()["message"],
                source="api_response",
            ),
        )
        background_tasks.add_task(
            create_entries,
            developer_id=developer.id,
            session_id=session_id,
            data=new_entries,
        )

    # Adaptive context handling
    jobs = []
    if chat_context.session.context_overflow == "adaptive":
        # FIXME: Start the adaptive context workflow
        # SCRUM-8

        # jobs = [await start_adaptive_context_workflow]
        msg = "Adaptive context is not yet implemented"
        raise NotImplementedError(msg)

    # Return the response
    # FIXME: Implement streaming for chat
    chat_response_class = ChunkChatResponse if chat_input.stream else MessageChatResponse

    chat_response: ChatResponse = chat_response_class(
        id=uuid7(),
        created_at=utcnow(),
        jobs=jobs,
        docs=doc_references,
        usage=model_response.usage.model_dump(),
        choices=[choice.model_dump() for choice in model_response.choices],
    )

    total_tokens_per_user.labels(str(developer.id)).inc(
        amount=chat_response.usage.total_tokens if chat_response.usage is not None else 0,
    )

    return chat_response
