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
def search_docs_by_embedding(
    *,
    developer_id: UUID,
    owners: list[tuple[Literal["user", "agent"], UUID]],
    query_embedding: list[float],
    k: int = 3,
    confidence: float = 0.5,
    ef: int = 50,
    mmr_strength: float = 0.0,
    embedding_size: int = 1024,
    ann_threshold: int = 1_000_000,
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, dict]:
    """
    Searches for document snippets in CozoDB by embedding query.

    Parameters:
        owner_type (Literal["user", "agent"]): The type of the owner of the documents.
        owner_id (UUID): The unique identifier of the owner.
        query_embedding (list[float]): The embedding vector of the query.
        k (int, optional): The number of nearest neighbors to retrieve. Defaults to 3.
        confidence (float, optional): The confidence threshold for filtering results. Defaults to 0.8.
        mmr_lambda (float, optional): The lambda parameter for MMR. Defaults to 0.25.
        embedding_size (int): Embedding vector length
        metadata_filter (dict[str, Any]): Dictionary to filter agents based on metadata.
    """

    assert len(query_embedding) == embedding_size
    assert sum(query_embedding)
    assert 0 <= mmr_strength < 1, "MMR strength must be in [0, 1) interval"

    mmr_lambda: float = 1 - mmr_strength

    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    owners: list[list[str]] = [
        [owner_type, str(owner_id)] for owner_type, owner_id in owners
    ]

    # Calculate the search radius based on confidence level
    radius: float = 1.0 - confidence

    determine_knn_ann_query = f"""
        owners[owner_type, owner_id] <- $owners
        snippet_counter[count(item)] :=
            owners[owner_type, owner_id_str],
            owner_id = to_uuid(owner_id_str),
            *docs {{
                owner_type,
                owner_id,
                doc_id: item,
                metadata,
            }}
            {', ' + metadata_filter_str if metadata_filter_str.strip() else ''}

        ?[use_ann] := 
            snippet_counter[count],
            count > {ann_threshold},
            use_ann = true

        :limit 1
        :create _determine_knn_ann {{
            use_ann
        }}
    """

    # Construct the datalog query for searching document snippets
    search_query = f"""
        # %debug _determine_knn_ann
        %if {{ 
            ?[use_ann] := *_determine_knn_ann{{ use_ann }}
        }}

        %then {{
            owners[owner_type, owner_id] <- $owners
            input[
                owner_type,
                owner_id,
                query_embedding,
            ] :=
                owners[owner_type, owner_id_str],
                owner_id = to_uuid(owner_id_str),
                query_embedding = vec($query_embedding)

            # Search for documents by owner
            ?[
                doc_id,
                index,
                title,
                content,
                distance,
            ] :=
                # Get input values
                input[owner_type, owner_id, query],

                # Restrict the search to all documents that match the owner
                *docs {{
                    owner_type,
                    owner_id,
                    doc_id,
                    title,
                }},

                # Search for snippets in the embedding space
                ~snippets:embedding_space {{
                    doc_id,
                    index,
                    content
                    |
                    query: query,
                    k: {k*(3 if mmr_strength else 1)},   # Get more candidates for diversity
                    ef: {ef},
                    radius: {radius},
                    bind_distance: distance,
                }}

            :create _search_result {{
                doc_id,
                index,
                title,
                content,
                distance,
            }}
        }}

        %else {{
            owners[owner_type, owner_id] <- $owners
            input[
                owner_type,
                owner_id,
                query_embedding,
            ] :=
                owners[owner_type, owner_id_str],
                owner_id = to_uuid(owner_id_str),
                query_embedding = vec($query_embedding)

            # Search for documents by owner
            ?[
                doc_id,
                index,
                title,
                content,
                distance,
            ] :=
                # Get input values
                input[owner_type, owner_id, query],

                # Restrict the search to all documents that match the owner
                *docs {{
                    owner_type,
                    owner_id,
                    doc_id,
                    title,
                }},

                # Search for snippets in the embedding space
                *snippets {{
                    doc_id,
                    index,
                    content,
                    embedding,
                }},
                !is_null(embedding),
                distance = cos_dist(query, embedding),
                distance <= {radius}

            :limit {k*(3 if mmr_strength else 1)}   # Get more candidates for diversity

            :create _search_result {{
                doc_id,
                index,
                title,
                content,
                distance,
            }}
        }}
        %end
    """

    normal_interim_query = f"""
        owners[owner_type, owner_id] <- $owners

        ?[
            owner_type,
            owner_id,
            doc_id,
            snippet_data,
            distance,
            mmr_score,
            title,
        ] := 
            owners[owner_type, owner_id_str],
            owner_id = to_uuid(owner_id_str),
            *_search_result{{ doc_id, index, title, content, distance }},
            mmr_score = distance,
            snippet_data = [index, content]

        # Sort the results by distance to find the closest matches
        :sort -mmr_score
        :limit {k*(3 if mmr_strength else 1)}   # Get more candidates for diversity

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

    mmr_interim_query = f"""
        owners[owner_type, owner_id] <- $owners

        # Calculate the min distance between every doc and every snippet being compared
        intersnippet_distance[
            doc_id,
            index1,
            min(dist)
        ] :=
            *_search_result{{ doc_id: doc_id2, index: index2 }},
            *snippets {{
                doc_id,
                index: index1,
                embedding: embedding1
            }},
            *snippets {{
                doc_id: doc_id2,
                index: index2,
                embedding: embedding2
            }},
            is_null(embedding1) == false,
            is_null(embedding2) == false,

            # When doc_id == doc_id2, dont compare the same snippet
            doc_id != doc_id2 || index1 != index2,
            dist = cos_dist(embedding1, embedding2)


        apply_mmr[
            doc_id,
            title,
            snippet_data,
            distance,
            mmr_score,
        ] :=
            *_search_result{{ doc_id, index, title, content, distance: original_distance }},
            intersnippet_distance[doc_id, index, intersnippet_distance],
            mmr_score = ({mmr_lambda} * original_distance) - ((1.0 - {mmr_lambda}) * intersnippet_distance),
            distance = max(0.0, min(1.0 - mmr_score, 1.0)),
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
            owners[owner_type, owner_id_str],
            owner_id = to_uuid(owner_id_str),
            
            apply_mmr[
                doc_id,
                title,
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
        n[
            doc_id,
            owner_type,
            owner_id,
            unique(snippet_data),
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
            }

        m[
            doc_id,
            owner_type,
            owner_id,
            collect(snippet),
            distance,
            title,
        ] := 
            n[
                doc_id,
                owner_type,
                owner_id,
                snippet_data,
                distance,
                title,
            ],
            snippet = {
                "index": snippet_datum->0,
                "content": snippet_datum->1
            },
            snippet_datum in snippet_data

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

    verify_query = "}\n\n{".join(
        [
            verify_developer_id_query(developer_id),
            *[
                verify_developer_owns_resource_query(
                    developer_id, f"{owner_type}s", **{f"{owner_type}_id": owner_id}
                )
                for owner_type, owner_id in owners
            ],
        ]
    )

    query = f"""
        {{ {verify_query} }}
        {{ {determine_knn_ann_query} }}
        {search_query}
        {{ {normal_interim_query if mmr_strength == 0.0 else mmr_interim_query} }}
        {{ {collect_query} }}
    """

    return (
        query,
        {
            "owners": owners,
            "query_embedding": query_embedding,
        },
    )
