from typing import TypeVar
from uuid import UUID

import numpy as np
from beartype import beartype
from fastapi import HTTPException
from pydantic import ValidationError

from ...autogen.openapi_model import ChatInput, DocReference, History, Session
from ...clients import litellm
from ...common.protocol.developers import Developer
from ...common.protocol.sessions import ChatContext
from ...common.utils.db_exceptions import common_db_exceptions, partialclass
from ..docs.mmr import maximal_marginal_relevance
from ..docs.search_docs_by_embedding import search_docs_by_embedding
from ..docs.search_docs_by_text import search_docs_by_text
from ..docs.search_docs_hybrid import search_docs_hybrid
from ..entries.get_history import get_history
from ..sessions.get_session import get_session
from ..utils import rewrap_exceptions

T = TypeVar("T")


@rewrap_exceptions({
    ValidationError: partialclass(HTTPException, status_code=400),
    TypeError: partialclass(HTTPException, status_code=400),
    **common_db_exceptions("history", ["get"]),
})
@beartype
async def gather_messages(
    *,
    developer: Developer,
    session_id: UUID,
    chat_context: ChatContext,
    chat_input: ChatInput,
    connection_pool=None,
) -> tuple[list[dict], list[DocReference]]:
    new_raw_messages = [msg.model_dump(mode="json") for msg in chat_input.messages]
    recall = chat_input.recall

    assert len(new_raw_messages) > 0

    # Get the session history
    history: History = await get_history(
        developer_id=developer.id,
        session_id=session_id,
        allowed_sources=["api_request", "api_response", "tool_response", "summarizer"],
        connection_pool=connection_pool,
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

    # Get recall options
    session: Session = await get_session(
        developer_id=developer.id,
        session_id=session_id,
        connection_pool=connection_pool,
    )
    recall_options = session.recall_options

    # Ensure recall_options is not None and has the necessary attributes
    if recall and recall_options:
        # search the last `search_threshold` messages
        search_messages = [
            msg
            for msg in (past_messages + new_raw_messages)[
                -(recall_options.num_search_messages) :
            ]
            if isinstance(msg["content"], str) and msg["role"] in ["user", "assistant"]
        ]

        if len(search_messages) == 0:
            return past_messages, []

        # Search matching docs
        embed_text = "\n\n".join([
            f"{msg.get('name') or msg['role']}: {msg['content']}" for msg in search_messages
        ]).strip()

        # Don't embed if search mode is text only
        if recall_options.mode != "text":
            [query_embedding, *_] = await litellm.aembedding(
                # Truncate on the left to keep the last `search_query_chars` characters
                inputs=embed_text[-(recall_options.max_query_length) :],
                # TODO: Make this configurable once it's added to the ChatInput model
                embed_instruction="Represent the query for retrieving supporting documents: ",
            )

        # Truncate on the right to take only the first `search_query_chars` characters
        query_text = search_messages[-1]["content"].strip()[: recall_options.max_query_length]

        # List all the applicable owners to search docs from
        active_agent_id = chat_context.get_active_agent().id
        user_ids = [user.id for user in chat_context.users]
        owners = [("user", user_id) for user_id in user_ids] + [("agent", active_agent_id)]

        # Search for doc references
        doc_references: list[DocReference] = []
        match recall_options.mode:
            case "vector":
                doc_references = await search_docs_by_embedding(
                    developer_id=developer.id,
                    owners=owners,
                    embedding=query_embedding,
                    connection_pool=connection_pool,
                )
            case "hybrid":
                doc_references = await search_docs_hybrid(
                    developer_id=developer.id,
                    owners=owners,
                    text_query=query_text,
                    embedding=query_embedding,
                    connection_pool=connection_pool,
                )
            case "text":
                doc_references = await search_docs_by_text(
                    developer_id=developer.id,
                    owners=owners,
                    query=query_text,
                    connection_pool=connection_pool,
                )

        # Apply MMR if enabled
        if (
            recall_options.mmr_strength > 0
            and len(doc_references) > recall_options.limit
            and recall_options.mode != "text"
            and len([doc for doc in doc_references if doc.snippet.embedding is not None]) >= 2
        ):
            # FIXME: This is a temporary fix to ensure that the MMR algorithm works.
            # We shouldn't be having references without embeddings.
            doc_references = [
                doc for doc in doc_references if doc.snippet.embedding is not None
            ]

            # Apply MMR
            indices = maximal_marginal_relevance(
                np.asarray(query_embedding),
                [doc.snippet.embedding for doc in doc_references],
                k=recall_options.limit,
            )
            doc_references = [doc for i, doc in enumerate(doc_references) if i in set(indices)]

        return past_messages, doc_references

    # If recall is False or recall_options is None, return past messages with no doc references
    return past_messages, []
