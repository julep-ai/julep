import json
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateEntryRequest, Entry, Relation
from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow
from ...common.utils.messages import content_to_json
from ..utils import (
    cozo_query,
    mark_session_updated_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
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
    Entry,
    transform=lambda d: {
        "id": UUID(d.pop("entry_id")),
        **d,
    },
)
@cozo_query
@beartype
def create_entries(
    *,
    developer_id: UUID,
    session_id: UUID,
    data: list[CreateEntryRequest],
    mark_session_as_updated: bool = True,
) -> tuple[list[str], dict]:
    developer_id = str(developer_id)
    session_id = str(session_id)

    data_dicts = [item.model_dump(exclude_unset=True) for item in data]

    for item in data_dicts:
        item["content"] = content_to_json(item["content"])
        item["session_id"] = session_id
        item["entry_id"] = item.pop("id", None) or str(uuid4())
        item["created_at"] = (item.get("created_at") or utcnow()).timestamp()

        if not item.get("token_count"):
            item["token_count"] = len(json.dumps(item)) // 3.5
            item["tokenizer"] = "character_count"

    cols, rows = cozo_process_mutate_data(data_dicts)

    # Construct a datalog query to insert the processed entries into the 'cozodb' database.
    # Refer to the schema for the 'entries' relation in the README.md for column names and types.
    create_query = f"""
        ?[{cols}] <- $rows

        :insert entries {{
            {cols}
        }}

        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        mark_session_updated_query(developer_id, session_id)
        if mark_session_as_updated
        else "",
        create_query,
    ]

    return (queries, {"rows": rows})


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(Relation)
@cozo_query
@beartype
def add_entry_relations(
    *,
    developer_id: UUID,
    data: list[Relation],
) -> tuple[list[str], dict]:
    developer_id = str(developer_id)

    data_dicts = [item.model_dump(mode="json") for item in data]
    cols, rows = cozo_process_mutate_data(data_dicts)

    create_query = f"""
        ?[{cols}] <- $rows

        :insert relations {{
            {cols}
        }}

        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        create_query,
    ]

    return (queries, {"rows": rows})
