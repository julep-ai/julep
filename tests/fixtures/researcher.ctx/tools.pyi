"""Tool contract for the researcher fixture."""

from typing import NotRequired, TypedDict

__server__ = "memory"

class NoteItem(TypedDict):
    """A single note payload."""

    content: str
    importance: NotRequired[int]

def search_notes(
    cues: list[str],
    limit: int = 20,
    min_importance: int | None = None,
) -> list[dict]:
    """Search notes by semantic similarity.

    Args:
        cues: 2-4 short search cues.
        limit: Maximum results to return.
        min_importance: Optional importance floor.

    Returns:
        Matching notes.
    """
    ...

def create_note(notes: list[NoteItem], background: str | None = None) -> dict:
    """Batch-create notes.

    Args:
        notes: Note payloads; each needs content.
        background: Shared context for the batch.
    """
    ...
