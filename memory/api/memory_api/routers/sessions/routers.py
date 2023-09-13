from fastapi import APIRouter
from .protocol import Session, ChatRequest, ChatMessage


router = APIRouter()


@router.post("/sessions/")
def create_session(request: Session) -> Session:
    pass


@router.post("/sessions/{session_id}/chat")
def session_chat(session_id: str, request: ChatRequest) -> list[ChatMessage]:
    pass
