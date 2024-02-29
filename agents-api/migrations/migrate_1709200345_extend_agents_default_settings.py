# /usr/bin/env python3

MIGRATION_ID = "extend_agents_default_settings"
CREATED_AT = 1709200345.052425


extend_agents_default_settings = {
    "up": """
    ?[
        agent_id,
        frequency_penalty,
        presence_penalty,
        length_penalty,
        repetition_penalty,
        top_p,
        temperature,
        min_p,
    ] := *agent_default_settings{
        agent_id,
        frequency_penalty,
        presence_penalty,
        length_penalty,
        repetition_penalty,
        top_p,
        temperature,
    }, min_p = 0.01

    :replace agent_default_settings {
        agent_id: Uuid,
        =>
        frequency_penalty: Float default 0.0,
        presence_penalty: Float default 0.0,
        length_penalty: Float default 1.0,
        repetition_penalty: Float default 1.0,
        top_p: Float default 0.95,
        temperature: Float default 0.7,
        min_p: Float default 0.01,
    }
    """,
    "down": """
    ?[
        agent_id,
        frequency_penalty,
        presence_penalty,
        length_penalty,
        repetition_penalty,
        top_p,
        temperature,
    ] := *agent_default_settings{
        agent_id,
        frequency_penalty,
        presence_penalty,
        length_penalty,
        repetition_penalty,
        top_p,
        temperature,
    }

    :replace agent_default_settings {
        agent_id: Uuid,
        =>
        frequency_penalty: Float default 0.0,
        presence_penalty: Float default 0.0,
        length_penalty: Float default 1.0,
        repetition_penalty: Float default 1.0,
        top_p: Float default 0.95,
        temperature: Float default 0.7,
    }
    """,
}


queries_to_run = [
    extend_agents_default_settings,
]


def up(client):
    client.run(extend_agents_default_settings["up"])


def down(client):
    client.run(extend_agents_default_settings["down"])
