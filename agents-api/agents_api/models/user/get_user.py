from uuid import UUID

from beartype import beartype


from ..utils import cozo_query


@cozo_query
@beartype
def get_user_query(
    developer_id: UUID,
    user_id: UUID,
) -> tuple[str, dict]:
    # Convert UUIDs to strings for query compatibility.
    user_id = str(user_id)
    developer_id = str(developer_id)

    query = """
    input[developer_id, user_id] <- [[to_uuid($developer_id), to_uuid($user_id)]]

    ?[
        id,
        name,
        about,
        created_at,
        updated_at,
        metadata,
    ] := input[developer_id, id],
        *users {
            user_id: id,
            developer_id,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        }"""

    return (query, {"developer_id": developer_id, "user_id": user_id})
