from typing import Literal
from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def delete_docs_by_id_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    doc_id: UUID,
) -> tuple[str, dict]:
    """Constructs and returns a datalog query for deleting documents and associated information snippets.

    This function targets the 'cozodb' database, allowing for the removal of documents and their related information snippets based on the provided document ID and owner (user or agent).

    Parameters:
        owner_type (Literal["user", "agent"]): The type of the owner, either 'user' or 'agent'.
        owner_id (UUID): The UUID of the owner.
        doc_id (UUID): The UUID of the document to be deleted.
        client (CozoClient): An instance of the CozoClient to execute the query.

    Returns:
        pd.DataFrame: The result of the executed datalog query.
    """
    # Convert UUID parameters to string format for use in the datalog query
    owner_id = str(owner_id)
    doc_id = str(doc_id)

    # The following query is divided into two main parts:
    # 1. Deleting information snippets associated with the document
    # 2. Deleting the document itself from the owner's collection
    query = f"""
    {{
        # This section constructs the subquery for identifying and deleting all information snippets associated with the given document ID.
        # Delete snippets
        input[doc_id] <- [[to_uuid($doc_id)]]
        ?[doc_id, snippet_idx] :=
            input[doc_id],
            *information_snippets {{
                doc_id,
                snippet_idx,
            }}

        :delete information_snippets {{
            doc_id,
            snippet_idx
        }}
    }} {{
        # This section constructs the subquery for deleting the document from the specified owner's (user or agent) document collection.
        # Delete the docs
        ?[doc_id, {owner_type}_id] <- [[
            to_uuid($doc_id),
            to_uuid($owner_id),
        ]]

        :delete {owner_type}_docs {{
            doc_id,
            {owner_type}_id,
        }}
        :returning
    }}"""

    return (query, {"doc_id": doc_id, "owner_id": owner_id})
