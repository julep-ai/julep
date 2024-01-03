import logging


logger = logging.getLogger(__name__)

create_users_relation_query = """
:create users {
    user_id: Uuid,
    =>
    name: String,
    about: String,
    created_at: Float,
    updated_at: Float,
}
"""


def init(client):
    sep = "\n}\n\n{\n"
    joined_queries = sep.join([create_users_relation_query])
    query = f"{{ {joined_queries} }}"

    try:
        client.run(query)

    except Exception as e:
        logger.exception(e)
