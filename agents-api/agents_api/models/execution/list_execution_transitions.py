from uuid import UUID

from ..utils import cozo_query


@cozo_query
def list_execution_transition_query(execution_id: UUID) -> tuple[str, dict]:

    query = """
{
    ?[transition_id, type, from, to, output, updated_at, created_at] := *transitions {
        execution_id: to_uuid($execution_id),
        transition_id,
        type,
        from,
        to,
        output,
        updated_at,
        created_at,
    }
    :limit 100
    :offset 0
}
"""
    return (
        query,
        {
            "execution_id": str(execution_id),
        },
    )
