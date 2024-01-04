from uuid import UUID


def create_agent_query(
    agent_id: UUID, name: str, about: str, model: str = "julep-ai/samantha-1-turbo"
):
    assert model in ["julep-ai/samantha-1", "julep-ai/samantha-1-turbo"]

    return f"""
    {{
        # Create default agent settings
        ?[agent_id] <- [["{agent_id}"]]

        :insert agent_default_settings {{
            agent_id
        }}
    }} {{
        # create the agent
        ?[agent_id, model, name, about] <- [
            ["{agent_id}", "{model}", "{name}", "{about}"]
        ]

        :insert agents {{
            agent_id =>
            model,
            name,
            about,
        }}
        :returning
    }}"""
