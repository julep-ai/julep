import pytest
from pycozo.client import Client
from memory_api.routers import (
    agents,
    sessions,
    users,
    entries,
    models,
    personality,
    beliefs,
    episodes,
)
from .queries import context_window_query_beliefs


client = Client()


# TODO: test cases, what should context_window_query_beliefs.replace("{session_id}", session_id) return in every case?

# 1. Session, user and character with the given IDs exist. No dialog entries
# 2. Session, user and character with the given IDs exist, one related dialog entry found
# 3. Session, user and character with the given IDs exist, more than one related dialog entry found
# 4. Session ID exists, but either user or character ID does not. No dialog entries
# 5. Session ID exists, but either user or character ID does not. One dialog entry found
# 6. Session ID exists, but either user or character ID does not. More than one dialog entry found
# 7. Session with the given ID does not exist


@pytest.fixture
def init_db(monkeypatch):
    monkeypatch.setattr(agents.db, "client", client)
    monkeypatch.setattr(sessions.db, "client", client)
    monkeypatch.setattr(users.db, "client", client)
    monkeypatch.setattr(entries.db, "client", client)
    monkeypatch.setattr(models.db, "client", client)
    monkeypatch.setattr(personality.db, "client", client)
    monkeypatch.setattr(beliefs.db, "client", client)
    monkeypatch.setattr(episodes.db, "client", client)

    agents.db.init()
    sessions.db.init()
    users.db.init()
    entries.db.init()
    models.db.init()
    personality.db.init()
    beliefs.db.init()
    episodes.db.init()


@pytest.fixture
def insert_data(init_db):
    user_id = "e920a904-9af5-4052-8f22-836be1393a04"
    character_id = "88e8fdfe-6b0a-4b86-9ea2-c93d2b42c648"
    session_id = "2e4b5200-45e3-435a-a06e-e1297b015bbf"
    insert_model_query = """
    ?[model_name, max_length, default_settings] <- [[
        "samantha-1-alpha",
        4096,
        {
            "frequency_penalty": 1,
            "max_tokens": 120,
            "repetition_penalty": 0.9,
            "temperature": 0.7,
        },
    ]]

    :put models {
        model_name,
        max_length,
        default_settings,
    }
    """
    insert_user_query = f"""
    ?[user_id, name, email, about, metadata] <- [
        ["{user_id}", "John", "john@gmail.com", "John is a good guy", {{}}]
    ]
    
    :put users {{
        user_id =>
        name,
        email,
        about,
        metadata,
    }}
    """
    insert_character_query = f"""
    ?[character_id, name, about, metadata, model] <- [
        ["{character_id}", "Samantha", "Samantha is an AI assistant", {{}}, "samantha-1-alpha"]
    ]
    
    :put characters {{
        character_id =>
        name,
        about,
        metadata,
        model,
    }}
    """
    insert_session_query = f"""
    ?[session_id, character_id, user_id, situation, metadata] <- [[
        to_uuid("{session_id}"),
        to_uuid("{character_id}"),
        to_uuid("{user_id}"),
        "you an AI assistant talking to people about life",
        {{}},
    ]]

    :put sessions {{
        character_id,
        user_id,
        session_id,
        situation,
        metadata,
    }}
    """
    client.run(insert_model_query)
    client.run(insert_user_query)
    client.run(insert_character_query)
    client.run(insert_session_query)

    return {
        "user_id": user_id,
        "character_id": character_id,
        "session_id": session_id,
    }


def test_context_window_session_does_not_exist(insert_data):
    session_id = "2e4b5200-45e3-435a-a06e-e1297b015000"
    res = client.run(context_window_query_beliefs.replace("{session_id}", session_id))

    assert len(res) == 0


def test_context_window_session_exists_no_entries(insert_data):
    res = client.run(
        context_window_query_beliefs.replace("{session_id}", insert_data["session_id"])
    )
    """
    [
        {'content': 'you an AI assistant talking to people about life', 'name': 'situation', 'role': 'system', 'timestamp': 1698754343, 'token_count': 15}, 
        {'content': 'About "John": John is a good guy\n\nAbout "Samantha": samantha is an AI assistant', 'name': 'information', 'role': 'system', 'timestamp': 1698754343, 'token_count': 24}, 
        {'content': [], 'name': 'information', 'role': 'system', 'timestamp': 0, 'token_count': 0.0},
    ]
    """

    assert len(res) == 1
    assert res["model_data"][0] == {
        "model_name": "samantha-1-alpha",
        "max_length": 4096,
        "default_settings": {
            "frequency_penalty": 1,
            "max_tokens": 120,
            "repetition_penalty": 0.9,
            "temperature": 0.7,
        },
    }
    assert res["character_data"][0] == {
        "name": "Samantha",
        "about": "Samantha is an AI assistant",
    }
    assert len(res["entries"][0]) > 0
    assert res["total_tokens"][0] == 39
