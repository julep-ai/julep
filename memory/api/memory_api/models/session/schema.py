import logging
from memory_api.clients.cozo import client


logger = logging.getLogger(__name__)

create_sessions_relation_query = """
:create sessions {
    session_id: Uuid,
    updated_at: Validity default [floor(now()), true],
    =>
    situation: String,
    summary: String?,
    created_at: Float,
}
"""

create_session_lookup_relation_query = """
:create session_lookup {
    agent_id: Uuid,
    user_id: Uuid? default null,
    session_id: Uuid,
}
"""


def init():
    sep = "\n}\n\n{\n"
    joined_queries = sep.join(
        [
            create_sessions_relation_query,
            create_session_lookup_relation_query,
        ]
    )

    query = f"{{ {joined_queries} }}"

    try:
        client.run(query)

    except Exception as e:
        logger.exception(e)
