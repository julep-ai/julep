import logging

logger = logging.getLogger(__name__)

create_agents_relation_query = """
:create agents {
    agent_id: Uuid,
    =>
    name: String,
    about: String,
    created_at: Float,
}
"""


def init(client):
    sep = "\n}\n\n{\n"
    joined_queries = sep.join([create_agents_relation_query])
    query = f"{{ {joined_queries} }}"

    try:
        client.run(query)

    except Exception as e:
        logger.exception(e)
