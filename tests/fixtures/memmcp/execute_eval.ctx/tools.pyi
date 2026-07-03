# AI-ANCHOR: tools: tool-loop eval fixture
"""Tool stubs for the tool-loop eval fixture."""

def record_memory(content: str) -> dict:
    """Store one memory.

    Args:
        content: The memory text to store.
    """
    ...

def search(query: str) -> list:
    """Search stored memories.

    Args:
        query: The search query.
    """
    ...
