import logging
from memory_api.clients.cozo import client


logger = logging.getLogger(__name__)

create_users_relation_query = """
:create users {
    user_id: Uuid,
    =>
    name: String,
    about: String,
    created_at: Float,
}
"""


def init():
    sep = "\n}\n\n{\n"
    joined_queries = sep.join([create_users_relation_query])
    query = f"{{ {joined_queries} }}"

    try:
        client.run(query)

    except Exception as e:
        logger.exception(e)
