"""
Chat implementation with automatic tool execution support.
When auto_run_tools is enabled, this implementation will automatically execute tools
and feed results back to the model.
"""

from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from uuid_extensions import uuid7

from ....autogen.openapi_model import (
    BaseChosenToolCall,
    ChatInput,
    CreateEntryRequest,
    MessageChatResponse,
    Tool,
    ToolExecutionResult,
)
from ....clients import litellm
from ....common.protocol.developers import Developer
from ....common.utils.datetime import utcnow
from ....common.utils.tool_runner import run_llm_with_tools, run_tool_call
from ....queries.entries.create_entries import create_entries
# Entry saving logic will be implemented directly in this file
from ..metrics import total_tokens_per_user
from .render import render_chat_input

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


async def chat(
    developer: Developer,
    session_id: UUID,
    chat_input: ChatInput,
    background_tasks: BackgroundTasks,
    x_custom_api_key: str | None = None,
    mock_response: str | None = None,
    connection_pool: Any = None,  # This is for testing purposes
) -> MessageChatResponse | StreamingResponse:
    """
    Chat implementation with automatic tool execution.

    When chat_input.auto_run_tools is True, tools are executed automatically.
    When False, tools are not passed to the model to prevent tool calls.

    Note: Streaming is not supported when tools are involved.

    Parameters:
        developer (Developer): The developer associated with the chat session.
        session_id (UUID): The unique identifier of the chat session.
        chat_input (ChatInput): The chat input data with auto_run_tools flag.
        background_tasks (BackgroundTasks): The background tasks to run.
        x_custom_api_key (Optional[str]): The custom API key.
        mock_response (Optional[str]): Mock response for testing.
        connection_pool: Connection pool for testing purposes.

    Returns:
        MessageChatResponse: The chat response (no streaming with tools).
    """
    (
        messages,
        doc_references,
        tools,  # auto_tools/render.py returns actual tools, not formatted
        settings,
        new_messages,
        chat_context,
    ) = await render_chat_input(
        developer=developer,
        session_id=session_id,
        chat_input=chat_input,
    )

    # Determine tools to use based on auto_run_tools
    # AIDEV-NOTE: When auto_run_tools=False, pass empty tools list to prevent
    # model from making tool calls that won't be executed. This simplifies the
    # flow as the model will always return a regular completion instead of tool calls.
    tools_to_use = tools if chat_input.auto_run_tools else []

    # Check if streaming is requested with tools
    if chat_input.stream and tools_to_use:
        # Streaming with tools is not supported
        msg = "Streaming is not supported when auto_run_tools is enabled"
        raise HTTPException(status_code=400, detail=msg)

    # Prepare base parameters
    completion_data = {
        "model": settings["model"],
        "user": str(developer.id),
        "tags": developer.tags,
        "custom_api_key": x_custom_api_key,
        "mock_response": mock_response,
        **settings,
    }

    # Remove messages from completion_data if it exists to avoid duplicate parameter error
    completion_data.pop("messages", None)
    completion_data.pop("tools", None)

    # If no tools or auto_run_tools is False, use simple completion
    if not tools_to_use:
        # Prepare parameters for LiteLLM
        params = {
            "messages": messages,
            "tools": None,  # No tools when auto_run_tools=False
            **completion_data,
        }

        # Set streaming parameter based on chat_input.stream
        if chat_input.stream:
            params["stream"] = True
            params["stream_options"] = {"include_usage": True}

        # Get response from LiteLLM
        model_response = await litellm.acompletion(**params)

        # Save messages if requested (non-tool execution path)
        if chat_input.save:
            # Create entries for input messages
            new_entries = [
                CreateEntryRequest.from_model_input(
                    model=settings["model"],
                    **msg,
                    source="api_request",
                )
                for msg in new_messages
            ]
            
            # Add the response
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
            )

        # Auto tools implementation does not support streaming
        # Keep model_response for later use
    else:
        # Use tool execution loop
        # Get the first agent from the chat context
        if not chat_context.agents:
            msg = "No agent found for the session"
            raise HTTPException(status_code=400, detail=msg)

        agent = chat_context.agents[0]

        # Create a partial function for tool execution with chat context
        async def run_tool_partial(tool: Tool, call: BaseChosenToolCall) -> ToolExecutionResult:
            return await run_tool_call(
                developer_id=developer.id,
                agent_id=agent.id,
                task_id=None,  # No task in chat context
                session_id=session_id,
                tool=tool,
                call=call,
                connection_pool=connection_pool,
            )

        # Use tools from render_chat_input which already includes agent tools + chat_input tools
        # Run LLM with automatic tool execution
        all_messages = await run_llm_with_tools(
            messages=messages,
            tools=tools_to_use,  # Already filtered based on auto_run_tools
            settings=completion_data,
            run_tool_call=run_tool_partial,
        )

        # The last message is the final response
        final_response = all_messages[-1]

        # Save all messages to history if requested
        if chat_input.save:

            # Save input messages
            entries_to_save = [CreateEntryRequest.from_model_input(
                        model=settings["model"],
                        **msg,
                        source="api_request",
                    ) for msg in new_messages]

            # Save all generated messages (including tool calls and results)
            entries_to_save.extend(CreateEntryRequest.from_model_input(
                        model=settings["model"],
                        **msg,
                        source="api_response",
                    ) for msg in all_messages[len(messages) :])

            background_tasks.add_task(
                create_entries,
                developer_id=developer.id,
                session_id=session_id,
                data=entries_to_save,
            )

    # Create non-streaming response
    if tools_to_use:
        # For tool execution, we synthesize usage data
        usage_data = {
            "prompt_tokens": 0,  # Would need to track this in run_llm_with_tools
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        # Extract the final message content from the last message
        final_content = final_response.get("content", "")
        final_tool_calls = final_response.get("tool_calls")
    else:
        # For non-tool execution, use the response from litellm
        usage_data = model_response.usage.model_dump() if model_response.usage else {}
        final_content = (
            model_response.choices[0].message.content if model_response.choices else ""
        )
        final_tool_calls = (
            model_response.choices[0].message.tool_calls if model_response.choices else None
        )

    chat_response = MessageChatResponse(
        id=uuid7(),
        created_at=utcnow(),
        jobs=[],
        docs=doc_references,
        usage=usage_data,
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": final_content,
                    "tool_calls": final_tool_calls,
                },
                "finish_reason": "stop",
            }
        ],
    )

    # Track usage metrics
    if usage_data.get("total_tokens", 0) > 0:
        total_tokens_per_user.labels(str(developer.id)).inc(amount=usage_data["total_tokens"])

    return chat_response
