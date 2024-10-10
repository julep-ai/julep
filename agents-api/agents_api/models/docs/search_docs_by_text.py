"""This module contains functions for searching documents in the CozoDB based on embedding queries."""

import json
from typing import Any, Literal, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import DocReference
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
    DocReference,
    transform=lambda d: {
        "owner": {
            "id": d["owner_id"],
            "role": d["owner_type"],
        },
        **d,
    },
)
@cozo_query
@beartype
def search_docs_by_text(
    *,
    developer_id: UUID,
    owners: list[tuple[Literal["user", "agent"], UUID]],
    query: str,
    k: int = 3,
) -> tuple[list[str], dict]:
    """
    Searches for document snippets in CozoDB by embedding query.

    Parameters:
        owners (list[tuple[Literal["user", "agent"], UUID]]): The type of the owner of the documents.
        query (str): The query string.
        k (int, optional): The number of nearest neighbors to retrieve. Defaults to 3.
    """

    owners: list[list[str]] = [
        [owner_type, str(owner_id)] for owner_type, owner_id in owners
    ]

    # Need to use NEAR/3($query) to search for arbitrary text within 3 words of each other
    # See: https://docs.cozodb.org/en/latest/vector.html#full-text-search-fts
    query = f"NEAR/3({json.dumps(query)})"

    # Construct the datalog query for searching document snippets
    search_query = f"""
        owners[owner_type, owner_id] <- $owners
        input[
            owner_type,
            owner_id,
        ] :=
            owners[owner_type, owner_id_str],
            owner_id = to_uuid(owner_id_str)

        candidate[doc_id] :=
            input[owner_type, owner_id],
            *docs {{
                owner_type,
                owner_id,
                doc_id
            }}

        search_result[
            doc_id,
            snippet_data,
            distance,
        ] :=
            candidate[doc_id],
            ~snippets:lsh {{
                doc_id,
                index,
                content
                |
                query: $query,
                k: {k},
            }},
            distance = 10000000,  # Very large distance to depict no valid distance
            snippet_data = [index, content]

        search_result[
            doc_id,
            snippet_data,
            distance,
        ] :=
            candidate[doc_id],
            ~snippets:fts {{
                doc_id,
                index,
                content
                |
                query: $query,
                k: {k},
                score_kind: 'tf_idf',
                bind_score: score,
            }},
            distance = -score,
            snippet_data = [index, content]

        m[
            doc_id,
            collect(snippet),
            distance,
            title,
            owner_type,
            owner_id,
        ] :=
            candidate[doc_id],
            *docs {{
                owner_type,
                owner_id,
                doc_id,
                title,
            }},
            search_result [
                doc_id,
                snippet_data,
                distance,
            ],
            snippet = {{
                "index": snippet_data->0,
                "content": snippet_data->1,
            }}


        ?[
            id,
            owner_type,
            owner_id,
            snippets,
            distance,
            title,
        ] := 
            input[owner_type, owner_id],
            m[
                id,
                snippets,
                distance,
                title,
                owner_type,
                owner_id,
            ]

        # Sort the results by distance to find the closest matches
        :sort distance
        :limit {k}
    """

    queries = [
        verify_developer_id_query(developer_id),
        *[
            verify_developer_owns_resource_query(
                developer_id, f"{owner_type}s", **{f"{owner_type}_id": owner_id}
            )
            for owner_type, owner_id in owners
        ],
        search_query,
    ]

    return (
        queries,
        {"owners": owners, "query": query},
    )
