"""This module contains functions for searching documents in the CozoDB based on embedding queries."""

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
def search_docs_by_embedding(
    *,
    developer_id: UUID,
    owners: list[tuple[Literal["user", "agent"], UUID]],
    query_embedding: list[float],
    k: int = 3,
    confidence: float = 0.7,
    ef: int = 128,
    mmr_lambda: float = 0.25,
    embedding_size: int = 1024,
) -> tuple[list[str], dict]:
    """
    Searches for document snippets in CozoDB by embedding query.

    Parameters:
    - owner_type (Literal["user", "agent"]): The type of the owner of the documents.
    - owner_id (UUID): The unique identifier of the owner.
    - query_embedding (list[float]): The embedding vector of the query.
    - k (int, optional): The number of nearest neighbors to retrieve. Defaults to 3.
    - confidence (float, optional): The confidence threshold for filtering results. Defaults to 0.8.
    - mmr_lambda (float, optional): The lambda parameter for MMR. Defaults to 0.25.
    """

    assert len(query_embedding) == embedding_size
    assert sum(query_embedding)

    owners: list[list[str]] = [
        [owner_type, str(owner_id)] for owner_type, owner_id in owners
    ]

    # Calculate the search radius based on confidence level
    radius: float = 1.0 - confidence

    # Construct the datalog query for searching document snippets
    interim_query = f"""
        owners[owner_type, owner_id] <- $owners
        input[
            owner_type,
            owner_id,
            query_embedding,
        ] :=
            owners[owner_type, owner_id_str],
            owner_id = to_uuid(owner_id_str),
            query_embedding = vec($query_embedding)

        candidate[doc_id] :=
            input[owner_type, owner_id, _],
            *docs {{
                owner_type,
                owner_id,
                doc_id
            }}

        intersnippet_distance[
            doc_id,
            index1,
            min(dist)
        ] :=
            *snippets {{
                doc_id,
                index: index1,
                embedding: embedding1
            }},
            *snippets {{
                doc_id,
                index: index2,
                embedding: embedding2
            }},
            index1 < index2,
            dist = cos_dist(embedding1, embedding2)

        doclength[doc_id, max(index)] :=
            *snippets {{
                doc_id,
                index,
            }}

        get_intersnippet[doc_id, index, distance] :=
            intersnippet_distance[doc_id, _, distance]

        get_intersnippet[doc_id, index, distance] :=
            not intersnippet_distance[doc_id, _, distance],
            distance = 0.0

        search_result[
            doc_id,
            content,
            index,
            distance,
        ] :=
            input[_, __, query],
            candidate[doc_id],
            ~snippets:embedding_space {{
                doc_id,
                index,
                content
                |
                query: query,
                k: {k*2},
                ef: {ef},
                radius: {radius},
                bind_distance: distance,
            }}

        apply_mmr[
            doc_id,
            snippet_data,
            distance,
            mmr_score,
        ] :=
            search_result[doc_id, content, index, distance],
            get_intersnippet[doc_id, index, intersnippet_distance],
            mmr_score = {mmr_lambda} * (distance - (1.0 - {mmr_lambda}) * intersnippet_distance),
            snippet_data = [index, content]

        ?[
            owner_type,
            owner_id,
            doc_id,
            snippet_data,
            distance,
            mmr_score,
            title,
        ] := 
            *docs {{
                owner_type,
                owner_id,
                doc_id,
                title,
            }},
            apply_mmr[
                doc_id,
                snippet_data,
                distance,
                mmr_score,
            ]

        # Sort the results by distance to find the closest matches
        :sort -mmr_score
        :limit {k}

        :create _interim {{
            owner_type,
            owner_id,
            doc_id,
            snippet_data,
            distance,
            mmr_score,
            title,
        }}
    """

    collect_query = """
        m[
            doc_id,
            owner_type,
            owner_id,
            collect(snippet),
            distance,
            title,
        ] := 
            *_interim {
                owner_type,
                owner_id,
                doc_id,
                snippet_data,
                distance,
                title,
            }, snippet = {
                "index": snippet_data->0,
                "content": snippet_data->1,
            }

        ?[
            id,
            owner_type,
            owner_id,
            snippets,
            distance,
            title,
        ] := m[
            id,
            owner_type,
            owner_id,
            snippets,
            distance,
            title,
        ]
    """

    queries = [
        verify_developer_id_query(developer_id),
        *[
            verify_developer_owns_resource_query(
                developer_id, f"{owner_type}s", **{f"{owner_type}_id": owner_id}
            )
            for owner_type, owner_id in owners
        ],
        interim_query,
        collect_query,
    ]

    return (
        queries,
        {
            "owners": owners,
            "query_embedding": query_embedding,
        },
    )
