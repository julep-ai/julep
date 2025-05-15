import json
from collections.abc import AsyncGenerator
from typing import Annotated, Any
from uuid import UUID

from fastapi import BackgroundTasks, Depends, Header
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_201_CREATED
from uuid_extensions import uuid7

from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
    ChunkChatResponse,
    CreateEntryRequest,
    MessageChatResponse,
)
from ...clients import litellm
from ...common.protocol.developers import Developer
from ...common.utils.datetime import utcnow
from ...dependencies.developer_id import get_developer_data
from ...queries.entries.create_entries import create_entries
from .metrics import total_tokens_per_user
from .render import render_chat_input
from .router import router

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


def with_mock_response(r: str | None = None):
    def wrapper():
        return r

    return wrapper


async def stream_chat_response(
    model_response: litellm.CustomStreamWrapper,
    developer_id: UUID,
    doc_references: list[Any],
    should_save: bool = False,
    session_id: UUID | None = None,
    model: str = "",
    background_tasks: BackgroundTasks | None = None,
) -> AsyncGenerator[str, None]:
    """
    Streams the chat response as Server-Sent Events.

    Args:
        model_response: The streaming model response from LiteLLM
        developer_id: The developer ID for usage tracking
        doc_references: Document references to include in the response
        should_save: Whether to save the response to history
        session_id: The session ID for saving response
        model: The model name used for the response
        background_tasks: Background tasks for saving responses
    """
    # Variables to collect the complete response for saving to history if needed
    collected_content = ""
    role = "assistant"

    # Usage information will be collected from the stream response
    usage_data = None

    # Send initial metadata
    response_id = uuid7()
    created_time = utcnow()
    metadata = {
        "id": str(response_id),
        "created_at": created_time.isoformat(),
        "docs": doc_references,
        "jobs": [],
        "usage": None,
    }
    yield f"data: {json.dumps(metadata)}\n\n"

    # Process all chunks
    async for chunk in model_response:
        # Check if this chunk contains usage data
        if hasattr(chunk, "usage") and chunk.usage:
            usage_data = chunk.usage.model_dump()

        # Collect content for saving if needed
        if should_save and chunk.choices:
            for choice in chunk.choices:
                if hasattr(choice, "delta") and choice.delta:
                    # Add content if it exists
                    if choice.delta.content:
                        collected_content += choice.delta.content

                    # Update role if provided
                    if hasattr(choice.delta, "role") and choice.delta.role:
                        role = choice.delta.role

        # Clean up the chunk's delta content to avoid None values
        if chunk.choices:
            for choice in chunk.choices:
                # Ensure content is never None in the JSON output
                if hasattr(choice, "delta") and (
                    hasattr(choice.delta, "content") and choice.delta.content is None
                ):
                    choice.delta.content = ""

        # Forward the chunk
        chunk_data = {
            "choices": [choice.model_dump() for choice in chunk.choices],
        }
        yield f"data: {json.dumps(chunk_data)}\n\n"

    # Check if the model_response object itself has the usage information
    if not usage_data and hasattr(model_response, "usage") and model_response.usage:
        usage_data = model_response.usage.model_dump()

    # Send usage info if available
    if usage_data:
        yield f"data: {json.dumps({'usage': usage_data})}\n\n"

        # Track token usage
        total_tokens = usage_data.get("total_tokens", 0)
        if total_tokens > 0:
            total_tokens_per_user.labels(str(developer_id)).inc(amount=total_tokens)

    # Save the complete response if requested
    if should_save and session_id and background_tasks and collected_content:
        response_entry = CreateEntryRequest.from_model_input(
            model=model,
            role=role,
            content=collected_content,
            source="api_response",
        )

        background_tasks.add_task(
            create_entries,
            developer_id=developer_id,
            session_id=session_id,
            data=[response_entry],
        )

    # Send done event
    yield "data: [DONE]\n\n"


@router.post(
    "/sessions/{session_id}/chat",
    status_code=HTTP_201_CREATED,
    tags=["sessions", "chat"],
    response_model=ChatResponse,
)
async def chat(
    developer: Annotated[Developer, Depends(get_developer_data)],
    session_id: UUID,
    chat_input: ChatInput,
    background_tasks: BackgroundTasks,
    x_custom_api_key: Annotated[str | None, Header(alias="X-Custom-Api-Key")] = None,
    mock_response: Annotated[str | None, Depends(with_mock_response())] = None,
    connection_pool: Any = None,  # FIXME: Placeholder that should be removed
) -> Any:
    """
    Initiates a chat session.

    Parameters:
        developer (Developer): The developer associated with the chat session.
        session_id (UUID): The unique identifier of the chat session.
        chat_input (ChatInput): The chat input data.
        background_tasks (BackgroundTasks): The background tasks to run.
        x_custom_api_key (Optional[str]): The custom API key.

    Returns:
        ChatResponse or StreamingResponse: The chat response or streaming response.
    """
    (
        messages,
        doc_references,
        formatted_tools,
        settings,
        new_messages,
        chat_context,
    ) = await render_chat_input(
        developer=developer,
        session_id=session_id,
        chat_input=chat_input,
    )

    # Prepare parameters for LiteLLM
    params = {
        "messages": messages,
        "tools": formatted_tools or None,
        "user": str(developer.id),
        "tags": developer.tags,
        "custom_api_key": x_custom_api_key,
    }

    # Set streaming parameter based on chat_input.stream
    if chat_input.stream:
        params["stream"] = True
        params["stream_options"] = {"include_usage": True}

    payload = {**settings, **params, "mock_response": mock_response}

    # Get response from LiteLLM (streaming or non-streaming)
    model_response = await litellm.acompletion(**payload)

    # Save the input messages to the session history if requested
    if chat_input.save:
        new_entries = [
            CreateEntryRequest.from_model_input(
                model=settings["model"],
                **msg,
                source="api_request",
            )
            for msg in new_messages
        ]

        # For non-streaming, save the response immediately
        if not chat_input.stream:
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

    # Handle streaming response
    if chat_input.stream:
        # Return streaming response using the unified function
        return StreamingResponse(
            stream_chat_response(
                model_response=model_response,
                developer_id=developer.id,
                doc_references=doc_references,
                should_save=chat_input.save,
                session_id=session_id if chat_input.save else None,
                model=settings["model"],
                background_tasks=background_tasks if chat_input.save else None,
            ),
            media_type="text/event-stream",
        )

    # Handle non-streaming response
    # Adaptive context handling
    jobs = []
    if chat_context.session.context_overflow == "adaptive":
        # FIXME: Start the adaptive context workflow
        # SCRUM-8
        msg = "Adaptive context is not yet implemented"
        raise NotImplementedError(msg)

    # Return the regular response
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
