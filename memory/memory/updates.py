from textwrap import dedent
from uuid import UUID

from .cozo import client


def update_session_situation(
    session_id: UUID,
    situation: str,
):
    query = dedent(
        f"""
    ?[
        session_id,
        updated_at,
        situation,
    ] <- [[
      "{session_id}",
      [floor(now()), true],
      "{situation}",
    ]]
    
    :put sessions {{
        session_id,
        updated_at,
        situation,
    }}
    """
    )

    return client.run(query)
