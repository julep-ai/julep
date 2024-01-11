from uuid import UUID


def get_agent_query(developer_id: UUID, agent_id: UUID):
    return f"""
    {{
        input[agent_id, developer_id] <- [[to_uuid("{agent_id}"), to_uuid("{developer_id}")]]

        ?[
            id,
            model,
            name,
            about,
            created_at,
            updated_at,
            default_settings,
        ] := input[id, developer_id],
            *agents {{
                developer_id,
                agent_id: id,
                model,
                name,
                about,
                created_at,
                updated_at,
            }},
            *agent_default_settings {{
                agent_id: id,
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
    }}
    """
