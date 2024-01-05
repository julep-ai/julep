import logging


logger = logging.getLogger(__name__)

create_entries_relation_query = """
:create entries {
    session_id: Uuid,
    entry_id: Uuid default random_uuid_v4(),
    source: String,
    role: String,
    name: String? default null,
    =>
    content: String,
    token_count: Int,
    tokenizer: String,
    created_at: Float default now(),
}
"""


def init(client):
    sep = "\n}\n\n{\n"
    joined_queries = sep.join([create_entries_relation_query])
    query = f"{{ {joined_queries} }}"

    try:
        client.run(query)

    except Exception as e:
        logger.exception(e)
