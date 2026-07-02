# AI-ANCHOR: tools: C5 execute agent tool definitions (trimmed vendored copy)
"""Tool definitions for the unified execute agent."""

from typing import NotRequired, TypedDict

class EpisodeItem(TypedDict):
    """Single episode payload accepted by `create_episodes`."""

    content: str
    importance: NotRequired[int]
    start_time: NotRequired[str]
    end_time: NotRequired[str]

def search_episodes(
    cues: list[str],
    limit: int = 20,
    time_window_hours: int = 168,
    min_importance: int = 30,
    similarity_threshold: float = 0.6,
) -> list[dict]:
    """Search for episodes using semantic similarity.

    Args:
        cues: 2-4 search cues combining actors, actions, and temporal hints.
        limit: Maximum results to return.
        time_window_hours: Hours from now to restrict search.
        min_importance: Minimum importance threshold (0-100).
        similarity_threshold: Similarity threshold (0-1).

    Returns:
        List of matching episodes with relevance scores.
    """
    ...

def create_episodes(
    episodes: list[EpisodeItem],
    background: str | None = None,
) -> dict:
    """Batch-create episodes.

    Args:
        episodes: Episode payloads; each needs content.
        background: Shared context for the batch.
    """
    ...
