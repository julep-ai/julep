import asyncio
from typing import Annotated, Any

from fastapi import Depends, HTTPException
from fastapi.background import BackgroundTasks
from uuid_extensions import uuid7

from ...activities.tool_executor import execute_tool_call, format_tool_results_for_llm
from ...common.utils.tool_runner import format_tool, run_llm_with_tools
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
from ..sessions.metrics import total_tokens_per_user
from ..sessions.render import render_chat_input
from .router import router


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


    # top_p is not supported for reasoning models
    if is_reasoning_model(model=settings["model"]) and settings.get("top_p"):
        settings.pop("top_p")

    # Use litellm for the models
    params = {
        "messages": messages,
        "tools": formatted_tools or None,
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

    async def run_tool(tool: CreateToolRequest, call: Any) -> ToolExecutionResult:
        return await execute_tool_call(call.model_dump())

    model_response = await run_llm_with_tools(
        messages=messages,
        tools=chat_input.tools or [],
        settings=payload,
        run_tool_call=run_tool,
        user=str(developer.id),
    )

    assistant_message = model_response.choices[0].message

    performed_tool_calls = assistant_message.tool_calls or []
    function_tool_requests: list[FunctionToolCall] = []

    all_interaction_messages = messages + [choice.message.model_dump() for choice in model_response.choices]

    if chat_input.save:
        new_entries = [
            CreateEntryRequest.from_model_input(
                model=settings["model"],
                **msg,
                source="api_request",
            )
            for msg in new_messages
        ]

        for msg in all_interaction_messages[len(messages) :]:
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
