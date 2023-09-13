from fastapi import APIRouter
from .protocol import Character, ChatRequest, ChatMessage


router = APIRouter()


@router.get("/characters/")
def get_characters() -> list[Character]:
    pass


@router.post("/characters/")
def create_character(character: Character) -> Character:
    pass


@router.post("/characters/{character_id}/chat")
def character_chat(character_id: str, request: ChatRequest) -> list[ChatMessage]:
    pass
