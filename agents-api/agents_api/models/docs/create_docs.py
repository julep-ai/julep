from typing import Literal
from uuid import UUID

from beartype import beartype

from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import cozo_query
from ...common.utils.datetime import utcnow


@cozo_query
@beartype
def create_docs_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    id: UUID,
    title: str,
    content: list[str] | str,
    metadata: dict = {},
):
    """
    Constructs and executes a datalog query to create a new document and its associated snippets in the 'cozodb' database.

    Parameters:
    - owner_type (Literal["user", "agent"]): The type of the owner of the document.
    - owner_id (UUID): The UUID of the document owner.
    - id (UUID): The UUID of the document to be created.
    - title (str): The title of the document.
    - content (str): The content of the document, which will be split into snippets.
    - metadata (dict): Metadata associated with the document. Defaults to an empty dictionary.

    Returns:
    pd.DataFrame: A DataFrame containing the results of the query execution.
    """

    if isinstance(content, str):
        content = [content]

    created_at: float = utcnow().timestamp()
    snippet_cols, snippet_rows = "", []

    # Process each content snippet and prepare data for the datalog query.
    for snippet_idx, snippet in enumerate(content):
        snippet_cols, new_snippet_rows = cozo_process_mutate_data(
            dict(
                doc_id=str(id),
                snippet_idx=snippet_idx,
                title=title,
                snippet=snippet,
            )
        )

        snippet_rows += new_snippet_rows

    # Construct the datalog query for creating the document and its snippets.
    query = f"""
    {{
        # This query creates a new document and its associated snippets in the database.
        # Section to create the document in the database
        ?[{owner_type}_id, doc_id, created_at, metadata] <- [[
            to_uuid($owner_id),
            to_uuid($id),
            $created_at,
            $metadata,
        ]]

        :insert {owner_type}_docs {{
            {owner_type}_id, doc_id, created_at, metadata,
        }}
    }} {{
        # Section to create and associate snippets with the document
        ?[{snippet_cols}] <- $snippet_rows

        :insert information_snippets {{
            {snippet_cols}
        }}
    }} {{
        # Section to return the created document and its snippets
        ?[{owner_type}_id, doc_id, created_at, metadata] <- [[
            to_uuid($owner_id),
            to_uuid($id),
            $created_at,
            $metadata,
        ]]
    }}"""

    # Execute the constructed datalog query and return the results as a DataFrame.
    return (
        query,
        {
            "owner_id": str(owner_id),
            "id": str(id),
            "created_at": created_at,
            "metadata": metadata,
            "snippet_rows": snippet_rows,
        },
    )
