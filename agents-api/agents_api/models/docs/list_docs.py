"""This module contains functions for querying document-related data from the 'cozodb' database using datalog queries."""

import json
from typing import Any, Literal, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import Doc
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    Doc,
    transform=lambda d: {
        "content": [s[1] for s in sorted(d["snippet_data"], key=lambda x: x[0])],
        "embeddings": [
            s[2]
            for s in sorted(d["snippet_data"], key=lambda x: x[0])
            if s[2] is not None
        ],
        **d,
    },
)
@cozo_query
@beartype
def list_docs(
    *,
    developer_id: UUID,
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
    include_without_embeddings: bool = False,
) -> tuple[list[str], dict]:
    """
    Constructs and returns a datalog query for listing documents and their associated information snippets.

    Parameters:
        developer_id (UUID): The unique identifier of the developer associated with the documents.
        owner_id (UUID): The unique identifier of the owner (user or agent) associated with the documents.
        owner_type (Literal["user", "agent"]): The type of owner associated with the documents.
        limit (int): The maximum number of documents to return.
        offset (int): The number of documents to skip before returning the results.
        sort_by (Literal["created_at"]): The field to sort the documents by.
        direction (Literal["asc", "desc"]): The direction to sort the documents in.
        metadata_filter (dict): A dictionary of metadata filters to apply to the documents.
        include_without_embeddings (bool): Whether to include documents without embeddings in the results.

    Returns:
        Doc[]
    """

    # Transforms the metadata_filter dictionary into a string representation for the datalog query.
    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    owner_id = str(owner_id)
    sort = f"{'-' if direction == 'desc' else ''}{sort_by}"

    get_query = f"""
        snippets[id, collect(snippet_data)] :=
            *snippets {{
                doc_id: id,
                index,
                content,
                embedding,
            }},
            {"" if include_without_embeddings else "not is_null(embedding),"}
            snippet_data = [index, content, embedding]

        ?[
            owner_type,
            id,
            title,
            snippet_data,
            created_at,
            metadata,
        ] :=
            owner_type = $owner_type,
            owner_id = to_uuid($owner_id),
            *docs {{
                owner_type,
                owner_id,
                doc_id: id,
                title,
                created_at,
                metadata,
            }},
            snippets[id, snippet_data],
            {metadata_filter_str}
        
        :limit $limit
        :offset $offset
        :sort {sort}
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, f"{owner_type}s", **{f"{owner_type}_id": owner_id}
        ),
        get_query,
    ]

    return (
        queries,
        {
            "owner_id": owner_id,
            "owner_type": owner_type,
            "limit": limit,
            "offset": offset,
        },
    )
