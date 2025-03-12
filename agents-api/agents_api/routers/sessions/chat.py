import asyncio
import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import BackgroundTasks, Depends, Header
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
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


async def wait_for_tasks(tasks: list[asyncio.Task]) -> None:
    """Wait for all background tasks to complete."""
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


@router.post(
    "/sessions/{session_id}/chat",
    status_code=HTTP_201_CREATED,
    tags=["sessions", "chat"],
    response_model=None,
)
async def chat(
    developer: Annotated[Developer, Depends(get_developer_data)],
    session_id: UUID,
    chat_input: ChatInput,
    background_tasks: BackgroundTasks,
    x_custom_api_key: str | None = Header(None, alias="X-Custom-Api-Key"),
    connection_pool: Any = None,  # FIXME: Placeholder that should be removed
) -> ChatResponse | StreamingResponse:  # FIXME: Update type to include StreamingResponse
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
        formatted_tools,
        settings,
        new_messages,
        chat_context,
    ) = await render_chat_input(
        developer=developer,
        session_id=session_id,
        chat_input=chat_input,
    )

    # Use litellm for other models
    params = {
        "messages": messages,
        "tools": formatted_tools or None,
        "user": str(developer.id),
        "tags": developer.tags,
        "custom_api_key": x_custom_api_key,
        "stream": chat_input.stream,  # Enable streaming if requested
    }
    payload = {**settings, **params}

    try:
        model_response = await litellm.acompletion(**payload)
    except Exception as e:
        import logging

        logging.error(f"LLM completion error: {e!s}")
        # Create basic error response
        return ChatResponse(
            id=uuid7(),
            created_at=utcnow(),
            jobs=[],
            docs=doc_references,
            usage=None,
            choices=[],
            error=f"Error getting model completion: {e!s}",
        )

    # Save the input messages to the session history
    if chat_input.save:
        new_entries = [
            CreateEntryRequest.from_model_input(
                model=settings["model"],
                **msg,
                source="api_request",
            )
            for msg in new_messages
        ]

        # For non-streaming responses, add the response to the new entries immediately
        if not chat_input.stream:
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
        else:
            # For streaming, we need to collect all chunks and save at the end
            # For now, just save the input messages and handle response separately
            background_tasks.add_task(
                create_entries,
                developer_id=developer.id,
                session_id=session_id,
                data=new_entries,
            )
            # The complete streamed response will be saved in the stream_chat_response function
            # using a separate background task to avoid blocking the stream

    # Adaptive context handling
    jobs = []
    if chat_context.session.context_overflow == "adaptive":
        # FIXME: Start the adaptive context workflow
        # SCRUM-8

        # jobs = [await start_adaptive_context_workflow]
        msg = "Adaptive context is not yet implemented"
        raise NotImplementedError(msg)

    # Return the response
    # Handle streaming response if requested
    stream_tasks: list[asyncio.Task] = []

    if chat_input.stream:
        # For streaming, we'll use an async generator to yield chunks
        async def stream_chat_response():
            """Stream chat response chunks to the client."""
            # Create initial response with metadata
            response_id = uuid7()
            created_at = utcnow()

            # Collect full response for metrics and optional saving
            content_so_far = ""
            final_usage = None
            has_content = False

            nonlocal stream_tasks

            try:
                # Stream chunks from the model_response (CustomStreamWrapper from litellm)
                async for chunk in model_response:
                    try:
                        # Update usage metrics if available
                        if hasattr(chunk, "usage") and chunk.usage:
                            final_usage = chunk.usage.model_dump()

                        # Check if we have choices and it's a non-empty list
                        has_choices = (
                            hasattr(chunk, "choices")
                            and chunk.choices
                            and len(chunk.choices) > 0
                        )

                        # If this is the last chunk with final usage data, update metrics
                        # Check for finish_reason with a terminal value (completed, length, etc.)
                        if final_usage and has_choices and chunk.choices[0].finish_reason:
                            total_tokens = final_usage.get("total_tokens", 0)
                            total_tokens_per_user.labels(str(developer.id)).inc(
                                amount=total_tokens
                            )

                        # For collecting the full response (optional)
                        if (
                            has_choices
                            and hasattr(chunk.choices[0], "delta")
                            and hasattr(chunk.choices[0].delta, "content")
                            and chunk.choices[0].delta.content
                        ):
                            content_so_far += chunk.choices[0].delta.content
                            has_content = True

                        # Convert litellm chunk to our API format
                        # Only extract choices if they exist
                        choices_to_send = []
                        if has_choices:
                            choices_to_send = [chunk.choices[0].model_dump()]

                        chunk_response = ChunkChatResponse(
                            id=response_id,
                            created_at=created_at,
                            jobs=jobs,
                            docs=doc_references,
                            usage=final_usage,
                            choices=choices_to_send,
                        )
                        # Yield JSON-serialized chunk
                        yield chunk_response.model_dump_json() + "\n"
                    except Exception as e:
                        # Handle errors in processing individual chunks
                        import logging

                        logging.error(f"Error processing chunk: {e!s}")
                        # Create an error chunk response
                        error_response = {
                            "id": str(response_id),
                            "created_at": created_at.isoformat(),
                            "error": "An error occurred while processing the chunk.",
                        }
                        yield json.dumps(error_response) + "\n"
                        # Continue with next chunk rather than crashing the stream
                        continue

                # Save complete response to history if needed
                if chat_input.save and has_content:
                    # FIXME: Implement saving the complete streamed response
                    # We have content_so_far containing the full message
                    # Need to create a CreateEntryRequest and call create_entries
                    # Challenge: This executes after streaming response has started,
                    # so we can't use background_tasks.add_task anymore
                    try:
                        # Create entry for the complete response
                        complete_entry = CreateEntryRequest.from_model_input(
                            model=settings["model"],
                            role="assistant",
                            content=content_so_far,
                            source="api_response",
                        )
                        # Use asyncio.create_task instead of direct await to avoid blocking
                        import asyncio

                        ref = asyncio.create_task(
                            create_entries(
                                developer_id=developer.id,
                                session_id=session_id,
                                data=[complete_entry],
                            )
                        )
                        stream_tasks.append(ref)

                    except Exception as e:
                        import logging

                        logging.error(f"Failed to save complete streamed response: {e!s}")
                        # Handle the error without exposing details to the user
                        error_response = {
                            "id": str(response_id),
                            "created_at": created_at.isoformat(),
                            "error": "An error occurred while saving the streamed response.",
                        }
                        yield json.dumps(error_response) + "\n"
            except Exception as e:
                # Handle errors in the streaming process
                import logging

                logging.error(f"Streaming error: {e!s}")
                error_response = {
                    "id": str(response_id),
                    "created_at": created_at.isoformat(),
                    "error": "An error occurred during streaming.",
                }
                yield json.dumps(error_response) + "\n"

        # Return a streaming response with a background task to wait for all entry saving tasks
        return StreamingResponse(
            stream_chat_response(),
            media_type="application/json",
            background=BackgroundTask(wait_for_tasks, stream_tasks),
        )

    # For non-streaming, return the complete response
    chat_response_class = MessageChatResponse
    chat_response: ChatResponse = chat_response_class(
        id=uuid7(),
        created_at=utcnow(),
        jobs=jobs,
        docs=doc_references,
        usage=model_response.usage.model_dump(),
        choices=[choice.model_dump() for choice in model_response.choices],
    )

    # For non-streaming responses, update metrics and return the response
    if not chat_input.stream:
        total_tokens_per_user.labels(str(developer.id)).inc(
            amount=chat_response.usage.total_tokens if chat_response.usage is not None else 0,
        )
        return chat_response

    # Note: For streaming responses, we've already returned the StreamingResponse above
    # This code is unreachable for streaming responses
    return None
