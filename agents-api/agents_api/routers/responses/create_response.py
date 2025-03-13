from typing import Annotated
from uuid import UUID
from uuid_extensions import uuid7
from fastapi import Depends
from fastapi.background import BackgroundTasks
from ...autogen.openapi_model import CreateResponse, Response, ChatResponse, ChunkChatResponse, MessageChatResponse, CreateEntryRequest
from ...dependencies.developer_id import get_developer_id, get_developer_data
from ...queries.entries.create_entries import create_entries
from .router import router
from ..sessions.render import render_chat_input
from ...routers.utils.model_converters import convert_create_response_to_chat_input, convert_chat_response_to_response
from ...routers.utils.create_responses_ids import create_responses_user, create_responses_session
from ...clients import litellm
from ...common.utils.datetime import utcnow
from ..sessions.metrics import total_tokens_per_user

@router.post("/responses", tags=["responses"])
async def create_response(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    create_response_data: CreateResponse,
) -> Response:
    chat_input = convert_create_response_to_chat_input(create_response_data)
    session_id = None
    agent_id = None
    if create_response_data.previous_response_id:
        session_id = create_response_data.previous_response_id
        # TODO: get agent_id from session_id
    else:
        agent_id = (await create_responses_user(x_developer_id, create_response_data)).id
        session_id = (await create_responses_session(x_developer_id, create_response_data, agent_id)).id
    
    developer = get_developer_data(x_developer_id)
    x_custom_api_key = None
    background_tasks = BackgroundTasks()

    ### Chat function
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
    }
    payload = {**settings, **params}

    model_response = await litellm.acompletion(**payload)

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
    ### End chat function

    response = convert_chat_response_to_response(chat_response, chat_input, session_id, agent_id)
    return response
