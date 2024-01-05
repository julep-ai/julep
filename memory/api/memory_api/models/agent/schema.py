import logging

logger = logging.getLogger(__name__)

create_agents_relation_query = """
:create agents {
    agent_id: Uuid,
    =>
    name: String,
    about: String,
    model: String default 'julep-ai/samantha-1-turbo',
    created_at: Float default now(),
    updated_at: Float default now(),
}
"""

create_model_settings_relation_query = """
:create agent_default_settings {
    agent_id: Uuid,
    =>
    frequency_penalty: Float default 0.0,
    presence_penalty: Float default 0.0,
    length_penalty: Float default 1.0,
    repetition_penalty: Float default 1.0,
    top_p: Float default 0.95,
    temperature: Float default 0.7,
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
