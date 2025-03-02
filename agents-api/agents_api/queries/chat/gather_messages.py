from typing import TypeVar
from uuid import UUID

import numpy as np
from beartype import beartype
from fastapi import HTTPException
from pydantic import ValidationError

from ...autogen.openapi_model import (
    ChatInput,
    DocReference,
    History,
    HybridDocSearchRequest,
    Session,
    TextOnlyDocSearchRequest,
    VectorDocSearchRequest,
)
from ...clients import litellm
from ...common.protocol.developers import Developer
from ...common.protocol.sessions import ChatContext
from ...common.utils.db_exceptions import common_db_exceptions, partialclass
from ...common.utils.get_doc_search import get_search_fn_and_params
from ..docs.mmr import maximal_marginal_relevance
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

    # If recall is disabled, return early
    if not recall:
        return past_messages, []

    # Get recall options
    session: Session = await get_session(
        developer_id=developer.id,
        session_id=session_id,
        connection_pool=connection_pool,
    )
    recall_options = session.recall_options

    # If recall is enabled but recall options are not configured, return early
    if recall_options is None:
        return past_messages, []

    # If recall is enabled and recall options are configured, get messages to search from
    search_messages = [
        msg
        for msg in (past_messages + new_raw_messages)[-(recall_options.num_search_messages) :]
        if isinstance(msg["content"], str) and msg["role"] in ["user", "assistant"]
    ]

    if not search_messages:
        return past_messages, []

    # Build search text and get embedding if needed
    embed_text = "\n\n".join(
        f"{msg.get('name') or msg['role']}: {msg['content']}" for msg in search_messages
    ).strip()

    query_embedding = None
    if recall_options.mode != "text":
        [query_embedding, *_] = await litellm.aembedding(
            inputs=embed_text[-(recall_options.max_query_length) :],
            embed_instruction="Represent the query for retrieving supporting documents: ",
        )

    # Get query text from last message
    query_text = search_messages[-1]["content"].strip()[: recall_options.max_query_length]

    # Get owners to search docs from
    active_agent_id = chat_context.get_active_agent().id
    owners = [("user", user.id) for user in chat_context.users]
    owners.append(("agent", active_agent_id))

    # Build search params based on mode
    search_params = None
    if recall_options.mode == "vector":
        search_params = VectorDocSearchRequest(
            lang=recall_options.lang,
            limit=recall_options.limit,
            metadata_filter=recall_options.metadata_filter,
            confidence=recall_options.confidence,
            mmr_strength=recall_options.mmr_strength,
            vector=query_embedding,
        )
    elif recall_options.mode == "hybrid":
        search_params = HybridDocSearchRequest(
            lang=recall_options.lang,
            limit=recall_options.limit,
            metadata_filter=recall_options.metadata_filter,
            confidence=recall_options.confidence,
            mmr_strength=recall_options.mmr_strength,
            alpha=recall_options.alpha,
            text=query_text,
            vector=query_embedding,
        )
    elif recall_options.mode == "text":
        search_params = TextOnlyDocSearchRequest(
            lang=recall_options.lang,
            limit=recall_options.limit,
            metadata_filter=recall_options.metadata_filter,
            text=query_text,
        )
    else:
        # Invalid mode, return early
        return past_messages, []

    # Execute search
    search_fn, params = get_search_fn_and_params(search_params)
    doc_references: list[DocReference] = await search_fn(
        developer_id=developer.id,
        owners=owners,
        connection_pool=connection_pool,
        **params,
    )

    # Apply MMR if enabled and applicable
    if (
        recall_options.mmr_strength > 0
        and len(doc_references) > recall_options.limit
        and recall_options.mode != "text"
    ):
        # Filter docs with embeddings
        docs_with_embeddings = [
            doc for doc in doc_references if doc.snippet.embedding is not None
        ]

        if len(docs_with_embeddings) >= 2:
            # Apply MMR
            indices = maximal_marginal_relevance(
                np.asarray(query_embedding),
                [doc.snippet.embedding for doc in docs_with_embeddings],
                k=min(recall_options.limit, len(docs_with_embeddings)),
                lambda_mult=1 - recall_options.mmr_strength,
            )
            doc_references = [
                doc for i, doc in enumerate(docs_with_embeddings) if i in set(indices)
            ]

    return past_messages, doc_references
