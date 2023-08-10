from textwrap import dedent

from .cozo import client
from .embed import embed
from .utils import extract_keywords

# @@ TODO: Add lru_cache to all queries

def get_character_about(character_id: str):
    results = client.run(
        dedent(
            f"""
    char[character_id] <- [[to_uuid("{character_id}")]]
    ?[name, about, metadata] := char[character_id], *characters{{name, about, metadata, character_id, updated_at @ floor(now())}}
    """
        )
    )

    name = results["name"][0]
    about = results["about"][0]
    metadata = results["metadata"][0]

    return dict(
        name=name,
        about=about,
        metadata=metadata,
    )


def get_user_by_email(email: str):
    results = client.run(
        dedent(
            f"""
    input[email] <- [["{email}"]]
    ?[character_id, assistant_id] := input[email], *users{{email, character_id, assistant_id}}
    """
        )
    )

    if not len(results):
        return None

    character_id = results["character_id"][0]
    assistant_id = results["assistant_id"][0]

    output = dict(
        character_id=character_id,
        assistant_id=assistant_id,
        character=get_character_about(character_id),
        assistant=get_character_about(assistant_id),
    )

    return output


def get_session_by_email(email: str, vocode_conversation_id: str):
    limit: int = 1
    user_details = get_user_by_email(email)
    character_id = user_details["character_id"]

    results = client.run(
        dedent(
            f"""
    char[character_id, vocode_conversation_id] <- [
      [to_uuid("{character_id}"), "{vocode_conversation_id}"]
    ]
                         
    ?[session_id, situation, summary, metadata] := char[character_id, vocode_conversation_id], *session_characters{{session_id, character_id}}, *sessions{{session_id, situation, summary, metadata, updated_at @ floor(now())}}, vocode_conversation_id == maybe_get(metadata, "vocode_conversation_id")
    :limit {limit}
    """
        )
    )

    if not len(results):
        return None

    session_id = results["session_id"][0]
    situation = results["situation"][0]
    summary = results["summary"][0]
    metadata = results["metadata"][0]

    return dict(
        session_id=session_id,
        situation=situation,
        summary=summary,
        metadata=metadata,
    )


def get_matching_beliefs(
    chatml,  #: ChatML,
    confidence: float = 0.8,
    n: int = 10,
    k: int = 3,
    window_size: int = 3,
    character_ids: list[str] = [],
    exclude_roles: list[str] = [],
):
    # @@ TODO: Filter by characters

    # Extract text window from conversation chatml
    chatml = chatml[-window_size:]

    text = "\n".join(
        [
            f"{message.get('name', message['role'])}: {message['content']}"
            for message in chatml
            if message["role"] not in exclude_roles
        ]
    )

    # Prepare embedding for search
    radius = 1.0 - confidence
    [query_embedding] = embed([text], "passage")

    # TODO: Apply mmr
    # Embedding search
    hnsw_query = dedent(
        f"""
    ?[belief, valence, dist, character_id] := ~beliefs:embedding_space{{ belief, valence, character_id |
        query: vec({query_embedding}),
        k: {n},
        ef: 20,
        radius: {radius},
        bind_distance: dist,
    }}

    :order -valence
    :order dist
    """
    )

    # Embedding seach results
    hnsw_results = client.run(hnsw_query)

    # Now mix up for character_ids
    groups = [
        group.tolist() for _, group in hnsw_results.groupby(["character_id"])["belief"]
    ]

    k_hnsw_results = []
    i = 0
    while len(k_hnsw_results) < k and len(groups) > 0:
        group_idx = i % len(groups)
        group = groups[group_idx]

        if not len(group):
            groups.pop(group_idx)
            continue

        item = group.pop(0)
        k_hnsw_results.append(item)
        i += 1

    # FTS query
    keywords = " ".join([keyword for keyword, _ in extract_keywords(text)])

    fts_query = dedent(
        f"""
    ?[belief, valence, score, character_id] := ~beliefs:summary {{ belief, valence, character_id |
        query: "{keywords}",
        k: {n},
        score_kind: 'tf_idf',
        bind_score: score
    }}
    
    :order -valence
    :order -score
    :limit {k}
    """
    )

    # Embedding seach results
    fts_results = client.run(fts_query)
    fts_results = fts_results["belief"].tolist()

    # Combine results
    results = k_hnsw_results + fts_results

    print(f"{len(results)} matching beliefs found for ```{text}```")

    return results


def get_beliefs_of_character(character_id: str, limit: int = 100):
    query = dedent(
        f"""
    char[character_id] <- [[to_uuid("{character_id}")]]
    ?[belief_id] := *beliefs{{belief_id, character_id}}, char[character_id]

    :limit {limit}
    """
    )

    return query


def get_session_entries(session_id: str):
    query = dedent(
        f"""
    session[session_id] <- [[to_uuid("{session_id}")]]
    ?[
        role,
        name,
        content,
        character_id,
        updated_at,
    ] := session[session_id],
         *entries{{
            session_id,
            role,
            name,
            content,
            character_id,
            updated_at @ floor(now())
         }}

    :sort updated_at
    """
    )

    results = client.run(query)
    if not len(results):
        return []

    results = results.to_dict(orient="records")
    return results
