from datetime import datetime
from typing import Annotated, Callable, Optional
from uuid import UUID, uuid4

from anthropic import AsyncAnthropic
from anthropic.types.beta.beta_message import BetaMessage
from fastapi import BackgroundTasks, Depends, Header
from langchain_core.tools import BaseTool
from langchain_core.tools.convert import tool as tool_decorator
from litellm import ChatCompletionMessageToolCall, Function, Message
from litellm.types.utils import Choices, ModelResponse
from starlette.status import HTTP_201_CREATED

from ...activities.utils import get_handler_with_filtered_params
from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
    ChunkChatResponse,
    CreateEntryRequest,
    MessageChatResponse,
)
from ...autogen.Tools import Tool
from ...clients import litellm
from ...common.protocol.developers import Developer
from ...common.protocol.sessions import ChatContext
from ...common.utils.datetime import utcnow
from ...common.utils.template import render_template
from ...dependencies.developer_id import get_developer_data
from ...env import anthropic_api_key
from ...models.chat.gather_messages import gather_messages
from ...models.chat.prepare_chat_context import prepare_chat_context
from ...models.entry.create_entries import create_entries
from .metrics import total_tokens_per_user
from .router import router

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"


def format_tool(tool: Tool) -> dict:
    if tool.type == "computer_20241022":
        return {
            "type": tool.type,
            "name": tool.name,
            "display_width_px": tool.computer_20241022
            and tool.computer_20241022.display_width_px,
            "display_height_px": tool.computer_20241022
            and tool.computer_20241022.display_height_px,
            "display_number": tool.computer_20241022
            and tool.computer_20241022.display_number,
        }

    if tool.type in ["bash_20241022", "text_editor_20241022"]:
        return tool.model_dump(include={"type", "name"})

    if tool.type == "function":
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.function and tool.function.parameters,
            },
        }

    # For other tool types, we need to translate them to the OpenAI function tool format
    formatted = {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description},
    }

    if tool.type == "system":
        handler: Callable = get_handler_with_filtered_params(tool.system)

        lc_tool: BaseTool = tool_decorator(handler)

        json_schema: dict = lc_tool.get_input_jsonschema()

        formatted["function"]["description"] = formatted["function"][
            "description"
        ] or json_schema.get("description")

        formatted["function"]["parameters"] = json_schema

    # # FIXME: Implement integration tools
    # elif tool.type == "integration":
    #     raise NotImplementedError("Integration tools are not supported")

    # # FIXME: Implement API call tools
    # elif tool.type == "api_call":
    #     raise NotImplementedError("API call tools are not supported")

    return formatted


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
    x_custom_api_key: Optional[str] = Header(None, alias="X-Custom-Api-Key"),
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

    if chat_input.stream:
        raise NotImplementedError("Streaming is not yet implemented")

    # First get the chat context
    chat_context: ChatContext = prepare_chat_context(
        developer_id=developer.id,
        session_id=session_id,
    )

    # Merge the settings and prepare environment
    chat_context.merge_settings(chat_input)
    settings: dict = chat_context.settings.model_dump(mode="json", exclude_none=True)

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
        dict(
            title=ref.title,
            content=[ref.snippet.content],
        )
        for ref in doc_references
    ]

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
    new_raw_messages = [msg.model_dump(mode="json") for msg in chat_input.messages]

    if chat_context.session.render_templates:
        new_messages = await render_template(new_raw_messages, variables=env)
    else:
        new_messages = new_raw_messages

    # Combine the past messages with the new messages
    messages = past_messages + new_messages

    # Get the tools
    tools = settings.get("tools") or chat_context.get_active_tools()

    # Format tools for litellm
    formatted_tools = [format_tool(tool) for tool in tools]

    # FIXME: Truncate chat messages in the chat context
    # SCRUM-7
    if chat_context.session.context_overflow == "truncate":
        # messages = messages[-settings["max_tokens"] :]
        raise NotImplementedError("Truncation is not yet implemented")

    # FIXME: Hotfix for datetime not serializable. Needs investigation
    messages = [
        {
            k: v
            for k, v in m.items()
            if k in ["role", "content", "tool_calls", "tool_call_id", "user"]
        }
        for m in messages
    ]

    # Check if using Claude model and has specific tool types
    is_claude_model = settings["model"].lower().startswith("claude-3.5")
    has_special_tools = any(
        tool["type"] in ["computer_20241022", "bash_20241022", "text_editor_20241022"]
        for tool in formatted_tools
    )

    if is_claude_model and has_special_tools:
        # Use Anthropic API directly
        client = AsyncAnthropic(api_key=anthropic_api_key)

        # Filter tools for specific types
        filtered_tools = [
            tool
            for tool in formatted_tools
            if tool["type"]
            in ["computer_20241022", "bash_20241022", "text_editor_20241022"]
        ]

        # Format messages for Claude
        claude_messages = []
        for msg in messages:
            # Skip messages that are not assistant or user
            if msg["role"] not in ["assistant", "user"]:
                continue

            claude_messages.append({"role": msg["role"], "content": msg["content"]})

        # Call Claude API
        claude_response: BetaMessage = await client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=claude_messages,
            tools=filtered_tools,
            max_tokens=settings.get("max_tokens", 1024),
            betas=[COMPUTER_USE_BETA_FLAG],
        )

        # Convert Claude response to litellm format
        text_block = next(
            (block for block in claude_response.content if block.type == "text"),
            None,
        )

        if claude_response.stop_reason == "tool_use":
            choice = Choices(
                message=Message(
                    role="assistant",
                    content=text_block.text if text_block else None,
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            type="function",
                            function=Function(
                                name=block.name,
                                arguments=block.input,
                            ),
                        )
                        for block in claude_response.content
                        if block.type == "tool_use"
                    ],
                ),
                finish_reason="tool_calls",
            )
        else:
            assert (
                text_block
            ), "Claude should always return a text block for stop_reason=stop"
            choice = Choices(
                message=Message(
                    role="assistant",
                    content=text_block.text,
                ),
                finish_reason="stop",
            )

        model_response = ModelResponse(
            id=claude_response.id,
            choices=[choice],
            created=int(datetime.now().timestamp()),
            model=claude_response.model,
            object="text_completion",
            usage={
                "total_tokens": claude_response.usage.input_tokens
                + claude_response.usage.output_tokens
            },
        )
    else:
        # FIXME: hardcoded tool to a None value as the tool calls are not implemented yet
        formatted_tools = None
        # Use litellm for other models
        model_response = await litellm.acompletion(
            messages=messages,
            tools=formatted_tools or None,
            user=str(developer.id),
            tags=developer.tags,
            custom_api_key=x_custom_api_key,
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
        # FIXME: We need to save all the choices
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
    jobs = []
    if chat_context.session.context_overflow == "adaptive":
        # FIXME: Start the adaptive context workflow
        # SCRUM-8

        # jobs = [await start_adaptive_context_workflow]
        raise NotImplementedError("Adaptive context is not yet implemented")

    # Return the response
    # FIXME: Implement streaming for chat
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

    total_tokens_per_user.labels(str(developer.id)).inc(
        amount=chat_response.usage.total_tokens
        if chat_response.usage is not None
        else 0
    )

    return chat_response
