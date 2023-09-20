from fastapi import APIRouter, HTTPException, status
from .protocol import Session, ChatRequest, ChatMessage
from memory_api.clients.cozo import client
from .protocol import SessionsRequest


router = APIRouter()


@router.post("/sessions/")
def create_session(request: Session):
    query = f"""
        ?[session_id, character_id, user_id, situation, metadata] <- [[
        to_uuid("{request.id}"),
        to_uuid("{request.character_id}"),
        to_uuid("{request.user_id}"),
        "{request.situation}",
        {request.metadata},
    ]]

    :put sessions {{
        character_id,
        user_id,
        session_id,
        situation,
        metadata,
    }}
    """

    client.run(query)


@router.get("/sessions/")
def get_sessions(request: SessionsRequest) -> Session:
    query = f"""
        input[session_id] <- [[
        to_uuid("{request.session_id}"),
    ]]

    ?[
        character_id,
        user_id,
        session_id,
        updated_at,
        situation,
        summary,
        metadata,
        created_at,
    ] := input[session_id],
        *sessions{{
            character_id,
            user_id,
            session_id,
            situation,
            summary,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)
    """

    try:
        res = [row.to_dict() for _, row in client.run(query).iterrows()][0]
        return Session(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.post("/sessions/{session_id}/chat")
def session_chat(session_id: str, request: ChatRequest) -> list[ChatMessage]:
    pass
