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
) -> tuple[list[dict], list[DocReference]]:
    new_raw_messages = [msg.model_dump(mode="json") for msg in chat_input.messages]
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
        entry.model_dump(mode="json")
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
            message["content"] = message["content"][0]["text"].strip()

    if not recall:
        return past_messages, []

    # TODO: Make this configurable?
    search_threshold = 4
    search_query_chars = 1000
    search_messages = [
        msg
        for msg in (past_messages + new_raw_messages)[-(search_threshold):]
        if isinstance(msg["content"], str) and msg["role"] in ["user", "assistant"]
    ]

    if len(search_messages) == 0:
        return past_messages, []

    # FIXME: This should only search text messages and not embed if text is empty
    # Search matching docs
    embed_text = "\n\n".join(
        [
            f"{msg.get('name') or msg['role']}: {msg['content']}"
            for msg in search_messages
        ]
    ).strip()

    [query_embedding, *_] = await litellm.aembedding(
        # Truncate on the left to keep the last `search_query_chars` characters
        inputs=embed_text[-(search_query_chars):],
    )

    # Truncate on the right to take only the first `search_query_chars` characters
    query_text = search_messages[-1]["content"].strip()[:search_query_chars]

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
