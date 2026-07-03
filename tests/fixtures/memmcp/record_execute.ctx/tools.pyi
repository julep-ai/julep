# AI-ANCHOR: tools: record/execute acceptance fixture (3 tools)
"""Tool stubs for the record/execute tool-loop acceptance fixture."""

def record_memory(content: str) -> dict:
    """Store one memory (write effect).

    Args:
        content: The memory text to store.
    """
    ...

def search(query: str) -> list:
    """Search stored memories (read effect).

    Args:
        query: The search query.
    """
    ...

def recall(key: str) -> dict:
    """Recall one stored memory by key (read effect).

    Args:
        key: The memory key to recall.
    """
    ...
