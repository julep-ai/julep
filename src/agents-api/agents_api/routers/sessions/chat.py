from collections.abc import AsyncGenerator
from typing import Annotated, Any
from uuid import UUID

from fastapi import BackgroundTasks, Depends, Header
from fastapi.responses import StreamingResponse
from litellm.utils import ModelResponse
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
from ...common.utils.usage_tracker import track_streaming_usage
from ...dependencies.developer_id import get_developer_data
from ...queries.entries.create_entries import create_entries
from .render import render_chat_input
from .router import router

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


def with_mock_response(r: str | None = None):
    def wrapper():
        return r

    return wrapper


def _join_deltas(acc: dict, delta: dict) -> dict:
    acc["content"] = (acc.get("content", "") or "") + (delta.pop("content", "") or "")
    return {**acc, **delta}


async def stream_chat_response(
    model_response: litellm.CustomStreamWrapper,
    developer_id: UUID,
    doc_references: list[Any],
    should_save: bool = False,
    session_id: UUID | None = None,
    model: str = "",
    background_tasks: BackgroundTasks | None = None,
    messages: list[dict] | None = None,
    custom_api_key_used: bool = False,
    developer_tags: list[str] | None = None,
    connection_pool: Any = None,  # This is for testing purposes
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
        messages: The original messages sent to the model (for usage tracking)
        custom_api_key_used: Whether a custom API key was used
        developer_tags: Tags associated with the developer (for metadata)
        connection_pool: Connection pool for testing purposes
    """
    collected_output = []
    # Variables to collect the complete response for saving to history if needed
    default_role = "assistant"
    default_finish_reason = "stop"

    # Usage information will be collected from the stream response
    usage_data = None

    # Create initial response with metadata
    response_id = uuid7()
    created_time = utcnow()

    # Process all chunks
    async for chunk in model_response:
        if not collected_output:
            collected_output = [{} for _ in range(len(chunk.choices or []))]

        collected_output = [
            _join_deltas(acc, choice.delta.model_dump())
            for acc, choice in zip(collected_output, chunk.choices)
        ]

        # Check if this chunk contains usage data
        if hasattr(chunk, "usage") and chunk.usage:
            usage_data = chunk.usage.model_dump()

        # Create a proper ChunkChatResponse for each chunk
        chunk_response = ChunkChatResponse(
            id=response_id,
            created_at=created_time,
            docs=doc_references,
            jobs=[],
            usage=usage_data,
            choices=[
                {
                    **choice.model_dump(),
                    "delta": {
                        **choice.delta.model_dump(),
                        "role": choice.delta.role or default_role,
                    },
                    "finish_reason": choice.finish_reason or default_finish_reason,
                }
                for choice in chunk.choices
            ],
        )

        # Forward the chunk as a proper ChunkChatResponse
        yield f"data: {chunk_response.model_dump_json()}\n\n"

    # Track usage using centralized tracker
    await track_streaming_usage(
        developer_id=developer_id,
        model=model,
        messages=messages or [],
        usage_data=usage_data,
        collected_output=collected_output,
        response_id=str(response_id),
        custom_api_used=custom_api_key_used,
        metadata={
            "tags": developer_tags or [],
            "streaming": True,
        },
        connection_pool=connection_pool,
    )

    # Save the complete response if requested
    if should_save:
        background_tasks.add_task(
            create_entries,
            developer_id=developer_id,
            session_id=session_id,
            data=[
                CreateEntryRequest.from_model_input(
                    model=model,
                    **{
                        **choice,
                        "role": choice.get("role", default_role) or default_role,
                        "finish_reason": choice.get("finish_reason", default_finish_reason)
                        or default_finish_reason,
                    },
                    source="api_response",
                )
                for choice in collected_output
            ],
        )


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
    connection_pool: Any = None,  # This is for testing purposes
) -> MessageChatResponse | StreamingResponse:
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
                session_id=session_id,
                model=settings["model"],
                background_tasks=background_tasks,
                messages=messages,
                custom_api_key_used=x_custom_api_key is not None,
                developer_tags=developer.tags,
                connection_pool=connection_pool,
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

    chat_response = MessageChatResponse(
        id=uuid7(),
        created_at=utcnow(),
        jobs=jobs,
        docs=doc_references,
        usage=model_response.usage.model_dump(),
        choices=[choice.model_dump() for choice in model_response.choices],
    )

    return chat_response
