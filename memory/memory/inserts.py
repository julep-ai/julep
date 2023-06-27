from textwrap import dedent
from uuid import uuid4, UUID

from .cozo import client

def create_character(
    name: str,
    is_human: bool,
    about: str,
    model: str = None,
):
    character_id: UUID = uuid4()
    model_or_null = f'"{model}"' if model is not None else "null"
    inp = f'["{character_id}", "{name}", {str(is_human).lower()}, "{about}", {model_or_null}]'

    query = dedent(f"""
    ?[
        character_id,
        name,
        is_human,
        about,
        model,
    ] <- [{inp}]

    :put characters {{
        character_id,
        name,
        is_human,
        about,
        model,
    }}
    """)
    
    return character_id, client.run(query)

def create_session(situation: str):
    
    session_id: UUID = uuid4()

    query = dedent(f"""
    ?[
        session_id,
        situation,
    ] <- [[
        "{session_id}",
        "{situation}",
    ]]
    
    :put sessions {{
        session_id,
        situation,
    }}""")

    return session_id, client.run(query)

def add_session_characters(session_id: UUID, *character_ids):
    assert character_ids
    c_ids = [
        f'[to_uuid("{c_id}")]'
        for c_id in character_ids
    ]

    c_ids = ", ".join(c_ids)

    query = dedent(f"""
    c_ids[id] <- [{c_ids}]
    ?[session_id, character_id] := c_ids[character_id], session_id = "{session_id}"

    :put session_characters {{
        session_id,
        character_id
    }}""")

    return client.run(query)

def add_entries(session_id: UUID, entries: list[dict]):

    entries_str = ""
    
    for entry in entries:
        role = entry["role"]
        content = entry["content"]

        timestamp = entry.get("timestamp", "now()")
        name = entry.get("name")
        name = f'"{name}"' if name else "null"
        
        entries_str += f'[{timestamp}, "{session_id}", "{role}", {name}, "{content}"],\n'
    
    query = f"""
    ?[
        timestamp,
        session_id,
        role,
        name,
        content,
    ] <- [
        {entries_str}
    ]
    
    :put entries {{
        timestamp,
        session_id,
        role,
        name,
        content,
    }}
    """

    return client.run(query)

def create_user(
    email: str,
    character_id: UUID,
    assistant_id: UUID,
):
    query = dedent(f"""
    ?[email, character_id, assistant_id] <- [
        ["{email}", "{character_id}", "{assistant_id}"]
    ]
    
    :put users {{
        email,
        character_id,
        assistant_id,
    }}""")

    return client.run(query)