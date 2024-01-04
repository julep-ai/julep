from uuid import UUID


def update_agent_query(agent_id: UUID, name: str, about: str, model: str = "julep-ai/samantha-1-turbo"):
    agent_id = str(agent_id)

    return f"""
        # update the agent
        ?[agent_id, name, about, model, updated_at] <- [
            [to_uuid("{agent_id}"), "{name}", "{about}", "{model}", now()]
        ]

        :update agents {{
            agent_id =>
            name,
            about,
            model,
            updated_at,
        }}
        :returning
    """
