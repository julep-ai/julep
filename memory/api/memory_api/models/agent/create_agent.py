from uuid import UUID


def create_agent_query(agent_id: UUID, name: str, about: str):
    return f"""
        ?[agent_id, name, about, created_at] <- [
            ["{agent_id}", "{name}", "{about}", now()]
        ]
        
        :put agents {{
            agent_id =>
            name,
            about,
            created_at,
        }}"""
