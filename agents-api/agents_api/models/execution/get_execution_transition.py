from uuid import UUID

from ..utils import cozo_query


@cozo_query
def get_execution_transition_query(
    execution_id: UUID, transition_id: UUID, developer_id: UUID
) -> tuple[str, dict]:

    query = """"""
    return (
        query,
        {
            "execution_id": str(execution_id),
            "transition_id": str(transition_id),
            "developer_id": str(developer_id),
        },
    )
