import asyncio
from typing import Annotated, Any

from fastapi import Depends, HTTPException
from fastapi.background import BackgroundTasks
from uuid_extensions import uuid7

from ...activities.tool_executor import execute_tool_call, format_tool_results_for_llm
from ...autogen.openapi_model import (
    ChatResponse,
    ChunkChatResponse,
    CreateEntryRequest,
    CreateResponse,
    FunctionToolCall,
    MessageChatResponse,
    Response,
)
from ...clients import litellm
from ...common.protocol.developers import Developer
from ...common.utils.datetime import utcnow
from ...dependencies.developer_id import get_developer_data
from ...queries.entries.create_entries import create_entries
from ...routers.utils.model_converters import (
    convert_chat_response_to_response,
    convert_create_response,
)
from ...common.utils.usage_tracker import track_completion_usage
from ..sessions.render import render_chat_input
from .router import router


async def process_tool_calls(
    current_messages: list[dict[str, Any]],
    tool_call_requests: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """
    Process any tool calls from the model response, execute them, and prepare
    messages for a follow-up model call if needed.

    Args:
        current_messages: The current message history
        tool_call_requests: The response from the model containing tool calls

    Returns:
        Updated messages with tool results appended
    """
    # Early exit if no tool calls to process
    if not tool_call_requests:
        return current_messages

    # Find the last assistant message with tool_calls
    # This is more efficient than iterating through the entire list
    for i in range(len(current_messages) - 1, -1, -1):
        if current_messages[i].get("role") == "assistant" and current_messages[i].get(
            "tool_calls"
        ):
            break
    else:
        # No assistant message with tool_calls found
        return current_messages

    # Execute all tool calls in parallel
    async def execute_tool_calls_async(tool_call: dict[str, Any]):
        # Execute the tool call
        tool_result = await execute_tool_call(tool_call)
        # Format results for the LLM
        return format_tool_results_for_llm(tool_result)

    # Create and execute tasks for all tool calls at once
    tasks = [execute_tool_calls_async(tool_call) for tool_call in tool_call_requests]
    formatted_results = await asyncio.gather(*tasks)

    # Extend the current messages with all formatted results
    current_messages.extend(formatted_results)

    return current_messages


def is_reasoning_model(model: str) -> bool:
    return model in ["o1", "o1-mini", "o1-preview", "o3-mini"]


@router.post("/responses", tags=["responses"])
async def create_response(
    developer: Annotated[Developer, Depends(get_developer_data)],
    create_response_data: CreateResponse,
    background_tasks: BackgroundTasks,
) -> Response:
    if create_response_data.tools:
        for tool in create_response_data.tools:
            if tool.type == "computer-preview":
                raise HTTPException(
                    status_code=400, detail="Computer preview is not supported yet"
                )

    _agent, session, chat_input = await convert_create_response(
        developer.id,
        create_response_data,
    )
    session_id = session.id
    x_custom_api_key = None
    # Chat function
    (
        messages,
        doc_references,
        _formatted_tools,
        settings,
        new_messages,
        chat_context,
    ) = await render_chat_input(
        developer=developer,
        session_id=session_id,
        chat_input=chat_input,
    )

    if settings.get("stop") == []:
        settings.pop("stop")

    # Prepare tools for the model - pass through tools as is
    tools_list = [tool.model_dump() for tool in chat_input.tools] if chat_input.tools else []

    # top_p is not supported for reasoning models
    if is_reasoning_model(model=settings["model"]) and settings.get("top_p"):
        settings.pop("top_p")

    # Use litellm for the models
    params = {
        "messages": messages,
        "tools": tools_list or None,
        "user": str(developer.id),
        "tags": developer.tags,
        "custom_api_key": x_custom_api_key,
    }
    payload = {**settings, **params}

    if create_response_data.reasoning:
        if is_reasoning_model(model=payload["model"]):
            # Enable reasoning for supported models
            payload["reasoning_effort"] = create_response_data.reasoning.effort
            if create_response_data.reasoning.generate_summary:
                raise HTTPException(
                    status_code=400, detail="Generate summary is not supported yet"
                )
        else:
            raise HTTPException(
                status_code=400, detail="Reasoning is not supported for this model"
            )

    # Get initial model response
    model_response = await litellm.acompletion(**payload)

    # Model response is a list of choices
    assistant_message = model_response.choices[0].message

    # Extract web search tool call if it exists
    tool_call_requests = assistant_message.tool_calls

    performed_tool_calls = []
    function_tool_requests: list[FunctionToolCall] = []
    # Process tool calls if present (including multiple recursive tool calls if needed)
    if tool_call_requests and tools_list:
        # Start with the original messages
        current_messages = messages.copy()

        # Add the initial assistant message
        current_messages.append(assistant_message.model_dump())

        # Track if there are more tool calls to process
        has_tool_calls = True

        # Set a reasonable limit for tool call iterations to prevent infinite loops
        max_iterations = 20
        iterations = 0

        # Process tool calls in a loop until no more calls or max iterations reached
        while has_tool_calls and iterations < max_iterations:
            iterations += len(tool_call_requests)

            # Do not process original function tool calls. They will be sent to the user as is.
            if (
                tool_call_requests[0].type == "function"
                and tool_call_requests[0].function.name != "web_search_preview"
            ):
                function_tool_requests.append(
                    FunctionToolCall(
                        id=tool_call_requests[0].id,
                        call_id=tool_call_requests[0].id,
                        name=tool_call_requests[0].function.name,
                        arguments=tool_call_requests[0].function.arguments,
                        status="completed",
                    )
                )
                break

            # Process tool calls and get updated messages
            current_messages = await process_tool_calls(current_messages, tool_call_requests)

            performed_tool_calls.extend(tool_call_requests)
            # Make a follow-up call to the model with updated messages
            response_params = {
                "messages": current_messages,
                "tools": tools_list,
                "user": str(developer.id),
                "tags": developer.tags,
                "custom_api_key": x_custom_api_key,
            }
            response_payload = {**settings, **response_params}

            # Get model response
            model_response = await litellm.acompletion(**response_payload)
            assistant_message = model_response.choices[0].message

            # Add the assistant message to the current messages
            current_messages.append(assistant_message.model_dump())

            # Check if there are more tool calls to process
            has_tool_calls = bool(
                assistant_message.tool_calls
                and model_response.choices[0].finish_reason == "tool_calls"
            )

            # Update tool calls for next iteration
            tool_call_requests = assistant_message.tool_calls

        # After loop completes, current_messages contains the full conversation
        all_interaction_messages = current_messages

        # Save all the interaction history if requested
        if chat_input.save:
            # Create entry requests for all interactions
            new_entries = []

            # Add the user message
            new_entries.extend([
                CreateEntryRequest.from_model_input(
                    model=settings["model"],
                    **msg,
                    source="api_request",
                )
                for msg in new_messages
            ])

            # Add all the tool interaction messages
            for msg in all_interaction_messages[len(messages) :]:
                # Skip messages already included from new_messages
                if msg.get("role") == "user" and any(
                    nm.get("content") == msg.get("content") for nm in new_messages
                ):
                    continue

                new_entries.append(
                    CreateEntryRequest.from_model_input(
                        model=settings["model"],
                        **msg,
                        source="api_response"
                        if msg.get("role") == "assistant"
                        else "tool_response",
                    )
                )

            # Save all entries
            background_tasks.add_task(
                create_entries,
                developer_id=developer.id,
                session_id=session_id,
                data=new_entries,
            )
    else:
        # No tool calls, just save the standard input and response
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

    # Track usage using centralized tracker
    await track_completion_usage(
        developer_id=developer.id,
        model=settings["model"],
        messages=messages,
        response=model_response,
        custom_api_used=x_custom_api_key is not None,
        metadata={"tags": developer.tags},
    )

    # End chat function
    return convert_chat_response_to_response(
        create_response=create_response_data,
        chat_response=chat_response,
        chat_input=chat_input,
        session_id=session_id,
        user_id=developer.id,
        function_tool_requests=function_tool_requests,
        performed_tool_calls=performed_tool_calls,
    )
