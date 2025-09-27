"""
Render endpoint router with feature flag-based implementation selection.
Routes to either legacy or auto-tools implementation based on feature flags.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_200_OK

from ...autogen.openapi_model import (
    ChatInput,
    RenderResponse,
)
from ...common.protocol.developers import Developer
from ...common.utils.feature_flags import get_feature_flag_value
from ...dependencies.developer_id import get_developer_data
from .router import router


@router.post(
    "/sessions/{session_id}/render",
    status_code=HTTP_200_OK,
    tags=["sessions", "render"],
)
async def render(
    developer: Annotated[Developer, Depends(get_developer_data)],
    session_id: UUID,
    chat_input: ChatInput,
) -> RenderResponse:
    """
    Renders a chat input.

    Routes to different implementations based on feature flags:
    - If auto_run_tools_chat feature flag is enabled, uses the new auto-tools implementation
    - Otherwise, uses the legacy implementation

    Parameters:
        developer (Developer): The developer associated with the chat session.
        session_id (UUID): The unique identifier of the chat session.
        chat_input (ChatInput): The chat input data.

    Returns:
        RenderResponse: The rendered chat input.
    """
    # Check if auto tools feature is enabled
    # AIDEV-NOTE: Feature flag controls which implementation to use
    if get_feature_flag_value("auto_run_tools_chat", developer_id=str(developer.id)):
        from .auto_tools.render import render as render_auto_tools

        return await render_auto_tools(
            developer=developer,
            session_id=session_id,
            chat_input=chat_input,
        )

    # Default to legacy implementation
    from .legacy.render import render as render_legacy

    return await render_legacy(
        developer=developer,
        session_id=session_id,
        chat_input=chat_input,
    )
