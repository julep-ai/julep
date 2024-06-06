from typing import Literal, Dict, Any
from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def create_execution_transition_query(
    developer_id: UUID,
    execution_id: UUID,
    transition_id: UUID,
    type_: Literal["finished", "waiting", "error", "step"],
    from_: tuple[str, int],
    to: tuple[str, int] | None,
    output: Dict[str, Any],
) -> tuple[str, dict]:
    # TODO: Check for agent in developer ID; Assert whether dev can access agent and by relation the task
    # TODO: Check for task and execution

    query = """
{
    ?[execution_id, transition_id, type, from, to, output] <- [[
        to_uuid($execution_id),
        to_uuid($transition_id),
        $type,
        $from,
        $to,
        $output,
    ]]

    :insert transitions {
        execution_id, transition_id, type, from, to, output
    }
}
"""
    return (
        query,
        {
            "execution_id": str(execution_id),
            "transition_id": str(transition_id),
            "type": type_,
            "from": from_,
            "to": to,
            "output": output,
        },
    )
