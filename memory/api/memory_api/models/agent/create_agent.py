from uuid import UUID


def create_agent_query(
    agent_id: UUID, name: str, about: str, model: str = "julep-ai/samantha-1-turbo"
):
    assert model in ["julep-ai/samantha-1", "julep-ai/samantha-1-turbo"]

    return f"""
    {{
        # First ensure that the agent doesn't exist
        input[agent_id] <- [[to_uuid("{agent_id}")]]

        search[collect(agent_id)] :=
            input[agent_id],
            *agents{{
                agent_id,
            }}

        ?[found] :=
            search[found],
            assert(length(found) == 0, 'user already exists')

    }} {{
        # Then create the agent
        ?[agent_id, model, name, about, created_at, updated_at] <- [
            ["{agent_id}", "{model}", "{name}", "{about}", now(), now()]
        ]
        
        :put agents {{
            agent_id =>
            model,
            name,
            about,
            created_at,
            updated_at,
        }}

    }} {{
        # Create default agent settings
        ?[
            agent_id,
            frequency_penalty,
            presence_penalty,
            length_penalty,
            repetition_penalty,
            top_p,
            temperature
        ] <- [[
            "{agent_id}",
            0.0,
            0.0,
            1.0,
            1.0,
            1.0,
            0.0,
        ]]

        :put agent_default_settings {{
            agent_id =>
            frequency_penalty,
            presence_penalty,
            length_penalty,
            repetition_penalty,
            top_p,
            temperature
        }}
    }}"""
