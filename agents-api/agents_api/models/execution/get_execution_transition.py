from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def get_execution_transition_query(
    execution_id: UUID, transition_id: UUID
) -> tuple[str, dict]:

    query = """
{
    ?[type, from, to, output] := *transitions {
        execution_id: to_uuid($execution_id),
        transition_id: to_uuid($transition_id),
        type,
        from,
        to,
        output,
        metadata,
        task_token,
        created_at,
        updated_at,
    }
}
"""
    return (
        query,
        {
            "execution_id": str(execution_id),
            "transition_id": str(transition_id),
        },
    )
