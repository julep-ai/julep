from typing import Annotated
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    ChatInput,
    ChatResponse,
    CreateEntryRequest,
    DocReference,
    History,
)
from ...clients.embed import embed
from ...clients.litellm import acompletion
from ...common.protocol.developers import Developer
from ...common.protocol.sessions import ChatContext
from ...common.utils.template import render_template
from ...dependencies.developer_id import get_developer_data
from ...models.docs.search_docs_hybrid import search_docs_hybrid
from ...models.entry.create_entries import create_entries
from ...models.entry.get_history import get_history
from ...models.session.prepare_chat_context import prepare_chat_context
from .router import router


@router.post(
    "/sessions/{session_id}/chat",
    status_code=HTTP_201_CREATED,
    tags=["sessions", "chat"],
)
async def chat(
    developer: Annotated[Developer, Depends(get_developer_data)],
    session_id: UUID,
    data: ChatInput,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    # First get the chat context
    chat_context: ChatContext = prepare_chat_context(
        developer_id=developer.id,
        session_id=session_id,
    )
    assert isinstance(chat_context, ChatContext)

    # Merge the settings and prepare environment
    chat_context.merge_settings(data)
    settings: dict = chat_context.settings.model_dump()
    env: dict = chat_context.get_chat_environment()

    # Get the session history
    history: History = get_history(
        developer_id=developer.id,
        session_id=session_id,
        allowed_sources=["api_request", "api_response", "tool_response", "summarizer"],
    )

    # Keep leaf nodes only
    relations = history.relations
    past_messages = [
        entry.model_dump()
        for entry in history.entries
        if entry.id not in {r.head for r in relations}
    ]

    new_raw_messages = [msg.model_dump() for msg in data.messages]

    # Search matching docs
    [query_embedding, *_] = await embed(
        inputs=[
            f"{msg.get('name') or msg['role']}: {msg['content']}"
            for msg in new_raw_messages
        ],
        join_inputs=True,
    )
    query_text = new_raw_messages[-1]["content"]

    doc_references: list[DocReference] = search_docs_hybrid(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=chat_context.get_active_agent().id,
        query=query_text,
        query_embedding=query_embedding,
    )

    # Render the messages
    env["docs"] = doc_references
    new_messages = render_template(new_raw_messages, variables=env)
    messages = past_messages + new_messages

    # Get the response from the model
    model_response = await acompletion(
        messages=messages,
        **settings,
        user=str(developer.id),
        tags=developer.tags,
    )

    # Save the input and the response to the session history
    new_entries = [CreateEntryRequest(**msg) for msg in new_messages]
    background_tasks.add_task(
        create_entries,
        developer_id=developer.id,
        session_id=session_id,
        data=new_entries,
        mark_session_as_updated=True,
    )

    # Return the response
    response_json = model_response.model_dump()
    response_json.pop("id", None)

    chat_response: ChatResponse = ChatResponse(
        **response_json,
        id=uuid4(),
        created_at=model_response.created,
        jobs=[],
        docs=doc_references,
    )

    return chat_response
