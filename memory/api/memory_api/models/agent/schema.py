import logging

logger = logging.getLogger(__name__)

create_agents_relation_query = """
:create agents {
    agent_id: Uuid,
    =>
    model: String,
    name: String,
    about: String,
    created_at: Float,
    updated_at: Float,
}
"""

create_model_settings_relation_query = """
:create agent_default_settings {
    agent_id: Uuid,
    =>
    frequency_penalty: Float,
    presence_penalty: Float,
    length_penalty: Float,
    repetition_penalty: Float,
    top_p: Float,
    temperature: Float,
}
"""


def init(client):
    sep = "\n}\n\n{\n"
    joined_queries = sep.join(
        [
            create_agents_relation_query,
            create_model_settings_relation_query,
        ]
    )
    query = f"{{ {joined_queries} }}"

    try:
        client.run(query)

    except Exception as e:
        logger.exception(e)
