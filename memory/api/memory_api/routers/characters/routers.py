from fastapi import APIRouter, HTTPException, status
from .protocol import Character, ChatRequest, ChatMessage, CharacterRequest
from memory_api.clients.cozo import client


router = APIRouter()


@router.get("/characters/")
def get_characters(request: CharacterRequest) -> Character:
    query = f"""
    input[character_id] <- [[to_uuid("{request.character_id}")]]

    ?[
        character_id,
        name,
        about,
        metadata,
        model,
        updated_at,
        created_at,
    ] := input[character_id],
        *characters {{
            character_id,
            name,
            about,
            metadata,
            model,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)"""

    try:
        res = [row.to_dict() for _, row in client.run(query).iterrows()][0]
        return Character(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )


@router.post("/characters/")
def create_character(character: Character) -> Character:
    query = f"""
    ?[character_id, name, about, metadata, model] <- [
        ["{character.id}", "{character.name}", "{character.about}", {character.metadata}, "{character.model}"]
    ]
    
    :put characters {{
        character_id =>
        name,
        about,
        metadata,
        model,
    }}
    """

    client.run(query)


@router.post("/characters/{character_id}/chat")
def character_chat(character_id: str, request: ChatRequest) -> list[ChatMessage]:
    pass
