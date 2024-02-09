from fastapi import APIRouter, HTTPException, status
from pydantic import UUID4
from .protocol import UpsertBeliefRequest, Belief, IndexRequest
from agents_api.clients.cozo import client


router = APIRouter()


@router.get("/beliefs/{belief_id}")
async def get_by_belief_id(belief_id: UUID4) -> Belief:
    query = f"""
    input[belief_id] <- [[to_uuid("{belief_id}")]]

    ?[
        referrent_is_user,
        referrent_id,
        subject_is_user,
        subject_id,
        belief_id,
        belief,
        valence,
        sentiment,

    ] := input[belief_id], *beliefs:by_belief_id {{
        referrent_is_user,
        referrent_id,
        subject_is_user,
        subject_id,
        belief_id,
        belief,
        valence,
        sentiment,
    }}
    """

    try:
        res = [row.to_dict() for _, row in client.run(query).iterrows()][0]
        return Belief(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Belief not found",
        )


@router.get("/beliefs/{character_id}")
async def get_by_character_id(character_id: UUID4) -> Belief:
    query = f"""
    input[character_id] <- [[
        to_uuid("{character_id}"),
    ]]

    ?[
        referrent_is_user,
        referrent_id,
        subject_is_user,
        subject_id,
        belief_id,
        belief,
        valence,
        source_episode,
        parent_belief,
        sentiment,
        processed,
        created_at,
        embedding,
        fact_embedding,

    ] := input[referrent_id], *beliefs {{
            referrent_is_user,
            referrent_id,
            subject_is_user,
            subject_id,
            belief_id,
            belief,
            valence,
            source_episode,
            parent_belief,
            sentiment,
            processed,
            created_at,
            embedding,
            fact_embedding,
        }},
        referrent_is_user = false,
        subject_is_user = null,
        subject_id = null
    """

    try:
        res = [row.to_dict() for _, row in client.run(query).iterrows()][0]
        return Belief(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Belief not found",
        )


@router.post("/beliefs/create")
async def create_belief(request: UpsertBeliefRequest):
    query = f"""
    input[
        belief_id,
        character_id,
        belief,
        embedding,
    ] <- [
        [
            to_uuid("{request.belief_id}"),
            to_uuid("{request.character_id}"),
            "{request.belief}",
            {request.embedding},
        ]
    ]

    ?[
        referrent_is_user,
        referrent_id,
        belief_id,
        belief,
        embedding,
    ] := input[
            belief_id,
            referrent_id,
            belief,
            embedding,
        ],
        referrent_is_user = false

    :put beliefs {{
        referrent_is_user,
        referrent_id,
        belief_id =>
        belief,
        embedding,
    }}
    """

    client.run(query)


@router.post("/beliefs/index")
async def query_by_index(request: IndexRequest) -> Belief:
    query = f"""
    input[character_id, vector] <- [[
        to_uuid("{request.character_id}"),
        vec({request.vector}),
    ]]

    ?[
        referrent_is_user,
        referrent_id,
        subject_is_user,
        subject_id,
        belief_id,
        belief,
        valence,
        source_episode,
        parent_belief,
        sentiment,
        processed,
        created_at,
        embedding,
        fact_embedding,

        dist,
    ] := input[referrent_id, vector],
        ~beliefs:embedding_space {{
            referrent_is_user,
            referrent_id,
            subject_is_user,
            subject_id,
            belief_id,
            belief,
            valence,
            source_episode,
            parent_belief,
            sentiment,
            processed,
            created_at,
            embedding,
            fact_embedding

        | query: vector,
            k: 3,
            ef: 20,
            bind_distance: dist,
            radius: 100000.0,
        }},
        referrent_is_user = false,
        subject_is_user = null,
        subject_id = null
    """

    try:
        res = [row.to_dict() for _, row in client.run(query).iterrows()][0]
        return Belief(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Belief not found",
        )
