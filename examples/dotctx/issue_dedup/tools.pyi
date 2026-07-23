"""Tool contract for the issue-dedup planner (the prompt-side assertion)."""


def search_similar_posts(query: str) -> list[dict]:
    """Search the issue tracker for existing posts similar to the given query.

    Args:
        query: The issue text (or a shorter failure-signature query) to search for.

    Returns:
        List of post dicts with id, title, content, upvotes.
    """
    ...
