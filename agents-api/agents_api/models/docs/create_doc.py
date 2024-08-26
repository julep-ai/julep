from typing import Any, Literal, TypeVar
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateDocRequest, Doc
from ...common.utils.cozo import cozo_process_mutate_data
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
    one=True,
    transform=lambda d: {
        "id": UUID(d["doc_id"]),
        **d,
    },
)
@cozo_query
@beartype
def create_doc(
    *,
    developer_id: UUID,
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    doc_id: UUID | None = None,
    data: CreateDocRequest,
) -> tuple[list[str], dict]:
    """
    Constructs and executes a datalog query to create a new document and its associated snippets in the 'cozodb' database.

    Parameters:
    - owner_type (Literal["user", "agent"]): The type of the owner of the document.
    - owner_id (UUID): The UUID of the document owner.
    - id (UUID): The UUID of the document to be created.
    - data (CreateDocRequest): The content of the document.
    """

    doc_id = str(doc_id or uuid4())
    owner_id = str(owner_id)

    if isinstance(data.content, str):
        data.content = [data.content]

    data.metadata = data.metadata or {}

    doc_data = data.model_dump()
    content = doc_data.pop("content")

    doc_data["owner_type"] = owner_type
    doc_data["owner_id"] = owner_id
    doc_data["doc_id"] = doc_id

    doc_cols, doc_rows = cozo_process_mutate_data(doc_data)

    snippet_cols, snippet_rows = "", []

    # Process each content snippet and prepare data for the datalog query.
    for snippet_idx, snippet in enumerate(content):
        snippet_cols, new_snippet_rows = cozo_process_mutate_data(
            dict(
                doc_id=doc_id,
                index=snippet_idx,
                content=snippet,
            )
        )

        snippet_rows += new_snippet_rows

    create_snippets_query = f"""
        ?[{snippet_cols}] <- $snippet_rows

        :create _snippets {{ {snippet_cols} }}
        }} {{ 
        ?[{snippet_cols}] <- $snippet_rows
        :insert snippets {{ {snippet_cols} }}
        :returning
    """

    # Construct the datalog query for creating the document and its snippets.
    create_doc_query = f"""
        ?[{doc_cols}] <- $doc_rows

        :create _docs {{ {doc_cols} }}
        }} {{
        ?[{doc_cols}] <- $doc_rows
        :insert docs {{ {doc_cols} }}
        :returning
        }} {{
        snippet_rows[collect(content)] :=
            *_snippets {{
                content
            }}

        ?[{doc_cols}, content, created_at] :=
            *_docs {{ {doc_cols} }},
            snippet_rows[content],
            created_at = now()
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, f"{owner_type}s", **{f"{owner_type}_id": owner_id}
        ),
        create_snippets_query,
        create_doc_query,
    ]

    # Execute the constructed datalog query and return the results as a DataFrame.
    return (
        queries,
        {
            "doc_rows": doc_rows,
            "snippet_rows": snippet_rows,
        },
    )
