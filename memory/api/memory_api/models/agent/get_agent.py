from uuid import UUID


def get_agent_query(agent_id: UUID):
    return f"""
        input[agent_id] <- [[to_uuid("{agent_id}")]]

        ?[
            id,
            model,
            name,
            about,
            created_at,
            updated_at,
            default_settings,
        ] := input[id],
            *agents {{
                agent_id: id,
                model,
                name,
                about,
                created_at,
                updated_at,
            }},
            *agent_default_settings {{
                agent_id,
                frequency_penalty,
                presence_penalty,
                length_penalty,
                repetition_penalty,
                top_p,
                temperature,
            }},
            default_settings = {{
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "length_penalty": length_penalty,
                "repetition_penalty": repetition_penalty,
                "top_p": top_p,
                "temperature": temperature,
            }}
    """
