"""
Chat endpoint router with feature flag-based implementation selection.
Routes to either legacy or auto-tools implementation based on feature flags.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import BackgroundTasks, Depends, Header
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
    MessageChatResponse,
)
from ...common.protocol.developers import Developer
from ...common.utils.feature_flags import get_feature_flag_value
from ...dependencies.developer_id import get_developer_data
from .router import router


def with_mock_response(r: str | None = None):
    def wrapper():
        return r

    return wrapper


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

    Routes to different implementations based on feature flags:
    - If auto_run_tools_chat feature flag is enabled, uses the new auto-tools implementation
    - Otherwise, uses the legacy implementation

    Parameters:
        developer (Developer): The developer associated with the chat session.
        session_id (UUID): The unique identifier of the chat session.
        chat_input (ChatInput): The chat input data.
        background_tasks (BackgroundTasks): The background tasks to run.
        x_custom_api_key (Optional[str]): The custom API key.
        mock_response (Optional[str]): Mock response for testing.
        connection_pool: Connection pool for testing purposes.

    Returns:
        ChatResponse or StreamingResponse: The chat response or streaming response.
    """
    # Check if auto tools feature is enabled
    # AIDEV-NOTE: Feature flag controls which implementation to use
    if get_feature_flag_value("auto_run_tools_chat", developer_id=str(developer.id)):
        from .auto_tools.chat import chat as chat_auto_tools
        
        return await chat_auto_tools(
            developer=developer,
            session_id=session_id,
            chat_input=chat_input,
            background_tasks=background_tasks,
            x_custom_api_key=x_custom_api_key,
            mock_response=mock_response,
            connection_pool=connection_pool,
        )

    # Default to legacy implementation
    from .legacy.chat import chat as chat_legacy
    
    return await chat_legacy(
        developer=developer,
        session_id=session_id,
        chat_input=chat_input,
        background_tasks=background_tasks,
        x_custom_api_key=x_custom_api_key,
        mock_response=mock_response,
        connection_pool=connection_pool,
    )