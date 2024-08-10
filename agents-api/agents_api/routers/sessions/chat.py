from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
)
from ...dependencies.developer_id import get_developer_id
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

    # Then, use the chat context to chat

    print(chat_context)
