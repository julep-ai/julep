"""Module for retrieving document snippets from the CozoDB based on document IDs."""

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
    wrap_in_class,
)


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    Doc,
    one=True,
    transform=lambda d: {
        "content": [s[1] for s in sorted(d["snippet_data"], key=lambda x: x[0])],
        **d,
    },
)
@cozo_query
@beartype
def get_doc(
    *,
    developer_id: UUID,
    doc_id: UUID,
) -> tuple[list[str], dict]:
    """
    Retrieves snippets of documents by their ID from the CozoDB.

    Parameters:
        doc_id (UUID): The unique identifier of the document.
        client (CozoClient, optional): The CozoDB client instance. Defaults to a pre-configured client.

    Returns:
        pd.DataFrame: A DataFrame containing the document snippets and related metadata.
    """

    doc_id = str(doc_id)

    get_query = """
        input[doc_id] <- [[to_uuid($doc_id)]]
        snippets[collect(snippet_data)] :=
            input[doc_id],
            *snippets {
                doc_id,
                index,
                content,
            },
            snippet_data = [index, content]

        ?[
            id,
            title,
            snippet_data,
            created_at,
            metadata,
        ] := input[id],
            *docs {
                doc_id: id,
                title,
                created_at,
                metadata,
            },
            snippets[snippet_data]
    """

    queries = [
        verify_developer_id_query(developer_id),
        get_query,
    ]

    return (queries, {"doc_id": doc_id})
