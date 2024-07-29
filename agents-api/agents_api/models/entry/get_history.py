from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import History
from ...common.utils.cozo import uuid_int_list_to_uuid4
from ..utils import (
    cozo_query,
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
    History,
    one=True,
    transform=lambda d: {
        "entries": [
            {
                # This is needed because cozo has a bug:
                # https://github.com/cozodb/cozo/issues/269
                "id": uuid_int_list_to_uuid4(entry.pop("id")),
                **entry,
            }
            for entry in d.pop("entries")
        ],
        **d,
    },
)
@cozo_query
@beartype
def get_history(
    *,
    developer_id: UUID,
    session_id: UUID,
    allowed_sources: list[str] = ["api_request", "api_response"],
) -> tuple[str, dict]:
    developer_id = str(developer_id)
    session_id = str(session_id)

    history_query = """
        session_entries[collect(entry)] :=
            *entries {
                session_id,
                entry_id,
                role,
                name,
                content,
                source,
                token_count,
                created_at,
                timestamp,
            },
            source in $allowed_sources,
            session_id = to_uuid($session_id),
            entry = {
                "session_id":  session_id,
                "id":    entry_id,
                "role":        role,
                "name":        name,
                "content":     content,
                "source":      source,
                "token_count": token_count,
                "created_at":  created_at,
                "timestamp":   timestamp
            }

        session_relations[collect(relation)] :=
            *entries {
                session_id,
                entry_id: head,
                source,
            },
            source in $allowed_sources,
            session_id = to_uuid($session_id),

            *relations {
                head,
                relation,
                tail,
            },

            relation = {
                "head": head,
                "relation": relation,
                "tail": tail,
            }


        session_relations[collect(relation)] :=
            *entries {
                session_id,
                entry_id: tail,
                source,
            },
            source in $allowed_sources,
            session_id = to_uuid($session_id),

            *relations {
                head,
                relation,
                tail,
            },

            relation = {
                "head": head,
                "relation": relation,
                "tail": tail,
            }


        ?[entries, relations, session_id, created_at] :=
            session_entries[entries],
            session_relations[relations],
            session_id = to_uuid($session_id),
            created_at = now()
     """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        history_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (query, {"session_id": session_id, "allowed_sources": allowed_sources})
