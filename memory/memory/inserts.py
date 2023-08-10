import json
from textwrap import dedent
from uuid import uuid4, UUID

from .cozo import client
from .queries import get_user_by_email


def create_character(
    name: str,
    is_human: bool,
    about: str = "",
    model: str = None,
):
    character_id: UUID = uuid4()
    model_or_null = f'"{model}"' if model is not None else "null"
    inp = f'["{character_id}", "{name}", {str(is_human).lower()}, "{about}", {model_or_null}]'

    query = dedent(
        f"""
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
    """
    )

    character_data = dict(
        character_id=character_id,
        name=name,
        is_human=is_human,
        about=about,
        model=model,
    )

    return character_data


def create_session(email: str, vocode_conversation_id: str, situation: str):
    user_details = get_user_by_email(email)
    character_id = user_details["character_id"]
    assistant_id = user_details["assistant_id"]

    session_id = str(uuid4())
    metadata = dict(vocode_conversation_id=vocode_conversation_id)
    metadata_str = json.dumps(metadata)

    client.run(
        dedent(
            f"""
    ?[session_id, situation, metadata] <- [[
        to_uuid("{session_id}"),
        "{situation}",
        {metadata_str},
    ]]
    :put sessions {{
        session_id, situation, metadata
    }}
    """
        )
    )

    client.run(
        dedent(
            f"""
    ?[session_id, character_id] <- [
        [to_uuid("{session_id}"), to_uuid("{character_id}")],   
        [to_uuid("{session_id}"), to_uuid("{assistant_id}")],   
    ]
    :put session_characters {{
        session_id, character_id
    }}
    """
        )
    )

    return dict(session_id=session_id, summary="", situation=situation)


def add_session_characters(session_id: UUID, *character_ids):
    assert character_ids
    c_ids = [f'[to_uuid("{c_id}")]' for c_id in character_ids]

    c_ids = ", ".join(c_ids)

    query = dedent(
        f"""
    c_ids[id] <- [{c_ids}]
    ?[session_id, character_id] := c_ids[character_id], session_id = "{session_id}"

    :put session_characters {{
        session_id,
        character_id
    }}"""
    )

    return client.run(query)


def add_entries(session_id: str, entries: list[dict]):
    entries_str = ""

    for entry in entries:
        role = entry["role"]
        content = entry["content"]

        name = entry.get("name")
        name = f'"{name}"' if name else "null"

        entries_str += (
            f'[to_uuid("{session_id}"), "{role}", {name}, "{content}"],\n'
        )

    query = f"""
    ?[
        session_id,
        role,
        name,
        content,
    ] <- [
        {entries_str}
    ]
    
    :put entries {{
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
    query = dedent(
        f"""
    ?[email, character_id, assistant_id] <- [
        ["{email}", "{character_id}", "{assistant_id}"]
    ]
    
    :put users {{
        email,
        character_id,
        assistant_id,
    }}"""
    )

    return client.run(query)
