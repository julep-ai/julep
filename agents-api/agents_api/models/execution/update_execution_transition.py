from uuid import UUID

from beartype import beartype

from agents_api.common.utils.datetime import utcnow

from ..utils import cozo_query
from ...common.utils.cozo import cozo_process_mutate_data


@cozo_query
@beartype
def update_execution_transition_query(
    execution_id: UUID, transition_id: UUID, **update_data
) -> tuple[str, dict]:
    # Only output and type can be updated
    assert update_data.keys() <= {
        "output",
        "type",
    }, "Only output and type can be updated for a transition"

    transition_update_cols, transition_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v, in update_data.items() if v is not None},
            "execution_id": str(execution_id),
            "transition_id": str(transition_id),
            "updated_at": utcnow().timestamp(),
        }
    )
    query = f"""
    {{
        input[{transition_update_cols}] <- $transition_update_vals

        ?[{transition_update_cols}] := input[{transition_update_cols}],
        *transitions {{
            execution_id: to_uuid($execution_id),
            transition_id: to_uuid($transition_id),
        }}

        :update transitions {{
            {transition_update_cols}
        }}
        :returning
    }}

"""

    return (
        query,
        {
            "transition_update_vals": transition_update_vals,
            "execution_id": str(execution_id),
            "transition_id": str(transition_id),
        },
    )
