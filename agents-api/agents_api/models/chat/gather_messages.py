from typing import TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.Chat import ChatInput
from ...autogen.openapi_model import DocReference, History
from ...clients import litellm
from ...common.protocol.developers import Developer
from ...common.protocol.sessions import ChatContext
from ..docs.search_docs_hybrid import search_docs_hybrid
from ..entry.get_history import get_history
from ..utils import (
    partialclass,
    rewrap_exceptions,
)

T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@beartype
async def gather_messages(
    *,
    developer: Developer,
    session_id: UUID,
    chat_context: ChatContext,
    chat_input: ChatInput,
):
    new_raw_messages = [msg.model_dump() for msg in chat_input.messages]
    recall = chat_input.recall

    assert len(new_raw_messages) > 0

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

    # Collapse the message content if content is a list of strings and only one string
    for message in past_messages:
        if (
            isinstance(message["content"], list)
            and len(message["content"]) == 1
            and message["content"][0].get("type") == "text"
        ):
            message["content"] = message["content"][0]["text"]

    if not recall:
        return past_messages, []

    # FIXME: This should only search text messages and not embed if text is empty 
    # Search matching docs
    [query_embedding, *_] = await litellm.aembedding(
        inputs="\n\n".join(
            [
                f"{msg.get('name') or msg['role']}: {msg['content']}"
                for msg in new_raw_messages
                if isinstance(msg["content"], str)
            ]
        ),
    )
    query_text = (
        new_raw_messages[-1]["content"]
        if isinstance(new_raw_messages[-1]["content"], str)
        else ""
    )

    # List all the applicable owners to search docs from
    active_agent_id = chat_context.get_active_agent().id
    user_ids = [user.id for user in chat_context.users]
    owners = [("user", user_id) for user_id in user_ids] + [("agent", active_agent_id)]

    doc_references: list[DocReference] = search_docs_hybrid(
        developer_id=developer.id,
        owners=owners,
        query=query_text,
        query_embedding=query_embedding,
    )

    return past_messages, doc_references
