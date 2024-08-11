from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
    History,
)
from ...common.utils.template import render_template
from ...dependencies.developer_id import get_developer_id
from ...models.entry.get_history import get_history
from ...models.session.prepare_chat_context import prepare_chat_context
from .router import router


@router.post(
    "/sessions/{session_id}/chat",
    status_code=HTTP_201_CREATED,
    tags=["sessions", "chat"],
)
async def chat(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    session_id: UUID,
    data: ChatInput,
) -> ChatResponse:
    # First get the chat context
    chat_context = prepare_chat_context(
        developer_id=x_developer_id,
        agent_id=data.agent_id,
        session_id=session_id,
    )

    # Merge the settings and prepare environment
    request_settings = data.settings
    chat_context.merge_settings(request_settings)

    env: dict = chat_context.get_chat_environment()

    # Get the session history
    history: History = get_history(
        developer_id=x_developer_id,
        session_id=session_id,
        allowed_sources=["api_request", "api_response", "tool_response", "summarizer"],
    )

    # Keep leaf nodes only
    relations = history.relations
    past_entries = [
        entry.model_dump()
        for entry in history.entries
        if entry.id not in {r.head for r in relations}
    ]

    past_messages = render_template(past_entries, variables=env)

    messages = past_messages + [msg.model_dump() for msg in data.messages]

    # TODO: Implement the chat logic here
    print(messages)

    # Get the response from the model

    # Save the input and the response to the session history

    # Return the response
    raise NotImplementedError()
